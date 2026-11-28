"""Inspect an authorized public source and prepare a Hebrew corpus candidate.

Only bounded, public HTTPS sources are accepted. This script never executes repository code.
The caller must have rights to use all selected text for model training.
"""
from __future__ import annotations

import hashlib
import ipaddress
import json
import os
import re
import socket
import sys
import zipfile
import gzip
import io
import time
import xml.etree.ElementTree as ET
from urllib.robotparser import RobotFileParser
from datetime import datetime, timezone
from collections import deque
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from charset_normalizer import from_bytes

MAX_DOWNLOAD_BYTES = 20 * 1024 * 1024
MAX_ARCHIVE_FILES = 500
MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_CORPUS_BYTES = 100 * 1024 * 1024
MAX_CRAWL_PAGES = 500
MAX_CRAWL_DEPTH = 5
MAX_TOTAL_CRAWL_BYTES = 100 * 1024 * 1024
MAX_SITEMAP_URLS = 500
CRAWL_DELAY_SECONDS = 0.5
ALLOWED_TEXT_SUFFIXES = {".txt", ".md", ".rst", ".html", ".htm"}
USER_AGENT = "IvritLM-SourceInspector/0.2 (+https://github.com/avtsye/IvritLM)"
HEBREW_RE = re.compile(r"[\u0590-\u05ff]")


def validate_public_https(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("Only absolute HTTPS URLs are accepted.")
    if parsed.username or parsed.password:
        raise ValueError("Credentials in source URLs are not accepted.")
    host = parsed.hostname.rstrip(".").lower()
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".local"):
        raise ValueError("Local hostnames are not accepted.")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address and not address.is_global:
        raise ValueError("Non-public IP addresses are not accepted.")
    if not address:
        try:
            records = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
        except socket.gaierror as exc:
            raise ValueError(f"Could not resolve source host: {host}") from exc
        addresses = {record[4][0].split("%", 1)[0] for record in records}
        if not addresses or any(not ipaddress.ip_address(item).is_global for item in addresses):
            raise ValueError("Source host resolves to a non-public address.")
    return url


def bounded_get(url: str) -> requests.Response:
    current = validate_public_https(url)
    session = requests.Session()
    for _ in range(4):
        response = session.get(current, headers={"User-Agent": USER_AGENT},
                               stream=True, timeout=(10, 30), allow_redirects=False)
        if response.is_redirect or response.is_permanent_redirect:
            location = response.headers.get("Location")
            response.close()
            if not location:
                raise ValueError("Redirect did not include a destination.")
            current = validate_public_https(urljoin(current, location))
            continue
        response.raise_for_status()
        length = response.headers.get("Content-Length")
        if length and int(length) > MAX_DOWNLOAD_BYTES:
            response.close()
            raise ValueError("Source exceeds the 20 MiB intake limit.")
        body = bytearray()
        for chunk in response.iter_content(chunk_size=65536):
            body.extend(chunk)
            if len(body) > MAX_DOWNLOAD_BYTES:
                response.close()
                raise ValueError("Source exceeds the 20 MiB intake limit.")
        response._ivritlm_body = bytes(body)
        response._content = response._ivritlm_body
        response._content_consumed = True
        response.close()
        return response
    raise ValueError("Too many redirects.")


def clean_text(raw: bytes, suffix: str = ".txt", encoding: str = "utf-8-sig") -> str:
    try:
        text = raw.decode(encoding, errors="replace")
    except LookupError:
        text = raw.decode("utf-8-sig", errors="replace")
    if suffix in {".html", ".htm"}:
        soup = BeautifulSoup(text, "html.parser")
        for node in soup(["script", "style", "noscript", "svg", "nav", "footer", "header"]):
            node.decompose()
        text = soup.get_text("\n", strip=True)
    text = text.replace("\x00", " ")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines).strip()


def is_hebrew_text(text: str) -> bool:
    letters = [c for c in text if c.isalpha()]
    if len(letters) < 100:
        return False
    return sum(bool(HEBREW_RE.match(c)) for c in letters) / len(letters) >= 0.40


def write_corpus(documents: list[tuple[str, str]], report: dict) -> dict:
    output = Path("artifacts/source-intake")
    output.mkdir(parents=True, exist_ok=True)
    corpus_path = output / "corpus.txt"
    seen = set()
    total = 0
    accepted = 0
    with corpus_path.open("w", encoding="utf-8", newline="\n") as stream:
        for label, text in documents:
            normalized = text.strip()
            if not normalized or not is_hebrew_text(normalized):
                continue
            digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
            if digest in seen:
                continue
            encoded_size = len((normalized + "\n").encode("utf-8"))
            if total + encoded_size > MAX_CORPUS_BYTES:
                break
            seen.add(digest)
            stream.write(f"\n\n### מקור: {label}\n\n{normalized}")
            total += encoded_size
            accepted += 1
    if not accepted:
        corpus_path.unlink(missing_ok=True)
        raise ValueError(
            "לא נמצאו מסמכי טקסט בעברית באיכות/אורך המתאימים. "
            "נסה מאגר עם קובצי TXT/MD בעברית או עמוד עברי ארוך יותר."
        )
    corpus = corpus_path.read_bytes()
    corpus_sha = hashlib.sha256(corpus).hexdigest()
    manifest = {
        "project": "IvritLM",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_url": report["canonical_url"],
        "source_type": report["source_type"],
        "license_review_required": True,
        "authorization_acknowledged": True,
        "accepted_document_count": accepted,
        "corpus_bytes": len(corpus),
        "corpus_sha256": corpus_sha,
        "language_filter": "At least 40% Hebrew letters and 100 alphabetic characters per document",
        "deduplication": "SHA-256 of normalized document text",
    }
    (output / "corpus-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    report.update({
        "stage": "corpus_candidate_created",
        "training_started": False,
        "accepted_document_count": accepted,
        "corpus_bytes": len(corpus),
        "corpus_sha256": corpus_sha,
        "corpus_path": "artifacts/source-intake/corpus.txt",
        "note": "A Hebrew corpus candidate was prepared. Review source rights and the corpus before starting training.",
    })
    return manifest


def inspect_github(url: str) -> tuple[dict, list[tuple[str, str]]]:
    parsed = urlparse(url)
    if parsed.hostname != "github.com":
        raise ValueError("GitHub sources must use github.com.")
    match = re.fullmatch(r"/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)/?", parsed.path)
    if not match:
        raise ValueError("Expected https://github.com/owner/repository")
    owner, repo = match.groups()
    repo = repo.removesuffix(".git")
    metadata = bounded_get(f"https://api.github.com/repos/{owner}/{repo}").json()
    if metadata.get("private") is not False:
        raise ValueError("Only public GitHub repositories are accepted.")
    branch = metadata.get("default_branch") or "main"
    archive_response = bounded_get(f"https://codeload.github.com/{owner}/{repo}/zip/refs/heads/{branch}")
    archive_path = Path("artifacts/source-intake/source.zip")
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    archive_path.write_bytes(archive_response._ivritlm_body)
    docs = []
    total_unpacked = 0
    with zipfile.ZipFile(archive_path) as archive:
        members = archive.infolist()
        if len(members) > MAX_ARCHIVE_FILES:
            raise ValueError(f"Repository archive exceeds {MAX_ARCHIVE_FILES} files.")
        for member in members:
            if member.is_dir() or Path(member.filename).suffix.lower() not in ALLOWED_TEXT_SUFFIXES:
                continue
            if member.file_size > MAX_FILE_BYTES:
                continue
            total_unpacked += member.file_size
            if total_unpacked > MAX_DOWNLOAD_BYTES:
                break
            raw = archive.read(member)
            text = clean_text(raw, Path(member.filename).suffix.lower())
            if is_hebrew_text(text):
                docs.append((member.filename, text))
    archive_path.unlink(missing_ok=True)
    report = {
        "source_type": "github",
        "canonical_url": metadata.get("html_url", url),
        "repository": metadata.get("full_name"),
        "default_branch": branch,
        "license_spdx_id": (metadata.get("license") or {}).get("spdx_id"),
        "license_review_required": True,
        "candidate_text_file_count": len(docs),
    }
    return report, docs


def normalize_page_url(url: str, base: str) -> str | None:
    target = urljoin(base, url)
    parsed = urlparse(target)
    if parsed.scheme != "https" or not parsed.hostname:
        return None
    if parsed.username or parsed.password or parsed.query:
        return None
    if parsed.hostname.lower() != urlparse(base).hostname.lower():
        return None
    path = parsed.path or "/"
    # Avoid fetching obvious non-page assets and actions.
    if Path(path).suffix.lower() in {
        ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".ico", ".css", ".js",
        ".pdf", ".zip", ".gz", ".mp3", ".mp4", ".woff", ".woff2", ".ttf",
    }:
        return None
    return parsed._replace(path=path, fragment="").geturl()


def load_robots(start: str) -> tuple[RobotFileParser, list[str]]:
    parsed = urlparse(start)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    parser = RobotFileParser()
    parser.set_url(robots_url)
    sitemap_urls: list[str] = []
    try:
        response = bounded_get(robots_url)
        body = response._ivritlm_body.decode("utf-8-sig", errors="replace")
        parser.parse(body.splitlines())
        sitemap_urls = parser.site_maps() or []
    except requests.HTTPError as exc:
        # A missing robots.txt is equivalent to no published crawl restrictions.
        if getattr(exc.response, "status_code", None) in (404, 410):
            parser.parse(["User-agent: *", "Allow: /"])
        else:
            parser.parse(["User-agent: *", "Disallow: /"])
    except requests.RequestException:
        parser.parse(["User-agent: *", "Disallow: /"])
    return parser, sitemap_urls


def discover_sitemap_urls(start: str, sitemap_urls: list[str]) -> list[str]:
    parsed_start = urlparse(start)
    candidates = list(sitemap_urls)
    candidates.extend([
        f"{parsed_start.scheme}://{parsed_start.netloc}/sitemap.xml",
        f"{parsed_start.scheme}://{parsed_start.netloc}/sitemap_index.xml",
    ])
    seen_maps: set[str] = set()
    discovered: list[str] = []
    while candidates and len(seen_maps) < 100 and len(discovered) < MAX_SITEMAP_URLS:
        sitemap_url = candidates.pop(0)
        normalized = normalize_page_url(sitemap_url, start)
        # Sitemap files have XML/GZ suffixes, so validate host and scheme separately.
        parsed = urlparse(sitemap_url)
        if (parsed.scheme != "https" or parsed.hostname != parsed_start.hostname
                or parsed.username or parsed.password or sitemap_url in seen_maps):
            continue
        seen_maps.add(sitemap_url)
        try:
            response = bounded_get(sitemap_url)
        except (requests.RequestException, ValueError):
            continue
        raw = response._ivritlm_body
        if sitemap_url.lower().endswith(".gz"):
            try:
                with gzip.GzipFile(fileobj=io.BytesIO(raw)) as compressed:
                    raw = compressed.read(MAX_DOWNLOAD_BYTES + 1)
                if len(raw) > MAX_DOWNLOAD_BYTES:
                    continue
            except OSError:
                continue
        try:
            root = ET.fromstring(raw)
        except ET.ParseError:
            continue
        for element in root.iter():
            if element.tag.rsplit("}", 1)[-1].lower() != "loc" or not element.text:
                continue
            loc = element.text.strip()
            if loc.lower().endswith((".xml", ".xml.gz")) and len(candidates) < 100:
                candidates.append(loc)
            else:
                page_url = normalize_page_url(loc, start)
                if page_url and page_url not in discovered:
                    discovered.append(page_url)
                    if len(discovered) >= MAX_SITEMAP_URLS:
                        break
    return discovered


def inspect_web(url: str) -> tuple[dict, list[tuple[str, str]]]:
    """Crawl a public website using its sitemap plus same-host internal links."""
    start = validate_public_https(url)
    host = urlparse(start).hostname
    robots, sitemap_urls = load_robots(start)
    sitemap_pages = discover_sitemap_urls(start, sitemap_urls)

    queue = deque((page, 0) for page in sitemap_pages)
    queue.appendleft((start, 0))
    queued = {page for page, _ in queue}
    visited: set[str] = set()
    documents: list[tuple[str, str]] = []
    total_bytes = 0
    page_titles: list[str] = []
    blocked_by_robots = 0
    failed_pages = 0
    max_depth_reached = 0

    while queue and len(visited) < MAX_CRAWL_PAGES and total_bytes < MAX_TOTAL_CRAWL_BYTES:
        current, depth = queue.popleft()
        if current in visited or urlparse(current).hostname != host:
            continue
        if not robots.can_fetch(USER_AGENT, current):
            blocked_by_robots += 1
            continue
        visited.add(current)
        try:
            response = bounded_get(current)
        except (requests.RequestException, ValueError):
            failed_pages += 1
            continue
        content_type = response.headers.get("Content-Type", "").lower()
        if "text/html" not in content_type and "text/plain" not in content_type:
            continue
        raw = response._ivritlm_body
        if total_bytes + len(raw) > MAX_TOTAL_CRAWL_BYTES:
            break
        total_bytes += len(raw)
        detected = from_bytes(raw).best()
        encoding = detected.encoding if detected else (response.encoding or "utf-8-sig")
        if "html" in content_type:
            soup = BeautifulSoup(raw.decode(encoding, errors="replace"), "html.parser")
            title = soup.title.get_text(" ", strip=True) if soup.title else ""
            if title:
                page_titles.append(title[:200])
            if depth < MAX_CRAWL_DEPTH:
                for anchor in soup.find_all("a", href=True):
                    target = normalize_page_url(anchor["href"], response.url)
                    if target and target not in visited and target not in queued:
                        queue.append((target, depth + 1))
                        queued.add(target)
            text = clean_text(raw, ".html", encoding)
        else:
            text = clean_text(raw, ".txt", encoding)
        if text:
            documents.append((response.url, text))
        max_depth_reached = max(max_depth_reached, depth)
        # Be polite to the source host rather than issuing a burst of requests.
        time.sleep(CRAWL_DELAY_SECONDS)

    capped = bool(queue) and (
        len(visited) >= MAX_CRAWL_PAGES or total_bytes >= MAX_TOTAL_CRAWL_BYTES
    )
    if not documents:
        raise ValueError("לא נמצאו דפי HTML או טקסט ציבוריים מותרים לסריקה באתר.")
    report = {
        "source_type": "web_crawl",
        "canonical_url": start,
        "page_titles": page_titles[:100],
        "pages_visited": len(visited),
        "candidate_document_count": len(documents),
        "sitemap_url_count": len(sitemap_pages),
        "downloaded_bytes": total_bytes,
        "blocked_by_robots": blocked_by_robots,
        "failed_pages": failed_pages,
        "max_depth_reached": max_depth_reached,
        "crawl_limit_reached": capped,
        "crawl_policy": (
            f"Same hostname only; sitemap plus internal links; maximum {MAX_CRAWL_PAGES} pages; "
            f"depth {MAX_CRAWL_DEPTH}; total download {MAX_TOTAL_CRAWL_BYTES} bytes; "
            "robots.txt respected; {CRAWL_DELAY_SECONDS} second delay between pages."
        ),
        "license_review_required": True,
    }
    return report, documents

def main() -> int:
    url = os.environ.get("SOURCE_URL", "").strip()
    kind = os.environ.get("SOURCE_KIND", "").strip()
    if not url:
        print("SOURCE_URL is required.", file=sys.stderr)
        return 2
    try:
        if kind == "github":
            report, documents = inspect_github(url)
        elif kind == "web":
            report, documents = inspect_web(url)
        else:
            raise ValueError("SOURCE_KIND must be github or web.")
        report.update({
            "created_at": datetime.now(timezone.utc).isoformat(),
            "project": "IvritLM",
            "license_acknowledgement": "confirmed_by_workflow_dispatcher",
        })
        manifest = write_corpus(documents, report)
        output = Path("artifacts/source-intake")
        (output / "report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(json.dumps({"report": report, "corpus_manifest": manifest}, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, requests.RequestException, zipfile.BadZipFile, OSError) as exc:
        print(f"Source intake failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

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
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

MAX_DOWNLOAD_BYTES = 20 * 1024 * 1024
MAX_ARCHIVE_FILES = 500
MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_CORPUS_BYTES = 5 * 1024 * 1024
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
        return response
    raise ValueError("Too many redirects.")


def clean_text(raw: bytes, suffix: str = ".txt") -> str:
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
    return sum(bool(HEBREW_RE.match(c)) for c in letters) / len(letters) >= 0.15


def write_corpus(documents: list[tuple[str, str]], report: dict) -> dict:
    output = Path("artifacts/source-intake")
    output.mkdir(parents=True, exist_ok=True)
    chunks = []
    seen = set()
    total = 0
    accepted = 0
    for label, text in documents:
        normalized = text.strip()
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        if not normalized or digest in seen or not is_hebrew_text(normalized):
            continue
        encoded = (normalized + "\n").encode("utf-8")
        if total + len(encoded) > MAX_CORPUS_BYTES:
            break
        seen.add(digest)
        chunks.append(f"\n\n### מקור: {label}\n\n{normalized}")
        total += len(encoded)
        accepted += 1
    if not chunks:
        raise ValueError(
            "לא נמצאו מסמכי טקסט בעברית באיכות/אורך המתאימים. "
            "נסה מאגר עם קובצי TXT/MD בעברית או עמוד עברי ארוך יותר."
        )
    corpus = ("\n".join(chunks) + "\n").encode("utf-8")
    corpus_path = output / "corpus.txt"
    corpus_path.write_bytes(corpus)
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
        "language_filter": "At least 15% Hebrew letters and 100 alphabetic characters per document",
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


def inspect_web(url: str) -> tuple[dict, list[tuple[str, str]]]:
    response = bounded_get(url)
    content_type = response.headers.get("Content-Type", "")
    if "text/html" not in content_type and "text/plain" not in content_type:
        raise ValueError(f"Unsupported content type: {content_type or 'unknown'}. Use HTML or plain text.")
    raw = response._ivritlm_body
    text = clean_text(raw, ".html" if "html" in content_type else ".txt")
    title = ""
    if "html" in content_type:
        soup = BeautifulSoup(raw.decode(response.encoding or "utf-8", errors="replace"), "html.parser")
        title = soup.title.get_text(" ", strip=True) if soup.title else ""
    report = {
        "source_type": "web",
        "canonical_url": response.url,
        "page_title": title[:300],
        "content_type": content_type,
        "downloaded_bytes": len(raw),
        "license_review_required": True,
    }
    return report, [(response.url, text)]


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

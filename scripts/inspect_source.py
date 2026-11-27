"""Validate a public source URL and produce a provenance intake report.

This stage deliberately does not execute submitted repository code or train weights.
"""
from __future__ import annotations

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
ALLOWED_TEXT_SUFFIXES = {".txt", ".md", ".html", ".htm", ".rst"}
USER_AGENT = "IvritLM-SourceInspector/0.1 (+https://github.com/avtsye/IvritLM)"


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
        response = session.get(
            current,
            headers={"User-Agent": USER_AGENT},
            stream=True,
            timeout=(10, 30),
            allow_redirects=False,
        )
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


def inspect_github(url: str) -> dict:
    parsed = urlparse(url)
    if parsed.hostname != "github.com":
        raise ValueError("GitHub sources must use github.com.")
    match = re.fullmatch(r"/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)/?", parsed.path)
    if not match:
        raise ValueError("Expected https://github.com/owner/repository")
    owner, repo = match.groups()
    repo = repo.removesuffix(".git")
    metadata_response = bounded_get(f"https://api.github.com/repos/{owner}/{repo}")
    metadata = metadata_response.json()
    if metadata.get("private") is not False:
        raise ValueError("Only public GitHub repositories are accepted.")
    branch = metadata.get("default_branch") or "main"
    archive_response = bounded_get(f"https://codeload.github.com/{owner}/{repo}/zip/refs/heads/{branch}")
    archive_path = Path("artifacts/source-intake/source.zip")
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    archive_path.write_bytes(archive_response._ivritlm_body)
    text_files = 0
    text_bytes = 0
    with zipfile.ZipFile(archive_path) as archive:
        members = archive.infolist()
        if len(members) > MAX_ARCHIVE_FILES:
            raise ValueError(f"Repository archive exceeds {MAX_ARCHIVE_FILES} files.")
        for member in members:
            if member.is_dir():
                continue
            if Path(member.filename).suffix.lower() not in ALLOWED_TEXT_SUFFIXES:
                continue
            if member.file_size > 2 * 1024 * 1024:
                continue
            text_files += 1
            text_bytes += member.file_size
    archive_path.unlink(missing_ok=True)
    return {
        "source_type": "github",
        "canonical_url": metadata.get("html_url", url),
        "repository": metadata.get("full_name"),
        "default_branch": branch,
        "license_spdx_id": (metadata.get("license") or {}).get("spdx_id"),
        "license_review_required": True,
        "candidate_text_file_count": text_files,
        "candidate_text_bytes": text_bytes,
        "note": "Repository files were not executed, ingested, or used for training; only archive metadata was inspected.",
    }


def inspect_web(url: str) -> dict:
    response = bounded_get(url)
    content_type = response.headers.get("Content-Type", "")
    if "text/html" not in content_type and "text/plain" not in content_type:
        raise ValueError(f"Unsupported content type: {content_type or 'unknown'}. Use HTML or plain text.")
    raw = response._ivritlm_body
    text = raw.decode(response.encoding or "utf-8", errors="replace")
    title = ""
    if "html" in content_type:
        soup = BeautifulSoup(text, "html.parser")
        for node in soup(["script", "style", "noscript", "svg"]):
            node.decompose()
        extracted = soup.get_text(" ", strip=True)
        title = soup.title.get_text(" ", strip=True) if soup.title else ""
    else:
        extracted = text
    return {
        "source_type": "web",
        "canonical_url": response.url,
        "page_title": title[:300],
        "content_type": content_type,
        "downloaded_bytes": len(raw),
        "extracted_character_count": len(extracted),
        "license_review_required": True,
        "note": "Page content was inspected for metadata only; it was not approved, added to a corpus, or used for training.",
    }


def main() -> int:
    url = os.environ.get("SOURCE_URL", "").strip()
    kind = os.environ.get("SOURCE_KIND", "").strip()
    if not url:
        print("SOURCE_URL is required.", file=sys.stderr)
        return 2
    try:
        result = inspect_github(url) if kind == "github" else inspect_web(url) if kind == "web" else None
        if result is None:
            raise ValueError("SOURCE_KIND must be github or web.")
        result.update({
            "created_at": datetime.now(timezone.utc).isoformat(),
            "project": "IvritLM",
            "stage": "source_intake_only",
            "training_started": False,
            "license_acknowledgement": "confirmed_by_workflow_dispatcher",
        })
        output = Path("artifacts/source-intake")
        output.mkdir(parents=True, exist_ok=True)
        (output / "report.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, requests.RequestException, zipfile.BadZipFile, OSError) as exc:
        print(f"Source inspection failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

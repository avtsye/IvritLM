from pathlib import Path
import requests
import json

from scripts.inspect_source import clean_text, is_hebrew_text, write_corpus


def test_clean_html_removes_script_and_navigation():
    raw = "<html><head><title>Title</title></head><body><nav>menu</nav><main><p>שלום עולם</p><script>secret()</script></main></body></html>".encode("utf-8")
    cleaned = clean_text(raw, ".html")
    assert "שלום עולם" in cleaned
    assert "secret" not in cleaned
    assert "menu" not in cleaned


def test_hebrew_filter_rejects_non_hebrew():
    hebrew = "שלום עולם " * 30
    english = "hello world " * 30
    assert is_hebrew_text(hebrew)
    assert not is_hebrew_text(english)


def test_corpus_deduplicates_and_writes_provenance(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    document = "זהו מסמך בעברית לצורך בדיקת יצירת קורפוס. " * 12
    report = {"canonical_url": "https://example.org", "source_type": "web"}
    manifest = write_corpus(
        [("page-1", document), ("duplicate", document), ("english", "hello world " * 30)],
        report,
    )
    corpus = Path("artifacts/source-intake/corpus.txt").read_text(encoding="utf-8")
    assert "מסמך בעברית" in corpus
    assert manifest["accepted_document_count"] == 1
    assert manifest["corpus_sha256"]
    assert report["training_started"] is False
    assert Path("artifacts/source-intake/corpus-manifest.json").is_file()

class _RawBody:
    def __init__(self, body):
        self.body = body

    def stream(self, chunk_size, decode_content=True):
        for offset in range(0, len(self.body), chunk_size):
            yield self.body[offset:offset + chunk_size]

    def close(self):
        pass


def test_bounded_get_preserves_json_after_streaming(monkeypatch):
    response = requests.Response()
    response.status_code = 200
    response.url = "https://example.com/data.json"
    response.headers = {"Content-Length": "11", "Content-Type": "application/json"}
    response.raw = _RawBody(b'{"ok":true}')
    response._content = False
    response._content_consumed = False

    class _Session:
        def get(self, *args, **kwargs):
            return response

    monkeypatch.setattr("scripts.inspect_source.validate_public_https", lambda url: url)
    monkeypatch.setattr("scripts.inspect_source.requests.Session", _Session)
    result = __import__("scripts.inspect_source", fromlist=["bounded_get"]).bounded_get("https://example.com/data.json")
    assert result._ivritlm_body == b'{"ok":true}'
    assert result.json() == {"ok": True}


def test_hebrew_filter_rejects_low_hebrew_ratio():
    mostly_english = "English words with a small שלום fragment " * 5
    mostly_hebrew = "זהו מסמך עברי תקין שמכיל מספיק אותיות ומילים לצורך בדיקה " * 4
    assert not is_hebrew_text(mostly_english)
    assert is_hebrew_text(mostly_hebrew)

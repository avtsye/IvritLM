from pathlib import Path

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

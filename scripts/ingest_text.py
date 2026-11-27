"""Create a reviewed UTF-8 Hebrew corpus from text pasted into the dashboard."""
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

HEBREW = re.compile(r"[\u0590-\u05ff]")


def main():
    raw = os.environ.get("TEXT_CONTENT", "")
    text = "\n".join(line.strip() for line in raw.replace("\r", "").splitlines() if line.strip())
    if len(text) < 100:
        raise SystemExit("יש להזין לפחות 100 תווים של טקסט.")
    letters = [c for c in text if c.isalpha()]
    if not letters or sum(bool(HEBREW.match(c)) for c in letters) / len(letters) < 0.15:
        raise SystemExit("הטקסט אינו מכיל שיעור מספיק של עברית.")
    if len(text.encode("utf-8")) > 5 * 1024 * 1024:
        raise SystemExit("הטקסט גדול מהמגבלה של 5 MiB.")
    output = Path("artifacts/source-intake")
    output.mkdir(parents=True, exist_ok=True)
    corpus = ("### טקסט שהוזן דרך לוח הניהול\n\n" + text + "\n").encode("utf-8")
    (output / "corpus.txt").write_bytes(corpus)
    digest = hashlib.sha256(corpus).hexdigest()
    manifest = {
        "project": "IvritLM",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_type": "dashboard_paste",
        "source_url": None,
        "license_review_required": True,
        "authorization_acknowledged": True,
        "accepted_document_count": 1,
        "corpus_bytes": len(corpus),
        "corpus_sha256": digest,
        "language_filter": "At least 15% Hebrew letters",
    }
    (output / "corpus-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output / "report.json").write_text(
        json.dumps({"stage": "corpus_candidate_created", "training_started": False,
                    "characters": len(text), "corpus_sha256": digest},
                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Prepared {len(text)} characters ({len(corpus)} bytes), SHA-256 {digest}")


if __name__ == "__main__":
    main()

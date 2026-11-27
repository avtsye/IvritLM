import json

import pytest

from scripts.train_chat import load_chat_jsonl


def test_load_chat_jsonl_serializes_hebrew_conversation(tmp_path):
    path = tmp_path / "chat.jsonl"
    path.write_text(json.dumps({
        "messages": [
            {"role": "user", "content": "שלום, מה נשמע? אני רוצה ללמוד על המודל ולבדוק כיצד הוא מסוגל לנהל שיחה בעברית."},
            {"role": "assistant", "content": "שלום! הכול בסדר, תודה ששאלת. אני יכול לעזור לך ללמוד, לנסח רעיונות ולענות על שאלות במגוון נושאים."},
        ]
    }, ensure_ascii=False) + "\n", encoding="utf-8")
    text, count = load_chat_jsonl(path)
    assert count == 1
    assert "### user" in text and "### assistant" in text
    assert "שלום" in text


def test_load_chat_jsonl_requires_assistant_last(tmp_path):
    path = tmp_path / "chat.jsonl"
    path.write_text(json.dumps({
        "messages": [
            {"role": "user", "content": "שלום"},
            {"role": "assistant", "content": "שלום"},
            {"role": "user", "content": "מה נשמע?"},
        ]
    }, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError, match="end with an assistant"):
        load_chat_jsonl(path)

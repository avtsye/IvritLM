import json

import pytest

from scripts.train_chat import load_chat_jsonl, load_chat_jsonl_with_mask
from ivritlm.training import make_batch
import torch


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

def test_chat_loss_mask_targets_only_assistant_response_bytes(tmp_path):
    path = tmp_path / "chat.jsonl"
    path.write_text(json.dumps({
        "messages": [
            {"role": "user", "content": "שאלת משתמש ארוכה מספיק לצורך בדיקה עם עוד מילים כדי לעבור את סף האורך של מערך הבדיקה"},
            {"role": "assistant", "content": "תשובת עוזר ארוכה מספיק לצורך בדיקה עם הסבר נוסף ומפורט כדי לוודא שהמסכה פועלת כראוי"},
        ]
    }, ensure_ascii=False) + "\n", encoding="utf-8")
    text, count, mask = load_chat_jsonl_with_mask(path)
    encoded = text.encode("utf-8")
    user_start = encoded.index("שאלת משתמש".encode("utf-8"))
    assistant_start = encoded.index("תשובת עוזר".encode("utf-8"))
    assert count == 1
    assert len(mask) == len(encoded)
    assert not any(mask[user_start:user_start + len("שאלת משתמש".encode("utf-8"))])
    assert all(mask[assistant_start:assistant_start + len("תשובת עוזר".encode("utf-8"))])

def test_masked_batch_ignores_all_non_assistant_targets():
    tokens = torch.arange(80, dtype=torch.long)
    target_mask = torch.zeros(80, dtype=torch.bool)
    target_mask[20:26] = True
    target_mask[50:56] = True
    _, targets = make_batch(tokens, batch_size=8, context_length=8, device="cpu", target_mask=target_mask)
    for row in targets:
        assert (row != -100).any()
        assert all(target_mask[int(token)] for token in row[row != -100])

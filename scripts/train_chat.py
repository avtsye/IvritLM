"""Supervised chat fine-tuning for the byte-level IvritLM prototype.

Input: JSONL, one object per line: {"messages":[{"role":"user","content":"..."},{"role":"assistant","content":"..."}]}
Loss is masked to assistant response bytes; prompt bytes remain context only.
"""
import argparse
import json
from pathlib import Path

import torch

from ivritlm.config import ModelConfig, TrainConfig
from ivritlm.training import train


ALLOWED_ROLES = {"system", "user", "assistant"}


def load_chat_jsonl_with_mask(path):
    conversations = []
    masks = []
    count = 0
    for line_no, raw in enumerate(Path(path).read_text(encoding="utf-8-sig").splitlines(), 1):
        if not raw.strip():
            continue
        try:
            item = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Line {line_no}: invalid JSON: {exc}") from exc
        messages = item.get("messages") if isinstance(item, dict) else None
        if not isinstance(messages, list) or len(messages) < 2:
            raise ValueError(f"Line {line_no}: expected an object with at least two messages.")
        rendered = []
        conversation_mask = []
        previous_role = None
        assistant_seen = False
        for message in messages:
            if not isinstance(message, dict):
                raise ValueError(f"Line {line_no}: each message must be an object.")
            role, content = message.get("role"), message.get("content")
            if role not in ALLOWED_ROLES or not isinstance(content, str) or not content.strip():
                raise ValueError(f"Line {line_no}: role must be system/user/assistant and content must be non-empty text.")
            if role == previous_role and role != "system":
                raise ValueError(f"Line {line_no}: user and assistant messages must alternate.")
            if role == "assistant":
                assistant_seen = True
            header = f"### {role}\n"
            body = content.strip()
            rendered.append(header + body + "\n")
            conversation_mask.extend([False] * len(header.encode("utf-8")))
            conversation_mask.extend([role == "assistant"] * len(body.encode("utf-8")))
            conversation_mask.append(role == "assistant")
            previous_role = role
        if not assistant_seen or previous_role != "assistant":
            raise ValueError(f"Line {line_no}: conversation must end with an assistant answer.")
        if conversations:
            conversations.append("\n\n")
            masks.extend([False, False])
        conversations.append("".join(rendered))
        masks.extend(conversation_mask)
        count += 1
    text = "".join(conversations)
    if count == 0:
        raise ValueError("No conversations were found in the JSONL file.")
    if len(text) < 100:
        raise ValueError("Chat dataset must contain at least 100 characters.")
    if len(masks) != len(text.encode("utf-8")):
        raise ValueError("Internal error: chat loss mask does not match UTF-8 byte-token positions.")
    return text, count, masks


def load_chat_jsonl(path):
    text, count, _ = load_chat_jsonl_with_mask(path)
    return text, count


def main():
    parser = argparse.ArgumentParser(description="Fine-tune IvritLM on Hebrew conversations.")
    parser.add_argument("--input", required=True, help="JSONL conversation dataset.")
    parser.add_argument("--resume", required=True, help="Existing pretraining checkpoint.pt.")
    parser.add_argument("--output", default="artifacts/pretraining")
    parser.add_argument("--steps", type=int, default=100)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--learning-rate", type=float, default=0.0001)
    args = parser.parse_args()
    if not Path(args.resume).is_file():
        raise FileNotFoundError("A pretraining checkpoint is required before chat fine-tuning.")
    checkpoint = torch.load(args.resume, map_location="cpu", weights_only=False)
    config = ModelConfig(**checkpoint["model_config"])
    text, count, loss_mask = load_chat_jsonl_with_mask(args.input)
    corpus_path = Path(args.output) / "chat-training.txt"
    corpus_path.parent.mkdir(parents=True, exist_ok=True)
    text = text.strip()  # training.read_corpus() strips outer whitespace too
    loss_mask = loss_mask[:len(text.encode("utf-8"))]
    corpus_path.write_text(text, encoding="utf-8")
    result = train(
        corpus_path, args.output, config,
        TrainConfig(steps=args.steps, batch_size=args.batch_size,
                    learning_rate=args.learning_rate),
        "cpu", args.resume, loss_mask=loss_mask,
    )
    result["chat_conversations"] = count
    result["training_mode"] = "assistant-only-masked-sft"
    metrics_path = Path(args.output) / "metrics.json"
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    metrics.update({"chat_conversations": count, "training_mode": "assistant-only-masked-sft", "loss_target": "assistant responses only"})
    metrics_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

"""Supervised chat fine-tuning for the byte-level IvritLM prototype.

Input: JSONL, one object per line: {"messages":[{"role":"user","content":"..."},{"role":"assistant","content":"..."}]}
This first version uses causal next-byte training over role-marked conversations.
"""
import argparse
import json
from pathlib import Path

import torch

from ivritlm.config import ModelConfig, TrainConfig
from ivritlm.training import train


ALLOWED_ROLES = {"system", "user", "assistant"}


def load_chat_jsonl(path):
    conversations = []
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
            rendered.append(f"### {role}\n{content.strip()}\n")
            previous_role = role
        if not assistant_seen or previous_role != "assistant":
            raise ValueError(f"Line {line_no}: conversation must end with an assistant answer.")
        conversations.append("\n".join(rendered))
    if not conversations:
        raise ValueError("No conversations were found in the JSONL file.")
    text = "\n\n".join(conversations)
    if len(text) < 100:
        raise ValueError("Chat dataset must contain at least 100 characters.")
    return text, len(conversations)


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
    text, count = load_chat_jsonl(args.input)
    corpus_path = Path(args.output) / "chat-training.txt"
    corpus_path.parent.mkdir(parents=True, exist_ok=True)
    corpus_path.write_text(text, encoding="utf-8")
    result = train(
        corpus_path, args.output, config,
        TrainConfig(steps=args.steps, batch_size=args.batch_size,
                    learning_rate=args.learning_rate),
        "cpu", args.resume,
    )
    result["chat_conversations"] = count
    result["training_mode"] = "causal-chat-finetuning"
    metrics_path = Path(args.output) / "metrics.json"
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    metrics.update({"chat_conversations": count, "training_mode": "causal-chat-finetuning"})
    metrics_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

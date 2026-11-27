"""Training loop and resumable checkpoint utilities."""
import hashlib
import json
import random
import time
from pathlib import Path
import torch
from torch.nn.utils import clip_grad_norm_
from .config import ModelConfig, TrainConfig
from .model import IvritLM


def read_corpus(path):
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Corpus file not found: {p}")
    text = p.read_text(encoding="utf-8-sig").strip()
    if len(text) < 100:
        raise ValueError("Corpus must contain at least 100 characters.")
    return text


def make_batch(tokens, batch_size, context_length, device):
    if tokens.numel() <= context_length + 1:
        raise ValueError("Tokenized corpus is shorter than context_length + 2.")
    starts = torch.randint(0, tokens.numel() - context_length - 1, (batch_size,))
    x = torch.stack([tokens[i:i + context_length] for i in starts])
    y = torch.stack([tokens[i + 1:i + context_length + 1] for i in starts])
    return x.to(device), y.to(device)


def train(corpus_path, output_dir, model_config=None, train_config=None, device_name="cpu"):
    from .tokenizer import ByteTokenizer
    model_config = model_config or ModelConfig()
    train_config = train_config or TrainConfig()
    model_config.validate()
    train_config.validate()
    random.seed(train_config.seed)
    torch.manual_seed(train_config.seed)
    if device_name.startswith("cuda") and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is not available.")
    device = torch.device(device_name)
    text = read_corpus(corpus_path)
    tokenizer = ByteTokenizer()
    ids = torch.tensor(tokenizer.encode(text), dtype=torch.long)
    split = max(model_config.context_length + 2, int(ids.numel() * (1 - train_config.validation_fraction)))
    split = min(split, ids.numel() - 1)
    train_tokens, val_tokens = ids[:split], ids[split:]
    if val_tokens.numel() <= model_config.context_length + 1:
        val_tokens = train_tokens[-(model_config.context_length + 2):]
    model = IvritLM(model_config).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=train_config.learning_rate)
    started = time.time()
    history = []
    model.train()
    for step in range(1, train_config.steps + 1):
        x, y = make_batch(train_tokens, train_config.batch_size, model_config.context_length, device)
        _, loss = model(x, y)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        if step == 1 or step % train_config.log_interval == 0 or step == train_config.steps:
            model.eval()
            with torch.no_grad():
                vx, vy = make_batch(val_tokens, min(train_config.batch_size, 4), model_config.context_length, device)
                _, val_loss = model(vx, vy)
            row = {"step": step, "train_loss": float(loss.item()), "validation_loss": float(val_loss.item()), "elapsed_seconds": round(time.time() - started, 2)}
            history.append(row)
            print(json.dumps(row))
            model.train()
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    tokenizer.save(str(out / "tokenizer.json"))
    corpus_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    checkpoint = {"model_state_dict": model.state_dict(), "optimizer_state_dict": optimizer.state_dict(), "step": train_config.steps, "model_config": model_config.to_dict(), "train_config": train_config.__dict__, "seed": train_config.seed, "corpus_sha256": corpus_hash, "history": history}
    temporary = out / "checkpoint.tmp"
    torch.save(checkpoint, temporary)
    temporary.replace(out / "checkpoint.pt")
    summary = {"steps": train_config.steps, "parameters": sum(p.numel() for p in model.parameters()), "final_train_loss": history[-1]["train_loss"], "final_validation_loss": history[-1]["validation_loss"], "elapsed_seconds": round(time.time() - started, 2), "device": str(device), "corpus_characters": len(text), "corpus_sha256": corpus_hash}
    (out / "metrics.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary

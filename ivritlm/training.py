"""Incremental training: every run resumes the last checkpoint when supplied."""
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


def _atomic_torch_save(payload, destination):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    torch.save(payload, temporary)
    temporary.replace(destination)


def train(corpus_path, output_dir, model_config=None, train_config=None,
          device_name="cpu", resume_from=None):
    from .tokenizer import ByteTokenizer

    model_config = model_config or ModelConfig()
    train_config = train_config or TrainConfig()
    model_config.validate()
    train_config.validate()
    if device_name.startswith("cuda") and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is not available.")
    device = torch.device(device_name)
    text = read_corpus(corpus_path)
    corpus_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    tokenizer = ByteTokenizer()
    ids = torch.tensor(tokenizer.encode(text), dtype=torch.long)
    split = max(model_config.context_length + 2, int(ids.numel() * (1 - train_config.validation_fraction)))
    split = min(split, ids.numel() - 1)
    train_tokens, val_tokens = ids[:split], ids[split:]
    if val_tokens.numel() <= model_config.context_length + 1:
        val_tokens = train_tokens[-(model_config.context_length + 2):]

    model = IvritLM(model_config).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=train_config.learning_rate)
    start_step = 0
    history = []
    corpus_hashes = []
    if resume_from:
        resume_path = Path(resume_from)
        if resume_path.is_file():
            # This is a project-generated checkpoint, not an untrusted user upload.
            state = torch.load(resume_path, map_location=device, weights_only=False)
            if state.get("model_config") != model_config.to_dict():
                raise ValueError("Checkpoint model configuration differs from this run; refusing an unsafe resume.")
            if state.get("tokenizer_type") != "utf8-byte-v1":
                raise ValueError("Checkpoint tokenizer is incompatible with this training code.")
            model.load_state_dict(state["model_state_dict"])
            optimizer.load_state_dict(state["optimizer_state_dict"])
            for group in optimizer.param_groups:
                group["lr"] = train_config.learning_rate
            start_step = int(state.get("global_step", state.get("step", 0)))
            history = list(state.get("history", []))
            corpus_hashes = list(state.get("corpus_hashes", []))
            rng = state.get("rng_state")
            if rng:
                torch.set_rng_state(rng["torch"])
                random.setstate(rng["python"])
                if torch.cuda.is_available() and rng.get("cuda"):
                    torch.cuda.set_rng_state_all(rng["cuda"])
            print(json.dumps({"event": "resume", "previous_global_step": start_step,
                              "previous_corpora": len(corpus_hashes)}))
        else:
            print(json.dumps({"event": "fresh_start", "reason": "no previous checkpoint found"}))
    if corpus_hash not in corpus_hashes:
        corpus_hashes.append(corpus_hash)

    started = time.time()
    final_step = start_step + train_config.steps
    model.train()
    for global_step in range(start_step + 1, final_step + 1):
        x, y = make_batch(train_tokens, train_config.batch_size, model_config.context_length, device)
        _, loss = model(x, y)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        local_step = global_step - start_step
        if local_step == 1 or local_step % train_config.log_interval == 0 or global_step == final_step:
            model.eval()
            with torch.no_grad():
                vx, vy = make_batch(val_tokens, min(train_config.batch_size, 4), model_config.context_length, device)
                _, val_loss = model(vx, vy)
            row = {"global_step": global_step, "run_step": local_step,
                   "train_loss": float(loss.item()), "validation_loss": float(val_loss.item()),
                   "elapsed_seconds": round(time.time() - started, 2)}
            history.append(row)
            print(json.dumps(row))
            model.train()

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    tokenizer.save(str(out / "tokenizer.json"))
    checkpoint = {
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "global_step": final_step,
        "step": final_step,
        "model_config": model_config.to_dict(),
        "train_config": train_config.__dict__,
        "tokenizer_type": "utf8-byte-v1",
        "seed": train_config.seed,
        "corpus_sha256": corpus_hash,
        "corpus_hashes": corpus_hashes,
        "history": history[-2000:],
        "rng_state": {
            "torch": torch.get_rng_state(),
            "python": random.getstate(),
            "cuda": torch.cuda.get_rng_state_all() if torch.cuda.is_available() else [],
        },
    }
    _atomic_torch_save(checkpoint, out / "checkpoint.pt")
    summary = {
        "global_step": final_step,
        "steps_this_run": train_config.steps,
        "parameters": sum(p.numel() for p in model.parameters()),
        "final_train_loss": history[-1]["train_loss"],
        "final_validation_loss": history[-1]["validation_loss"],
        "elapsed_seconds": round(time.time() - started, 2),
        "device": str(device),
        "corpus_characters": len(text),
        "corpus_sha256": corpus_hash,
        "corpora_seen": len(corpus_hashes),
        "resumed": start_step > 0,
    }
    (out / "metrics.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "run-manifest.json").write_text(json.dumps({
        "summary": summary, "model_config": model_config.to_dict(),
        "train_config": train_config.__dict__, "corpus_hashes": corpus_hashes,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary

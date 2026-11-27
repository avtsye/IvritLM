"""Export IvritLM's byte-tokenized Transformer as HF GPT-2 for GGUF conversion.

The architecture is GPT-2-compatible at the tensor level. The tokenizer is a
byte-level GPT-2 vocabulary with no merge rules, preserving the model's 0..255
UTF-8 byte IDs and the dedicated BOS/EOS IDs.
"""
import argparse
import json
from pathlib import Path

import torch

from ivritlm.config import ModelConfig
from ivritlm.model import IvritLM


def bytes_to_unicode():
    byte_values = list(range(ord("!"), ord("~") + 1))
    byte_values += list(range(ord("¡"), ord("¬") + 1))
    byte_values += list(range(ord("®"), ord("ÿ") + 1))
    codepoints = list(byte_values)
    extra = 0
    for value in range(256):
        if value not in byte_values:
            byte_values.append(value)
            codepoints.append(256 + extra)
            extra += 1
    return dict(zip(byte_values, (chr(value) for value in codepoints)))


def build_tokenizer_files(output, context_length):
    output.mkdir(parents=True, exist_ok=True)
    byte_map = bytes_to_unicode()
    vocab = {byte_map[i]: i for i in range(256)}
    (output / "vocab.json").write_text(json.dumps(vocab, ensure_ascii=False), encoding="utf-8")
    (output / "merges.txt").write_text("#version: 0.2\n", encoding="utf-8")
    tokenizer_config = {
        "tokenizer_class": "GPT2Tokenizer",
        "vocab_size": 258,
        "model_max_length": context_length,
        "add_prefix_space": False,
        "bos_token": "<|bos|>",
        "eos_token": "<|eos|>",
        "added_tokens_decoder": {
            "256": {"content": "<|bos|>", "lstrip": False, "normalized": False, "rstrip": False, "single_word": False, "special": True},
            "257": {"content": "<|eos|>", "lstrip": False, "normalized": False, "rstrip": False, "single_word": False, "special": True},
        },
    }
    (output / "tokenizer_config.json").write_text(json.dumps(tokenizer_config, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "special_tokens_map.json").write_text(
        json.dumps({"bos_token": "<|bos|>", "eos_token": "<|eos|>"}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def export(checkpoint_path, output_dir):
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    config_values = checkpoint["model_config"]
    config = ModelConfig(**config_values)
    model = IvritLM(config)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()
    state = model.state_dict()
    hf = {
        "transformer.wte.weight": state["token_embedding.weight"].contiguous(),
        "transformer.wpe.weight": state["position_embedding.weight"].contiguous(),
        "transformer.ln_f.weight": state["final_norm.weight"].contiguous(),
        "transformer.ln_f.bias": state["final_norm.bias"].contiguous(),
        "lm_head.weight": state["token_embedding.weight"].contiguous(),
    }
    d = config.d_model
    for layer in range(config.n_layers):
        src = f"blocks.{layer}."
        dst = f"transformer.h.{layer}."
        hf[dst + "ln_1.weight"] = state[src + "norm1.weight"].contiguous()
        hf[dst + "ln_1.bias"] = state[src + "norm1.bias"].contiguous()
        hf[dst + "attn.c_attn.weight"] = state[src + "attn.in_proj_weight"].t().contiguous()
        hf[dst + "attn.c_attn.bias"] = state[src + "attn.in_proj_bias"].contiguous()
        hf[dst + "attn.c_proj.weight"] = state[src + "attn.out_proj.weight"].t().contiguous()
        hf[dst + "attn.c_proj.bias"] = state[src + "attn.out_proj.bias"].contiguous()
        hf[dst + "ln_2.weight"] = state[src + "norm2.weight"].contiguous()
        hf[dst + "ln_2.bias"] = state[src + "norm2.bias"].contiguous()
        hf[dst + "mlp.c_fc.weight"] = state[src + "mlp.0.weight"].t().contiguous()
        hf[dst + "mlp.c_fc.bias"] = state[src + "mlp.0.bias"].contiguous()
        hf[dst + "mlp.c_proj.weight"] = state[src + "mlp.2.weight"].t().contiguous()
        hf[dst + "mlp.c_proj.bias"] = state[src + "mlp.2.bias"].contiguous()

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    torch.save(hf, output / "pytorch_model.bin")
    hf_config = {
        "architectures": ["GPT2LMHeadModel"],
        "model_type": "gpt2",
        "vocab_size": config.vocab_size,
        "n_positions": config.context_length,
        "n_ctx": config.context_length,
        "n_embd": config.d_model,
        "n_layer": config.n_layers,
        "n_head": config.n_heads,
        "n_inner": 4 * config.d_model,
        "activation_function": "gelu",
        "resid_pdrop": config.dropout,
        "embd_pdrop": config.dropout,
        "attn_pdrop": config.dropout,
        "layer_norm_epsilon": 1e-5,
        "bos_token_id": 256,
        "eos_token_id": 257,
        "tie_word_embeddings": True,
        "use_cache": True,
    }
    (output / "config.json").write_text(json.dumps(hf_config, indent=2), encoding="utf-8")
    build_tokenizer_files(output, config.context_length)
    print(json.dumps({"exported": str(output), "global_step": checkpoint.get("global_step", 0),
                      "vocab_size": config.vocab_size, "architecture": "GPT2-compatible"},
                     ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    export(args.checkpoint, args.output)


if __name__ == "__main__":
    main()

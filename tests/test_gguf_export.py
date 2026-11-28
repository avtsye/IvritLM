import json
import torch

from ivritlm.config import ModelConfig
from ivritlm.model import IvritLM
from scripts.export_hf import bytes_to_unicode, export
from scripts.patch_llama_cpp import patch


def test_gpt2_byte_mapping_is_lossless():
    mapping = bytes_to_unicode()
    assert len(mapping) == 256
    assert len(set(mapping.values())) == 256


def test_export_writes_hf_gpt2_model_and_byte_vocab(tmp_path):
    config = ModelConfig(context_length=16, d_model=32, n_heads=4, n_layers=1, dropout=0.0)
    model = IvritLM(config)
    checkpoint = tmp_path / "checkpoint.pt"
    torch.save({"model_config": config.to_dict(), "model_state_dict": model.state_dict(), "global_step": 9}, checkpoint)
    out = tmp_path / "hf"
    export(checkpoint, out)
    saved_config = json.loads((out / "config.json").read_text(encoding="utf-8"))
    vocab = json.loads((out / "vocab.json").read_text(encoding="utf-8"))
    assert saved_config["architectures"] == ["GPT2LMHeadModel"]
    assert saved_config["vocab_size"] == 258
    assert vocab["<|bos|>"] == 256 and vocab["<|eos|>"] == 257
    tokenizer_config = json.loads((out / "tokenizer_config.json").read_text(encoding="utf-8"))
    assert tokenizer_config["unk_token"] == "<|eos|>"
    assert (out / "pytorch_model.bin").is_file()
    assert (out / "merges.txt").is_file()
    marker = json.loads((out / "ivritlm_tokenizer.json").read_text(encoding="utf-8"))
    assert marker["tokenizer_type"] == "utf8-byte-v1"
    assert marker["pretokenizer"] == "gpt-2"

def test_llama_cpp_patch_is_guarded_and_idempotent(tmp_path):
    converter = tmp_path / "conversion"
    converter.mkdir()
    base = converter / "base.py"
    base.write_text("    def get_vocab_base_pre(self, tokenizer) -> str:\n        return 'unknown'\n", encoding="utf-8")
    assert patch(tmp_path) is True
    assert patch(tmp_path) is False
    source = base.read_text(encoding="utf-8")
    assert 'return "gpt-2"' in source
    assert source.count("ivritlm_tokenizer.json") == 1

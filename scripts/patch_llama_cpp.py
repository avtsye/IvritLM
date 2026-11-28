"""Patch the pinned llama.cpp converter for IvritLM's no-merge byte tokenizer."""
import argparse
from pathlib import Path


SIGNATURE = "    def get_vocab_base_pre(self, tokenizer) -> str:\n"
GUARD = (
    '        if (self.dir_model / "ivritlm_tokenizer.json").is_file():\n'
    '            return "gpt-2"\n\n'
)


def patch(converter_root):
    target = Path(converter_root) / "conversion" / "base.py"
    if not target.is_file():
        raise FileNotFoundError(f"llama.cpp converter file not found: {target}")
    source = target.read_text(encoding="utf-8")
    if GUARD in source:
        return False
    if SIGNATURE not in source:
        raise RuntimeError("Pinned llama.cpp converter API changed; refusing an unverified patch.")
    target.write_text(source.replace(SIGNATURE, SIGNATURE + GUARD, 1), encoding="utf-8")
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--converter-root", default="llama.cpp")
    args = parser.parse_args()
    changed = patch(args.converter_root)
    print("Patched llama.cpp for IvritLM byte tokenizer." if changed else "llama.cpp patch already present.")


if __name__ == "__main__":
    main()

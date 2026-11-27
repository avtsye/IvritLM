BOS_ID = 256
EOS_ID = 257
VOCAB_SIZE = 258

class ByteTokenizer:
    """Deterministic UTF-8 byte tokenizer; baseline, not final subword tokenizer."""
    vocab_size = VOCAB_SIZE
    bos_id = BOS_ID
    eos_id = EOS_ID

    def encode(self, text, add_special_tokens=True):
        ids = list(text.encode("utf-8"))
        return [BOS_ID, *ids, EOS_ID] if add_special_tokens else ids

    def decode(self, ids):
        raw = bytes(token for token in ids if 0 <= token <= 255)
        return raw.decode("utf-8", errors="replace")

    def save(self, path):
        from pathlib import Path
        Path(path).write_text('{"type":"utf8-byte","vocab_size":258,"bos_id":256,"eos_id":257}\n', encoding="utf-8")

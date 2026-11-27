import torch
from ivritlm.config import ModelConfig
from ivritlm.model import IvritLM
from ivritlm.tokenizer import ByteTokenizer, BOS_ID, EOS_ID


def test_byte_tokenizer_round_trip_hebrew():
    text = "שלום עולם — IvritLM"
    tokenizer = ByteTokenizer()
    assert tokenizer.decode(tokenizer.encode(text)) == text
    assert tokenizer.encode(text)[0] == BOS_ID
    assert tokenizer.encode(text)[-1] == EOS_ID


def test_model_shapes_and_loss():
    model = IvritLM(ModelConfig(context_length=16, d_model=32, n_heads=4, n_layers=1, dropout=0.0))
    x = torch.randint(0, 258, (2, 16))
    logits, loss = model(x, x)
    assert logits.shape == (2, 16, 258)
    assert loss is not None and torch.isfinite(loss)


def test_model_rejects_too_long_context():
    model = IvritLM(ModelConfig(context_length=8, d_model=32, n_heads=4, n_layers=1))
    try:
        model(torch.zeros((1, 9), dtype=torch.long))
    except ValueError as exc:
        assert "context_length" in str(exc)
    else:
        raise AssertionError("Expected context length validation.")

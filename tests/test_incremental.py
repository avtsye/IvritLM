from ivritlm.config import ModelConfig, TrainConfig
from ivritlm.training import train


def test_training_resumes_global_step_and_optimizer(tmp_path):
    corpus = tmp_path / "corpus.txt"
    corpus.write_text(("שלום עולם. זהו טקסט אימון ניסיוני בעברית לבדיקת המשך אימון. " * 80), encoding="utf-8")
    output = tmp_path / "out"
    model = ModelConfig(context_length=16, d_model=32, n_heads=4, n_layers=1, dropout=0.0)
    first = train(str(corpus), str(output), model,
                  TrainConfig(steps=2, batch_size=2, learning_rate=0.001, seed=7, validation_fraction=0.1, log_interval=1))
    assert first["global_step"] == 2
    second = train(str(corpus), str(output), model,
                   TrainConfig(steps=2, batch_size=2, learning_rate=0.001, seed=7, validation_fraction=0.1, log_interval=1),
                   resume_from=str(output / "checkpoint.pt"))
    assert second["global_step"] == 4
    assert second["steps_this_run"] == 2
    assert second["resumed"] is True

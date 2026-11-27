from pathlib import Path
from ivritlm.config import ModelConfig, TrainConfig
from ivritlm.training import train

ROOT = Path(__file__).resolve().parents[1]
if __name__ == "__main__":
    result = train(str(ROOT / "data/smoke/hebrew_sample.txt"), str(ROOT / "artifacts/smoke"), ModelConfig(context_length=64, d_model=64, n_heads=4, n_layers=2, dropout=0.0), TrainConfig(steps=12, batch_size=4, learning_rate=1e-3, seed=42, validation_fraction=0.1, log_interval=3))
    print("SMOKE_TRAIN_OK", result)

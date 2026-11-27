"""Command-line entry point for a real corpus training run."""
import argparse
import json
from ivritlm.config import ModelConfig, TrainConfig
from ivritlm.training import train


def main():
    parser = argparse.ArgumentParser(description="Train IvritLM from random initialization.")
    parser.add_argument("--corpus", required=True, help="UTF-8 text file from an approved corpus.")
    parser.add_argument("--output", default="artifacts/pretraining")
    parser.add_argument("--steps", type=int, default=100)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--context-length", type=int, default=128)
    parser.add_argument("--d-model", type=int, default=128)
    parser.add_argument("--layers", type=int, default=4)
    parser.add_argument("--heads", type=int, default=4)
    parser.add_argument("--learning-rate", type=float, default=0.0003)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--device", default="cpu", choices=["cpu", "cuda"])
    args = parser.parse_args()
    model = ModelConfig(context_length=args.context_length, d_model=args.d_model, n_heads=args.heads, n_layers=args.layers)
    training = TrainConfig(steps=args.steps, batch_size=args.batch_size, learning_rate=args.learning_rate, seed=args.seed)
    print(json.dumps(train(args.corpus, args.output, model, training, args.device), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

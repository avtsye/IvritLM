# Development guide

## Requirements

- Git.
- Python 3.11.
- Virtual environment.
- CPU for tests and tiny smoke training; a GPU is needed for serious experiments.

## Setup

```bash
git clone https://github.com/avtsye/IvritLM.git
cd IvritLM
python -m venv .venv
```

Activate the environment:

- Windows PowerShell: `.venv\\Scripts\\Activate.ps1`
- Linux/macOS: `source .venv/bin/activate`

Install pinned dependencies and run the test suite:

```bash
python -m pip install -r requirements-intake.txt -r requirements-model.txt
python -m pytest -q
python scripts/smoke_train.py
```

## Run a training experiment

```bash
python scripts/train.py --corpus data/corpus/train.txt --steps 100 --batch-size 4 --output artifacts/pretraining
```

The corpus must be UTF-8 text, at least 100 characters, and explicitly approved for training. Do not commit private or restricted data. The generated checkpoint and metrics go under `artifacts/`; generated outputs should not be committed.

Available options:

- `--steps`: optimizer steps.
- `--batch-size`: examples per batch.
- `--context-length`: tokens per training example.
- `--d-model`, `--layers`, `--heads`: Transformer size.
- `--learning-rate`, `--seed`: optimization and reproducibility.
- `--device`: `cpu` or `cuda`.

## Repository structure

- `ivritlm/`: model, tokenizer, configuration, training code.
- `scripts/`: smoke and real-corpus training commands.
- `tests/`: unit tests.
- `configs/`: experiment examples.
- `data/smoke/`: synthetic test-only text.
- `docs/`: operational and architecture documentation.

## Generated files

Do not commit virtual environments, caches, raw corpora, checkpoints, logs, or temporary datasets. The GitHub pretraining workflow uploads checkpoints as short-lived Actions artifacts (14 days); download important outputs and preserve provenance metadata.

## Contribution loop

1. Read the relevant architecture and training documentation.
2. Make a focused change.
3. Add tests.
4. Run the test suite and smoke training.
5. Update `CHANGELOG.md`, `ROADMAP.md`, and operational documentation when behavior changes.

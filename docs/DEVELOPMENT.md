# Development guide

## Requirements

- Git.
- Python 3.11.
- Virtual environment.
- CPU for tests and tiny smoke training; a GPU is needed for serious experiments.

## Setup

Clone the repository, create a Python 3.11 virtual environment, and install:

    python -m pip install -r requirements-intake.txt -r requirements-model.txt
    python -m pytest -q
    python scripts/smoke_train.py

## Run incremental training locally

First run:

    python scripts/train.py --corpus data/corpus/train.txt --steps 100 --batch-size 4 --output artifacts/pretraining

Continue from the same checkpoint:

    python scripts/train.py --corpus data/corpus/train.txt --steps 100 --batch-size 4 --output artifacts/pretraining --resume artifacts/pretraining/checkpoint.pt

The --steps value is the number of additional steps for that invocation. Model configuration and tokenizer must match the checkpoint. Never delete or overwrite the only copy of a valuable checkpoint.

## Prepare Google Drive OAuth

See docs/TRAINING.md for Google Cloud OAuth setup and GitHub Actions secrets. The local helper is:

    python scripts/google_drive_auth.py --client-secrets path/to/client_secret.json

Do not commit the client secrets JSON or refresh token.

## Export a checkpoint to GGUF

    python scripts/export_hf.py --checkpoint artifacts/pretraining/checkpoint.pt --output artifacts/hf-export
    python llama.cpp/convert_hf_to_gguf.py artifacts/hf-export --outfile artifacts/pretraining/model.gguf --outtype f16

The second command requires the pinned llama.cpp checkout and its converter dependencies. The GitHub smoke workflow performs this validation automatically.

## Repository structure

- ivritlm/: model, tokenizer, configuration, training code.
- scripts/: smoke and real training, Drive storage/authentication, and GGUF export.
- tests/: unit and incremental-training tests.
- configs/: experiment examples.
- data/smoke/: synthetic test-only text.
- docs/: operational and architecture guides.

## Generated files

Do not commit virtual environments, caches, raw corpora, checkpoints, logs, OAuth credentials, or temporary datasets. The Drive folder holds versioned model outputs; GitHub Actions artifacts are only a secondary 14-day copy.

## Contribution loop

1. Read architecture and training documentation.
2. Make a focused change.
3. Add tests.
4. Run unit tests and smoke training.
5. Update CHANGELOG.md, ROADMAP.md, and relevant documentation.

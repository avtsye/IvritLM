# Training and automation operations

## Implemented workflows

| Workflow | Trigger | Purpose | Output |
|---|---|---|---|
| `ci.yml` | push, pull request, manual | compile package, install pinned dependencies, run tests, validate dashboard | test result |
| `smoke-train.yml` | model-code changes or manual | 12-step synthetic CPU training check | smoke checkpoint and metrics, 7-day artifact |
| `pretrain.yml` | manual only | bounded training on an approved UTF-8 text file already in the repository | checkpoint, tokenizer metadata, metrics, 14-day artifact |
| `train.yml` | manual from dashboard | inspect a public source and produce a provenance intake report | intake report only |

The source-intake workflow and pretraining workflow are intentionally separate. Submitting a URL to the dashboard does not silently authorize or ingest its contents into the training corpus.

## Model implementation

The package in `ivritlm/` currently includes:

- `config.py`: validated model and training settings.
- `tokenizer.py`: deterministic UTF-8 byte tokenizer (IDs 0–255 for bytes, 256 BOS, 257 EOS).
- `model.py`: randomly initialized decoder-only Transformer with causal self-attention.
- `training.py`: next-token batches, AdamW updates, validation loss, checkpoint and metrics output.

This is a baseline implementation. Byte tokenization is inefficient compared with a trained Hebrew subword tokenizer. There is no claim of useful language ability until a real approved corpus is trained and independently evaluated.

## Run a synthetic smoke test locally

```bash
python -m pip install -r requirements-model.txt
python -m pytest -q
python scripts/smoke_train.py
```

The smoke sample in `data/smoke/hebrew_sample.txt` is synthetic test text only. Never report its checkpoint as a Hebrew model release.

## Run pretraining on a reviewed corpus

The current GitHub-hosted workflow accepts only a `.txt` file already committed inside this repository. Because this repository is public, committing a corpus makes it public too. Do not place private, confidential, personal, gated, or otherwise restricted data here. Review source terms and permission before adding any text.

1. Add the approved corpus at a repository path, for example `data/corpus/train.txt`.
2. Open GitHub → Actions → **IvritLM - Pretraining** → Run workflow.
3. Supply the repository-relative path, a step count from 1 to 1,000, and batch size from 1 to 16.
4. The hosted CPU job trains from random initialization and uploads `checkpoint.pt`, `tokenizer.json`, and `metrics.json` as a 14-day artifact.
5. Download the artifact from that run. Keep its config, corpus provenance, and metrics together.

A short CPU run is an engineering experiment, not meaningful pretraining. The default architecture is intentionally small (128 hidden dimensions, 4 layers, context 128) to keep the first workflow bounded. For larger runs, first configure a suitable GPU runner and external artifact storage; do not assume GitHub-hosted CPU is adequate.

## Checkpoints and limitations

A checkpoint currently contains model weights, optimizer state, step, model/training settings, seed, corpus SHA-256, and logged losses. Atomic local writing is used before artifact upload. A dedicated resume implementation, scheduler state, random-generator-state restoration, source manifest, Git commit metadata, and durable artifact storage are not implemented yet. The Actions artifact expires after 14 days, so download and preserve any run you need.

## Security and operations

- Workflows use read-only repository permissions unless a documented write action is required.
- Only manual dispatch starts pretraining; no training runs automatically on pull requests.
- The workflow validates that the corpus path resolves inside the checked-out repository and that step/batch values stay bounded.
- Never put secrets in corpus files, workflow inputs, logs, or artifacts.
- A standard hosted runner has no guaranteed GPU. Current pretraining explicitly uses CPU.

## Next engineering steps

1. Create an approved corpus manifest with source URL, license/permission review, snapshot/version, checksum, language and split.
2. Build a deterministic corpus cleaner and train/validation/test split process.
3. Replace the byte tokenizer with a trained Hebrew subword tokenizer and preserve tokenizer/model compatibility metadata.
4. Add checkpoint resume, learning-rate scheduling, evaluation, and generation CLI.
5. Add a GPU runner and durable artifact store after hardware and cost are agreed.

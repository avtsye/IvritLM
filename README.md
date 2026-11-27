# IvritLM

**IvritLM** is an experimental, open-source Hebrew-first language model trained from randomly initialized weights.

> **Status: early prototype.** The repository now contains a small decoder-only Transformer, a UTF-8 byte tokenizer baseline, a training loop, and a manual CPU pretraining workflow. No useful or production-ready model has been trained or published. The bundled Hebrew text is synthetic smoke-test material only.

## Current implementation

- **Model:** PyTorch decoder-only Transformer with causal self-attention and tied token/output embeddings.
- **Initialization:** random weights; no pretrained model is loaded.
- **Tokenizer:** deterministic UTF-8 byte tokenizer (258 IDs, including BOS/EOS). It handles Hebrew reliably but is inefficient; a trained Hebrew subword tokenizer remains a next milestone.
- **Training:** next-byte prediction, validation loss logging, and checkpoint plus metrics output.
- **Tests:** tokenizer round-trip, model tensor/loss checks, and a CPU end-to-end smoke run.
- **Compute:** GitHub-hosted CPU is suitable only for tiny experiments. Real pretraining needs a substantially larger approved corpus and suitable compute.

## Where the model is stored

The **model source code** lives in `ivritlm/` in this GitHub repository. The **trained weights** are created only when a training run completes and are saved as `artifacts/pretraining/checkpoint.pt` during the job. The workflow uploads them as a GitHub Actions artifact named `ivritlm-checkpoint-RUN_ID` (14-day retention). They are not part of the website and are not committed to Git. The current repository has no trained production checkpoint.

## Start here

- [Training dashboard](https://avtsye.github.io/IvritLM/) — source intake and run history; it does not itself host model weights.
- [Training operations](docs/TRAINING.md) — how to run smoke tests and actual pretraining.
- [Development guide](docs/DEVELOPMENT.md) — local setup and commands.
- [Architecture](docs/ARCHITECTURE.md) — model/tokenizer/training design.
- [Data policy](docs/DATA_POLICY.md) — approval and provenance requirements.
- [Roadmap](ROADMAP.md) — implemented and pending milestones.
- [Changelog](CHANGELOG.md) — repository changes.

## Start a small real-corpus run

1. Prepare a UTF-8 `.txt` corpus that you are authorized to use for model training.
2. Keep private or restricted data out of this public repository. The current hosted workflow reads a corpus file committed in the repository, so that file becomes public.
3. Open Actions → **IvritLM - Pretraining** → Run workflow.
4. Enter the repository-relative corpus path, such as `data/corpus/train.txt`, and choose a bounded step count.
5. Download the resulting checkpoint artifact and metrics from the completed run.

Do not use `data/smoke/hebrew_sample.txt` as a real training corpus. It exists solely to test that the software executes.

## Repository map

- `.github/workflows/` — CI, source intake, smoke training, and manual pretraining.
- `configs/` — experiment configuration examples.
- `data/smoke/` — synthetic test text only; not training data.
- `docs/` — architecture, data policy, operations, and maintenance guides.
- `ivritlm/` — tokenizer, Transformer, configuration, and training loop.
- `scripts/` — smoke-test and real-training entry points.
- `tests/` — automated tests.

## Limitations and next milestones

The current baseline uses bytes rather than subword tokens, has no corpus curation/manifest pipeline, no scheduler or resume command, and no large-scale GPU orchestration. A successful smoke test proves code execution, not Hebrew language ability. Dataset permissions, privacy, train/validation separation, and compute budget must be reviewed before meaningful pretraining.

Training from scratch is data- and compute-intensive. GitHub Actions is used for repeatable tests and bounded CPU experiments, not promised free GPU training. Code, dataset, and checkpoint licenses are separate questions.

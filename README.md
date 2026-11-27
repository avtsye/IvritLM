# IvritLM

**IvritLM** is an experimental, open-source Hebrew-first language model trained from randomly initialized weights.

> **Status: early prototype.** The repository contains a small decoder-only Transformer, a UTF-8 byte tokenizer baseline, incremental training code, Google Drive checkpoint persistence, and an initial GGUF export path. No useful or production-ready model has been trained or published. The bundled Hebrew text is synthetic smoke-test material only.

## Current implementation

- **Model:** PyTorch decoder-only Transformer with causal self-attention and tied token/output embeddings.
- **Initialization:** random weights for the first run; later runs restore and continue the previous checkpoint.
- **Tokenizer:** deterministic UTF-8 byte tokenizer (258 IDs, including BOS/EOS). It handles Hebrew reliably but is inefficient; a trained Hebrew subword tokenizer remains a next milestone.
- **Incremental training:** restores model weights, optimizer state, global step, and RNG state; each run adds the requested number of optimizer steps.
- **Persistence:** each IvritLM package version has a dedicated Google Drive subfolder containing step-numbered checkpoints, tokenizer metadata, manifests, metrics, and GGUF files. A root-level latest.json points to the newest files. GitHub Actions artifacts are a 14-day secondary copy.
- **GGUF:** exports through a GPT-2-compatible bridge and the pinned llama.cpp converter. Runtime compatibility still requires separate validation.
- **Compute:** GitHub-hosted CPU is suitable only for tiny experiments. Real pretraining needs a substantially larger approved corpus and suitable compute.

## Where the model is stored

- **Model source code:** ivritlm/ in this repository.
- **Latest durable checkpoint:** Google Drive, referenced by root-level latest.json. It contains model tensors, optimizer state, training configuration, RNG state, and corpus hashes.
- **Versioned Drive layout:** IvritLM Models/<module-version>/, for example IvritLM Models/0.1.0/.
- **Versioned checkpoints:** checkpoint-step-000000000100.pt and subsequent step-numbered files inside the module-version folder.
- **GGUF exports:** ivritlm-step-000000000100.gguf and subsequent step-numbered files in the same folder.
- **Tokenizer, metrics, and run manifests:** stored alongside the checkpoint and GGUF.

The actual trained weights are not committed to this Git repository and are not hosted by the dashboard page.

## One-time Google Drive setup

See docs/TRAINING.md. The workflow uses a Google OAuth refresh token stored as GitHub Actions secrets; credentials are never committed to this repository.

## Start a small training run

1. Prepare a UTF-8 .txt corpus that you are authorized to use for model training.
2. Do not put private, confidential, personal, gated, or restricted text in this public repository. The current workflow reads a repository-resident corpus, so that file becomes public.
3. Complete the one-time Drive setup.
4. Open GitHub → Actions → IvritLM - Incremental Pretraining and GGUF Export → Run workflow.
5. Supply the repository-relative corpus path and the number of additional training steps.
6. The workflow restores the latest Drive checkpoint, trains on top of it, saves a new checkpoint, exports GGUF, and uploads the new versioned files to Drive.

Do not use data/smoke/hebrew_sample.txt as a real training corpus. It exists solely to test that the software executes.

## Repository map

- .github/workflows/ — CI, source intake, smoke training, and manual incremental pretraining.
- configs/ — experiment configuration examples.
- data/smoke/ — synthetic test text only; not training data.
- docs/ — architecture, data policy, operations, and maintenance guides.
- ivritlm/ — tokenizer, Transformer, configuration, and training loop.
- scripts/ — training, Drive storage/authentication, and GGUF export.
- tests/ — automated tests.

## Limitations and next milestones

The baseline still uses bytes rather than efficient subword tokens, and the hosted workflow is CPU-only and bounded. The GGUF bridge is an initial GPT-2-compatible export path; it is not a claim of runtime-validated compatibility until conversion and runtime tests pass. The dashboard can dispatch source inspection and incremental pretraining; source inspection still does not automatically build a corpus. Actual training requires Drive secrets and an approved corpus file. Corpus curation, tokenizer training, evaluation, GPU training, and source-to-corpus ingestion remain future work.

Training from scratch is data- and compute-intensive. GitHub Actions is used for repeatable tests and bounded CPU experiments, not promised free GPU training. Code, dataset, and checkpoint licenses are separate questions.

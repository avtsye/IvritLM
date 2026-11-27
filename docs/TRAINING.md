# Training and automation operations

## Workflows

| Workflow | Trigger | Purpose | Output |
|---|---|---|---|
| ci.yml | push, pull request, manual | compile package, install dependencies, run tests | test result |
| smoke-train.yml | model-code changes or manual | synthetic CPU training check | smoke checkpoint and metrics |
| pretrain.yml | manual only | restore Drive checkpoint, add training steps, export GGUF | versioned Drive files plus 14-day Actions artifact |
| train.yml | manual from dashboard | inspect a public source and produce a provenance report | intake report only |

The source-intake workflow and pretraining workflow are separate. The dashboard does not yet dispatch incremental pretraining.

## Incremental training

The model package contains:
- ivritlm/config.py: validated model and training settings.
- ivritlm/tokenizer.py: UTF-8 byte tokenizer (IDs 0–255, BOS 256, EOS 257).
- ivritlm/model.py: randomly initialized decoder-only Transformer.
- ivritlm/training.py: next-token training, AdamW, validation loss, and resumable checkpoints.

When --resume points to a prior checkpoint, training restores model weights, optimizer state, global step, and RNG state. The --steps value means additional steps for this run. Model configuration and tokenizer version must match; incompatible checkpoints are rejected. New corpus SHA-256 values are appended to the checkpoint history.

Each run writes checkpoint.pt (model tensors, optimizer state, config, step, corpus hashes, loss history, RNG state), tokenizer.json, metrics.json, and run-manifest.json.

## One-time Google Drive setup

The workflow uses the owner's OAuth refresh token and the least-privilege drive.file scope. The setup helper creates or finds an IvritLM Models folder in the owner's Drive; files are stored in that account's Drive quota.

1. In Google Cloud Console, create/select a project and enable the Google Drive API.
2. Configure the OAuth consent screen and add the Google account that will authorize Drive. For long-term unattended training, set the app publishing status to In production; refresh tokens issued while an external OAuth app is in Testing mode expire after 7 days, so they would need to be renewed weekly. If you keep Testing mode, add the authorizing account as a test user and expect to repeat authorization when the token expires.
3. Create an OAuth client of type Desktop app and download its client-secrets JSON.
4. In a local clone, install requirements-model.txt and run:
   python scripts/google_drive_auth.py --client-secrets path/to/client_secret.json
5. Complete Google's authorization in the browser. The helper creates or finds the IvritLM Models folder and prints its folder ID, client ID, client secret, and refresh token.
6. In GitHub → repository Settings → Secrets and variables → Actions, create these repository secrets:
   - DRIVE_CLIENT_ID
   - DRIVE_CLIENT_SECRET
   - DRIVE_REFRESH_TOKEN
   - DRIVE_FOLDER_ID (the ID printed by the helper)

The OAuth grant is limited to files created or opened by this IvritLM integration; it does not receive broad access to the rest of Drive. Treat the client secret and refresh token as passwords. Never commit the OAuth JSON, refresh token, checkpoint, or private corpus. Do not paste credentials into chat or workflow logs. If a credential is exposed, revoke it in Google Cloud and create a new one.

## What is stored in Drive

Every successful training run creates versioned files in the selected folder:
- checkpoint-step-000000000100.pt: full trainable weights plus optimizer/RNG state.
- tokenizer-step-000000000100.json: tokenizer metadata.
- manifest-step-000000000100.json: run configuration and corpus hashes.
- metrics-step-000000000100.json: training metrics.
- ivritlm-step-000000000100.gguf: inference-oriented GGUF export.
- latest.json: pointer to the latest checkpoint and GGUF file IDs.

The step number is illustrative. Files are versioned, not overwritten. Drive storage use grows with each run; old versions can be archived or cleaned up after a retention policy is chosen. The checkpoint is uploaded before GGUF conversion, so a conversion failure does not discard newly trained weights. The latest GGUF pointer updates only after export upload succeeds.

## Local smoke test

Install requirements-model.txt, then run:
- python -m pytest -q
- python scripts/smoke_train.py

The text in data/smoke/hebrew_sample.txt is synthetic test material only, not a real training corpus.

## Run incremental pretraining

The hosted workflow accepts only a .txt corpus committed inside this public repository. That file becomes public. Do not put private, confidential, personal, gated, or restricted data here. Review source terms and permission before adding text.

1. Complete the one-time Drive setup.
2. Add an approved UTF-8 corpus, for example data/corpus/train.txt.
3. Open GitHub → Actions → IvritLM - Incremental Pretraining and GGUF Export → Run workflow.
4. Supply the repository-relative corpus path, 1–1,000 additional steps, and batch size 1–16.
5. The workflow downloads the latest Drive checkpoint (or starts from random weights if the folder has no checkpoint), performs additional updates, and uploads a new checkpoint version.
6. It exports to a GPT-2-compatible intermediate format, converts with the pinned llama.cpp revision, validates the GGUF header, and uploads GGUF and metrics to Drive.
7. GitHub Actions also stores a secondary 14-day copy.

A short CPU run is an engineering experiment, not meaningful pretraining. The default architecture is small (128 hidden dimensions, 4 layers, context 128). The hosted workflow explicitly uses CPU; it does not promise free GPU training.

## GGUF conversion status

scripts/export_hf.py maps IvritLM tensors to a GPT-2-compatible state dictionary and builds a byte-level GPT-2 vocabulary with no merge rules. The workflow invokes llama.cpp's convert_hf_to_gguf.py at a pinned commit. This is an initial compatibility bridge, not a claim that every inference runtime has been verified. The GGUF smoke workflow must pass before treating the format as verified.

## Security and operations

- Training starts only through manual dispatch.
- The workflow serializes training runs to prevent concurrent checkpoint races.
- OAuth credentials are passed only through GitHub Actions secrets.
- Corpus paths are validated to remain inside the checked-out repository.
- Checkpoint files contain the full model and optimizer state; protect the Drive folder accordingly.

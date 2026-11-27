# Training and automation operations

## Workflows

| Workflow | Trigger | Purpose | Output |
|---|---|---|---|
| ci.yml | push, pull request, manual | compile package, install dependencies, run tests | test result |
| smoke-train.yml | model-code changes or manual | synthetic CPU training check | smoke checkpoint and metrics |
| pretrain.yml | manual or dashboard | restore Drive checkpoint, add training steps, export GGUF | versioned Drive files plus 14-day Actions artifact |
| train.yml | manual from dashboard | inspect a public source and produce a provenance report | intake report only |

The source-intake workflow and pretraining workflow are separate. Source intake now extracts bounded text from a public GitHub repository or one public web page, filters for Hebrew text, deduplicates documents, creates a corpus candidate and provenance manifest, and uploads both to Google Drive. It does not start training automatically. Review the source rights and corpus before dispatching pretraining.

## Incremental training

The model package contains:
- ivritlm/config.py: validated model and training settings.
- ivritlm/tokenizer.py: UTF-8 byte tokenizer (IDs 0–255, BOS 256, EOS 257).
- ivritlm/model.py: randomly initialized decoder-only Transformer.
- ivritlm/training.py: next-token training, AdamW, validation loss, and resumable checkpoints.

When --resume points to a prior checkpoint, training restores model weights, optimizer state, global step, and RNG state. The --steps value means additional steps for this run. Model configuration and tokenizer version must match; incompatible checkpoints are rejected. New corpus SHA-256 values are appended to the checkpoint history.

Each run writes checkpoint.pt (model tensors, optimizer state, config, step, corpus hashes, loss history, RNG state), tokenizer.json, metrics.json, and run-manifest.json.

## Connect IvritLM to your Google Drive (one time)

The connection is made by Google OAuth on your own computer. The browser page never receives Google credentials. GitHub Actions receives them only as encrypted repository secrets.

### A. Create Google OAuth credentials

1. Open Google Cloud Console and create a project (or select an existing project).
2. In APIs & Services → Library, enable **Google Drive API** for that project.
3. Configure the OAuth consent screen. Add the Google account that owns the Drive folder as a test user if the app is still in Testing.
4. For unattended use beyond the initial test period, set the OAuth app to **In production**. Google refresh tokens for an external app left in Testing normally expire after 7 days. Publishing may require completing Google's verification requirements depending on the app and scopes.
5. In APIs & Services → Credentials, create an **OAuth client ID** with application type **Desktop app**, then download its JSON file. Keep this file private.

### B. Authorize from your computer

In a local clone of this repository, open a terminal in the repository folder and run:

    python -m pip install -r requirements-model.txt
    python scripts/google_drive_auth.py --client-secrets path/to/client_secret.json

Replace the path with the actual location of the downloaded JSON. A Google sign-in/consent page opens. Sign in to the Drive-owning account and approve the requested Drive file access. The script creates or finds the root folder **IvritLM Models** and prints four values:
- DRIVE_CLIENT_ID
- DRIVE_CLIENT_SECRET
- DRIVE_REFRESH_TOKEN
- DRIVE_FOLDER_ID

The helper uses the narrow drive.file scope. It does not request broad read/write access to every file in Drive. It can manage files created by this IvritLM integration.

### C. Add the four values to GitHub

1. Open https://github.com/avtsye/IvritLM/settings/secrets/actions.
2. Choose **New repository secret** for each of the four names above.
3. Paste the corresponding value printed by the local helper into the matching secret. Do not add quotation marks or spaces around it.
4. Save each secret. GitHub masks secrets in workflow logs; do not print them or put them in source files.

Do not paste credentials into ChatGPT, issues, commits, or workflow inputs. Never commit the OAuth JSON or refresh token. If a credential is exposed, revoke it in Google Cloud and repeat authorization.

### D. What the Drive layout looks like

The root folder is **IvritLM Models**. Each package release gets its own subfolder named exactly after ivritlm.__version__. The current package version is 0.1.0:

    My Drive/
      IvritLM Models/
        latest.json
        0.1.0/
          checkpoint-step-000000000100.pt
          tokenizer-step-000000000100.json
          manifest-step-000000000100.json
          metrics-step-000000000100.json
          ivritlm-step-000000000100.gguf
        0.2.0/
          ...

The latest.json file stays in the root folder and points to the newest checkpoint and GGUF file IDs. It keeps checkpoint_module_version/checkpoint_version_folder_id separate from model_module_version/model_version_folder_id, so a failed GGUF export cannot accidentally label an older model file as belonging to the new package version. Files inside a version folder are step-numbered and are not overwritten by later runs. When the package version changes, the next training run creates/uses the new version folder. The model checkpoint itself is resumed from the root latest.json pointer, subject to strict architecture/tokenizer compatibility checks.

### E. Verify the connection

After adding all four secrets, open GitHub → Actions → **IvritLM - Incremental Pretraining and GGUF Export** → Run workflow. Select an approved repository-relative UTF-8 .txt corpus and a small step count for the first test. The workflow's validation step checks that all four secrets exist before it attempts to contact Drive.

A successful run should show the checkpoint and GGUF upload steps as completed. You can also open Google Drive → IvritLM Models and confirm the version subfolder and files. The static dashboard cannot inspect or display the secret values or directly verify Drive connectivity; the workflow run is the authoritative check.

## What is stored in Drive

For each training step count, the version subfolder stores:
- checkpoint-step-000000000100.pt: full trainable weights plus optimizer/RNG state.
- tokenizer-step-000000000100.json: tokenizer metadata.
- manifest-step-000000000100.json: run configuration and corpus hashes.
- metrics-step-000000000100.json: training metrics.
- ivritlm-step-000000000100.gguf: inference-oriented GGUF export.
- Root-level latest.json: pointer to the latest checkpoint and GGUF file IDs.

The step number is illustrative. Drive storage use grows with each run; old versions can be archived or cleaned up after a retention policy is chosen. The checkpoint is uploaded before GGUF conversion, so a conversion failure does not discard newly trained weights. The latest GGUF pointer updates only after export upload succeeds.

## Local smoke test

Install requirements-model.txt, then run:
- python -m pytest -q
- python scripts/smoke_train.py

The text in data/smoke/hebrew_sample.txt is synthetic test material only, not a real training corpus.

## Run incremental pretraining

The hosted workflow accepts only a .txt corpus committed inside this public repository. That file becomes public. Do not put private, confidential, personal, gated, or restricted data here. Review source terms and permission before adding text.

1. Complete the one-time Drive setup above.
2. Add an approved UTF-8 corpus, for example data/corpus/train.txt.
3. Open the training dashboard, enter your GitHub token, and use the incremental-training section; alternatively open GitHub → Actions → IvritLM - Incremental Pretraining and GGUF Export → Run workflow.
4. Supply the repository-relative corpus path, 1–1,000 additional steps, and batch size 1–16.
5. The workflow downloads the latest Drive checkpoint (or starts from random weights if the folder has no checkpoint), performs additional updates, and uploads a new checkpoint version into the current module-version folder.
6. It exports to a GPT-2-compatible intermediate format, converts with the pinned llama.cpp revision, validates the GGUF header, and uploads GGUF and metrics to the same version folder.
7. GitHub Actions also stores a secondary 14-day copy.

A short CPU run is an engineering experiment, not meaningful pretraining. The hosted workflow explicitly uses CPU; it does not promise free GPU training.

## GGUF conversion status

scripts/export_hf.py maps IvritLM tensors to a GPT-2-compatible state dictionary and builds a byte-level GPT-2 vocabulary with no merge rules. The workflow invokes llama.cpp's convert_hf_to_gguf.py at a pinned commit. This is an initial compatibility bridge, not a claim that every inference runtime has been verified. The GGUF smoke workflow must pass before treating the format as verified.

## Security and operations

- Training starts only through manual dispatch.
- The workflow serializes training runs to prevent concurrent checkpoint races.
- OAuth credentials are passed only through GitHub Actions secrets.
- Corpus paths are validated to remain inside the checked-out repository.
- Checkpoint files contain the full model and optimizer state; protect the Drive folder accordingly.


## Source intake and Drive-backed corpus

The dashboard's source form dispatches `train.yml`. After the authorization acknowledgement, the workflow downloads a bounded public source (GitHub archive or one HTML/plain-text page), selects only TXT/Markdown/RST/HTML documents, extracts readable text, filters documents with at least 15% Hebrew letters, deduplicates by SHA-256, and limits the resulting corpus to 5 MiB. Repository code is never executed. The output is a **corpus candidate**, not a license determination; public accessibility and a checkbox do not establish legal permission. Review source terms and the generated corpus before training.

The corpus and its provenance manifest are stored in the Drive folder `IvritLM Corpora`. The root `latest.json` records the latest corpus file ID and SHA-256. The training workflow can now leave `corpus_path` empty to download that latest corpus automatically. A manually supplied repository-relative TXT path remains supported. The first training run starts from random weights if no checkpoint exists; later runs resume the latest compatible IvritLM checkpoint.

Drive layout:

    IvritLM Models/
      latest.json
      0.1.0/
        checkpoint-step-....pt
        tokenizer-step-....json
        manifest-step-....json
        metrics-step-....json
        ivritlm-step-....gguf
      IvritLM Corpora/
        hebrew-corpus-<sha256-prefix>.txt
        manifest-<sha256-prefix>.json

Source intake and pretraining both require the four Google Drive repository secrets. The dashboard token needs Actions read/write permission to dispatch workflows and read workflow runs.

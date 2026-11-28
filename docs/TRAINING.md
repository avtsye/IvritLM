# Training and automation operations

## Workflows

| Workflow | Trigger | Purpose | Output |
|---|---|---|---|
| ci.yml | push, pull request, manual | compile package, install dependencies, run tests | test result |
| smoke-train.yml | model-code changes or manual | synthetic CPU training check | smoke checkpoint and metrics |
| pretrain.yml | manual or dashboard | restore Drive checkpoint, add training steps, export GGUF | versioned Drive files plus 14-day Actions artifact |
| train.yml | dashboard | crawl a public source and build a Hebrew corpus | versioned corpus and provenance in Drive |
| ingest-text.yml | dashboard | ingest pasted Hebrew text | corpus and provenance in Drive |

The dashboard is a single control center for adding text, crawling sources, starting training, and reviewing workflow runs. Users can paste up to 40,000 characters per ingestion run or load a local TXT file. Public website intake crawls up to 500 same-host pages (depth 5, 100 MiB total downloaded, 0.5-second request delay); public GitHub intake extracts supported TXT/Markdown/RST/HTML files. Intake requires at least 40% Hebrew letters per document, deduplicates documents, writes a corpus and provenance manifest, and uploads them to Drive. Ingestion and pretraining remain separate actions. Pretraining requires an explicit approval input confirming that source rights and corpus contents were reviewed.

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

The helper uses the narrow drive.file scope. It does not request broad read/write access to every file in Drive. It can manage files created by this IvritLM integration. The Drive scripts initialize `truststore` before networking, using the Windows/system certificate store while keeping TLS certificate verification enabled. If a filtering proxy is used, its trusted CA certificate must be installed in the operating system trust store; do not disable SSL verification.

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

1. Complete the one-time Google Drive setup above and add the four GitHub Actions secrets.
2. Optionally run the dashboard's source intake to create a Hebrew corpus candidate in Drive. Review its source rights and provenance before training.
3. In the dashboard's incremental-training section, leave the corpus path empty to use the latest corpus from Drive, or enter a repository-relative UTF-8 .txt file path.
4. Choose 1–1,000 additional steps and batch size 1–16, then dispatch the workflow.
5. The workflow restores the latest checkpoint and (when path is empty) the latest Drive corpus. If no checkpoint exists, it starts from random weights.
6. It trains, saves a new checkpoint, exports to a GPT-2-compatible intermediate format, converts with the pinned llama.cpp revision, validates the GGUF header, and uploads GGUF and metrics to the module-version folder.
7. GitHub Actions also stores a secondary 14-day copy.

The source-intake process creates a corpus candidate; it does not certify copyright or usage rights. Only use sources for which you have explicit authorization. Dashboard paste intake is limited to 40,000 characters per run; multiple batches are appended to a cumulative corpus with duplicate-record filtering. The current model is a small from-scratch Transformer prototype with a UTF-8 byte tokenizer. A short CPU run is an engineering experiment, not meaningful pretraining. The hosted workflow uses CPU and does not promise free GPU training.

## GGUF conversion status

scripts/export_hf.py maps IvritLM tensors to a GPT-2-compatible state dictionary and builds a byte-level GPT-2 vocabulary with no merge rules. The workflow invokes llama.cpp's convert_hf_to_gguf.py at a pinned commit. This is an initial compatibility bridge, not a claim that every inference runtime has been verified. The GGUF smoke workflow must pass before treating the format as verified.

## Security and operations

- Training starts only through manual dispatch and requires explicit data-review approval.
- The workflow serializes training runs to prevent concurrent checkpoint races.
- OAuth credentials are passed only through GitHub Actions secrets.
- Corpus paths are validated to remain inside the checked-out repository.
- Checkpoint files contain the full model and optimizer state; protect the Drive folder accordingly.


## Source intake and Drive-backed corpus

The dashboard's source form dispatches `train.yml`. After the authorization acknowledgement, the workflow downloads a bounded public source (GitHub archive or same-host pages discovered from sitemaps and links), selects only TXT/Markdown/RST/HTML documents, extracts readable text, filters documents with at least 40% Hebrew letters, deduplicates by SHA-256, and limits the resulting corpus to 100 MiB. Repository code is never executed. The output is a **corpus candidate**, not a license determination; public accessibility and a checkbox do not establish legal permission. Review source terms and the generated corpus before training.

The corpus and its provenance manifest are stored in the Drive folder `IvritLM Corpora`. Source intake never dispatches training automatically; review rights and contents first, then approve manually in the pretraining form. The root `latest.json` records the latest corpus file ID and SHA-256. The training workflow can now leave `corpus_path` empty to download that latest corpus automatically. A manually supplied repository-relative TXT path remains supported. The first training run starts from random weights if no checkpoint exists; later runs resume the latest compatible IvritLM checkpoint.

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

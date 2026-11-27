# Training and automation operations

## What GitHub Actions is for

GitHub Actions should orchestrate repeatable tasks:

- formatting, linting, type checks, and unit tests;
- data-manifest validation and small data-quality checks;
- tokenizer and model CPU smoke tests;
- small, bounded experiments;
- packaging metadata and publishing approved artifacts.

A standard hosted runner is not assumed to have a GPU or enough memory/time for meaningful large-scale pretraining. Do not start an expensive training job until its hardware, runtime, storage, and cost are known.

## Workflow design

Planned workflows:

| Workflow | Trigger | Purpose |
|---|---|---|
| `ci.yml` | push and pull request | fast code checks and tests |
| `data-check.yml` | pull request or manual | validate manifests and dataset metadata |
| `smoke-train.yml` | manual or selected changes | tiny deterministic CPU training run |
| `train.yml` | manual dispatch only initially | controlled training on explicitly configured compute |
| `evaluate.yml` | after a checkpoint is produced | held-out evaluation and report |

The actual workflow files and their triggers are authoritative. This table describes the intended design, not workflows that already exist.

## Safe workflow defaults

- Use least-privilege workflow permissions.
- Pin third-party Actions to reviewed commit SHAs.
- Do not expose secrets to workflows triggered by untrusted pull requests.
- Require explicit manual dispatch for compute-intensive training.
- Validate configuration and data manifests before allocating compute.
- Set bounded timeouts and save checkpoints periodically.
- Never print tokens, credentials, or private dataset locations in logs.
- Avoid uploading raw training data as public workflow artifacts.

## Checkpointing and resume

A checkpoint must include model weights and the state needed for a faithful resume (optimizer, scheduler, step, random-number generator state, and config metadata). Save atomically where possible. On resume, verify compatibility with the model config, tokenizer, dataset version, and code revision. A weights-only export is not a resumable training checkpoint.

GitHub-hosted job storage is temporary. Use a deliberate artifact strategy with retention settings, checksums, and access controls. Do not rely on a later job finding files left on a previous runner.

## GPU strategy

The training workflow must not assume that a standard GitHub-hosted runner includes a GPU. If a GPU runner or external compute provider is configured, document:

- hardware model and VRAM;
- runner labels and trust boundary;
- who pays for compute and storage;
- how credentials are supplied;
- network and data access;
- maximum job duration;
- artifact/checkpoint retention;
- how to stop a runaway job.

## Manual run procedure

Once `train.yml` exists:

1. Review the current training config and dataset manifest.
2. Confirm the target runner and estimated resource requirements.
3. Start the workflow with the intended config and run identifier.
4. Monitor logs and resource usage.
5. Confirm that checkpoints and metadata were uploaded.
6. Run evaluation on the held-out split.
7. Record the outcome in the experiment log and changelog.

Do not describe a run as successful merely because the workflow exited with code zero; verify artifacts and evaluation outputs.

## Current status

Training workflows are planned. They are not considered available until their YAML files, validation, and documentation are committed.

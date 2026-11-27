# Development guide

This guide describes the intended local workflow. Commands will be updated when the corresponding package files land.

## Requirements

- Git.
- Python 3.11 or newer (the exact supported version will be pinned in `pyproject.toml`).
- A virtual environment.
- CPU is sufficient for linting, unit tests, and tiny smoke tests. A GPU is optional for local experiments.

## Initial checkout

```bash
git clone https://github.com/avtsye/IvritLM.git
cd IvritLM
python -m venv .venv
```

Activate the environment:

- Windows PowerShell: `.venv\\Scripts\\Activate.ps1`
- Linux/macOS: `source .venv/bin/activate`

When dependency metadata is added, install using the repository's pinned development requirements. Do not install arbitrary latest versions and then report the environment as reproducible.

## Expected developer loop

1. Read this guide and the relevant document under `docs/`.
2. Create a focused branch for a change.
3. Make the smallest coherent implementation.
4. Add or update tests.
5. Run formatting, static checks, and tests using the commands documented by the project.
6. Update `CHANGELOG.md` and any affected operational documentation.
7. Open a pull request describing behavior changes, validation, and any migration steps.

## Configuration

Experiment settings belong in version-controlled YAML files under `configs/`. Avoid hard-coded training parameters. Record the exact config used for each run.

## Generated files

Do not commit virtual environments, caches, raw corpora, checkpoints, logs, or temporary datasets. Large artifacts should be stored in an explicitly configured artifact store or release, with checksums and provenance metadata.

## Current status

The repository is in bootstrap stage. If a command or component described as planned is not present in the tree, do not assume it is implemented. Check the README and ROADMAP before using it.

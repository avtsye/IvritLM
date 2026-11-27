# Contributing to IvritLM

Thank you for helping improve the project. Contributions should be understandable, testable, and documented.

## Before changing code

1. Read [README.md](README.md), [the architecture](docs/ARCHITECTURE.md), and the relevant subsystem guide.
2. Check [ROADMAP.md](ROADMAP.md) and [CHANGELOG.md](CHANGELOG.md) to understand current status.
3. For data-related work, read [the data policy](docs/DATA_POLICY.md) first.
4. Keep changes focused and avoid unrelated refactors.

## Required for a code change

- Add or update tests.
- Update user-facing documentation if commands, configuration, outputs, or behavior change.
- Update `CHANGELOG.md` under Unreleased.
- Update the roadmap when a milestone changes.
- Add a decision-log entry for durable architectural changes.
- Include exact validation commands and results in the pull request.

## Required for a dataset change

- Provide source provenance and license/permission evidence.
- Add or update the dataset manifest.
- Describe normalization, filtering, and deduplication.
- Explain how train/evaluation isolation is preserved.
- Do not commit restricted or private raw data.

## Pull request checklist

- [ ] Scope and motivation are clear.
- [ ] Tests were added or updated.
- [ ] All relevant checks pass.
- [ ] Documentation and changelog are updated.
- [ ] No secrets, private data, or unlicensed corpus content is included.
- [ ] Any performance or compute implications are stated.

## Maintainer release procedure

1. Review the diff and provenance of changed data.
2. Run the complete CI suite.
3. Verify model/checkpoint and tokenizer compatibility, if applicable.
4. Review evaluation results and known limitations.
5. Update version and changelog.
6. Publish artifacts with checksums and metadata.
7. Create a release with concise installation, usage, and rollback instructions.

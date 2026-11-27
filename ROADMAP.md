# Roadmap

This roadmap describes intended milestones. Items are not complete until implemented, tested, and reflected in the changelog.

## M0 — Repository foundation
- [x] Establish project identity and scope.
- [x] Document architecture direction and from-scratch requirement.
- [x] Document data provenance and operational constraints.
- [ ] Add code license and contribution templates.

## M1 — Reproducible Python package
- [ ] Add pinned project/development dependencies.
- [ ] Add package skeleton and configuration validation.
- [ ] Add linting, formatting, and basic CI.
- [ ] Add deterministic CPU unit-test setup.

## M2 — Hebrew tokenizer
- [ ] Add corpus manifest schema and validator.
- [ ] Add deterministic normalization and deduplication.
- [ ] Train SentencePiece tokenizer from approved training data only.
- [ ] Add tokenizer coverage and round-trip tests.

## M3 — Minimal model
- [ ] Implement decoder-only Transformer with random initialization.
- [ ] Add causal-mask and tensor-shape tests.
- [ ] Add a tiny synthetic-data training smoke test.
- [ ] Add local text-generation CLI.

## M4 — Training pipeline
- [ ] Add config-driven training loop and scheduler.
- [ ] Add resumable checkpoints and run metadata.
- [ ] Add Actions workflows for CI and bounded smoke training.
- [ ] Add explicit external/GPU runner configuration documentation.

## M5 — First Hebrew experiment
- [ ] Approve and version a legally usable Hebrew corpus.
- [ ] Train a baseline tokenizer and small model.
- [ ] Evaluate on isolated held-out data.
- [ ] Publish a report with limitations and reproducibility metadata.

## M6 — Iterative improvement
- [ ] Compare model sizes and context lengths.
- [ ] Improve data quality and coverage.
- [ ] Track regressions across fixed evaluation suites.
- [ ] Publish versioned checkpoints only after release gates pass.

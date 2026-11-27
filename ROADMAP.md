# Roadmap

Items are complete only when code, tests, and documentation are present.

## M0 — Repository foundation
- [x] Establish project identity, scope, and architecture direction.
- [x] Document data provenance and operational constraints.
- [x] Add Hebrew RTL source-intake dashboard and workflow.
- [x] Connect dashboard to incremental pretraining dispatch.
- [x] Add CI validation for the dashboard and intake script.
- [ ] Enable GitHub Pages in repository settings and verify public deployment.

## M1 — Reproducible Python package
- [x] Add initial package skeleton and validated model/training configuration.
- [x] Pin initial PyTorch and pytest dependencies.
- [x] Add basic model CI and unit tests.
- [ ] Add linting, formatting, and broader static checks.

## M2 — Hebrew tokenizer and corpus
- [x] Add deterministic UTF-8 byte tokenizer baseline with Hebrew round-trip test.
- [ ] Add approved corpus manifest schema and validator.
- [ ] Add deterministic normalization and deduplication pipeline.
- [ ] Train and evaluate an efficient Hebrew subword tokenizer.

## M3 — Minimal model
- [x] Implement decoder-only Transformer with random initialization and causal attention.
- [x] Add model shape/loss tests and context-length validation.
- [x] Add tiny synthetic-data CPU smoke training.
- [x] Add basic autoregressive generation method.
- [x] Add a GPT-2-compatible weight/tokenizer export bridge with unit tests.
- [ ] Verify GGUF conversion and runtime inference in CI.

## M4 — Training pipeline
- [x] Add next-token training loop, validation-loss logging, and checkpoint/metrics output.
- [x] Add bounded manual CPU pretraining workflow.
- [x] Resume model weights and optimizer state across runs; preserve global step and RNG state.
- [x] Add versioned Google Drive checkpoint, tokenizer, metrics, and GGUF persistence.
- [x] Add manual incremental training workflow with a pinned llama.cpp converter.
- [ ] Add learning-rate scheduler and richer hardware/code-revision metadata.
- [ ] Add secure GPU runner and evaluate durable artifact retention/cost.

## M5 — First Hebrew experiment
- [ ] Approve and version a legally usable Hebrew corpus.
- [ ] Train a baseline subword tokenizer and a small model on real approved data.
- [ ] Evaluate on isolated held-out data.
- [ ] Publish a report with limitations and reproducibility metadata.

## M6 — Iterative improvement
- [ ] Compare model sizes and context lengths.
- [ ] Improve data quality and Hebrew coverage.
- [ ] Track regressions across fixed evaluation suites.
- [ ] Publish versioned checkpoints only after release gates pass.

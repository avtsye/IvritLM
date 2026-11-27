# Testing and evaluation

## Automated checks

- `python -m compileall -q ivritlm scripts tests` — syntax compilation.
- `python -m pytest -q` — tokenizer and model unit tests.
- `python scripts/smoke_train.py` — tiny end-to-end CPU training and checkpoint creation.
- `node --check site/app.js` — dashboard JavaScript syntax.

CI installs the pinned dependencies and runs compilation, tests, and dashboard checks. The separate smoke-training workflow uploads its checkpoint and metrics as a seven-day artifact.

## What the tests cover

- Hebrew UTF-8 byte-tokenizer round-trip and special token IDs.
- Transformer output shape, finite next-token loss, and context-length rejection.
- End-to-end optimizer update and checkpoint/metrics generation through the smoke workflow.

## What remains to test

- Explicit causal-leakage regression test.
- Checkpoint load/resume equivalence.
- Train/validation/test document-level isolation.
- Corpus manifest validation, deduplication, and normalization.
- Evaluation and generation quality on a fixed held-out Hebrew test set.

## Interpretation

A passing smoke test proves that the code path executes and weights can be updated. It does not demonstrate Hebrew fluency, factual reliability, or usefulness. Synthetic smoke text is not an approved training corpus.

## Release gates

A release candidate needs passing CI, approved corpus provenance, reproducible configuration, verified checkpoint checksum, held-out evaluation report, known limitations, and license review for all distributed artifacts.

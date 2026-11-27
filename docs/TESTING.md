# Testing and evaluation

## Automated checks

- python -m compileall -q ivritlm scripts tests — syntax compilation.
- python -m pytest -q — tokenizer, model, incremental-resume, and export-structure tests.
- python scripts/smoke_train.py — tiny end-to-end CPU training and checkpoint creation.
- GGUF smoke workflow — exports a synthetic checkpoint through the pinned llama.cpp converter and checks the GGUF magic header.
- node --check site/app.js — dashboard JavaScript syntax.

## What the tests cover

- Hebrew UTF-8 byte-tokenizer round-trip and special token IDs.
- Transformer output shape, finite next-token loss, and context-length rejection.
- A second training run resumes from the first checkpoint, restores optimizer state, and advances the global step rather than starting at zero.
- GPT-2 byte vocabulary mapping and export file/tensor metadata.
- End-to-end smoke training and GGUF file generation in GitHub Actions.

## What remains to test

- Load the produced GGUF with llama.cpp inference runtime and verify tokenizer round-trip on Hebrew.
- Compare logits from the PyTorch model and converted GGUF model on the same byte-token inputs.
- Explicit causal-leakage regression test.
- Train/validation/test document-level isolation.
- Corpus manifest validation, deduplication, and normalization.
- Evaluation and generation quality on a fixed held-out Hebrew test set.

## Interpretation

A passing smoke test proves that the software path executes and weights can be updated. It does not demonstrate Hebrew fluency, factual reliability, or usefulness. Synthetic smoke text is not an approved training corpus.

## Release gates

A release candidate needs passing CI, verified GGUF conversion and runtime loading, approved corpus provenance, reproducible configuration, verified checkpoint checksum, held-out evaluation report, known limitations, and license review for all distributed artifacts.

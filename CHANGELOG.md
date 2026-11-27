# Changelog

## Unreleased

### Added
- Incremental training that restores model weights, optimizer state, global step, and random-generator state from the prior checkpoint.
- Corpus SHA-256 history and per-run metrics/manifests.
- Google Drive OAuth helper and resumable uploads organized into one subfolder per IvritLM package version.
- Root-level latest.json pointer to the newest checkpoint and GGUF, while step-numbered outputs remain inside their version folder.
- Expanded Google Drive connection guide covering OAuth setup, local authorization, GitHub Actions secrets, and verification.
- GPT-2-compatible export bridge for the current byte-tokenized Transformer.
- Manual incremental pretraining workflow that restores Drive state, trains additional steps, saves the checkpoint, converts to GGUF, and uploads the result.
- Hebrew dashboard controls for dispatching incremental training with corpus path, additional steps, and batch size.
- Tests for incremental checkpoint resume and HF export structure.

### Limitations
- Drive OAuth secrets and folder ID must be configured by the repository owner before the incremental workflow can run.
- GGUF conversion/runtime compatibility still needs a successful end-to-end smoke workflow and runtime loading test.
- The byte tokenizer is a simple baseline, not the intended efficient Hebrew subword tokenizer.
- The bundled sample corpus is synthetic and must not be treated as real training data.
- Hosted pretraining remains CPU-only and bounded; it is not suitable for large-scale pretraining.
- The current source-intake dashboard validates source metadata but does not yet ingest source text into the training corpus.
- No scheduler, corpus curation pipeline, efficient tokenizer, GPU orchestration, or published production checkpoint exists yet.

### Previously added
- Initial PyTorch decoder-only Transformer, UTF-8 byte tokenizer, and next-token training loop.
- RTL web dashboard and public-source intake validation workflow.
- Bounded source inspection and JSON provenance report artifact.
- Documentation for dashboard token handling and training operations.

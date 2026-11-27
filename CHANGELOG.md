# Changelog

## Unreleased

### Added
- Initial PyTorch decoder-only Transformer (`ivritlm/model.py`) with causal attention, random initialization, and autoregressive generation.
- UTF-8 byte tokenizer baseline with dedicated BOS/EOS IDs and Hebrew round-trip support.
- Config validation, next-token training loop, validation-loss logging, atomic checkpoint write, and metrics JSON.
- CPU smoke-training script and Actions workflow that uploads a test checkpoint.
- Manual bounded CPU pretraining workflow for a reviewed UTF-8 text corpus stored in the repository.
- Model unit tests and CI dependency installation/test execution.
- Documentation of model source location, checkpoint artifact storage, and current limitations.

### Limitations
- The byte tokenizer is a simple baseline, not the intended efficient Hebrew subword tokenizer.
- The bundled sample corpus is synthetic and must not be treated as real training data.
- Pretraining workflow is CPU-only and limited to 1,000 steps; it is not suitable for large-scale training.
- No scheduler, resume command, approved corpus manifest, or published production checkpoint exists yet.
- Source intake dashboard remains separate from the actual pretraining workflow.

### Previously added
- RTL web dashboard and public-source intake validation workflow.
- Bounded source inspection and JSON provenance report artifact.
- Documentation for GitHub Pages activation and dashboard token handling.

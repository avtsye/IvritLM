# Testing and evaluation

## Test layers

1. **Static checks:** formatting, linting, type checks, and configuration validation.
2. **Unit tests:** tokenizer behavior, tensor shapes, causal attention masks, loss calculation, checkpoint serialization.
3. **Integration tests:** tiny end-to-end training and inference using synthetic or explicitly approved miniature data.
4. **Data checks:** encoding validity, duplicate rates, manifest completeness, split isolation, and Hebrew-script statistics.
5. **Model evaluation:** held-out next-token loss/perplexity and a documented qualitative Hebrew test suite.

## Critical correctness checks

- Causal attention must not expose future tokens.
- Training and validation documents must not overlap.
- Tokenizer training must use only the training corpus.
- Padding and ignored labels must not contribute to loss.
- Checkpoint resume must restore optimizer and scheduler state.
- Inference must load the tokenizer associated with the checkpoint.
- Tests must not download unknown corpora or model weights implicitly.

## Metrics

Report validation loss and perplexity with the dataset version and tokenization details. Perplexity values are only meaningfully comparable when the evaluation data and tokenizer conventions are comparable.

Qualitative examples should be sampled from a fixed, documented prompt set and reviewed for grammaticality, coherence, repetition, and factual reliability. Include failures, not only favorable samples.

## Release gates

A release candidate must have:

- passing CI;
- reproducible config and data metadata;
- a verified checkpoint and checksum;
- evaluation report;
- documented known limitations;
- license and provenance review for all distributed artifacts.

A smoke test proves that the pipeline executes. It does not prove language competence.

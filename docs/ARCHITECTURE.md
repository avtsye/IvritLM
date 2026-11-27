# Architecture

## Goal

IvritLM is intended to be a Hebrew-first, decoder-only Transformer language model trained with next-token prediction from randomly initialized parameters.

## Planned pipeline

1. **Corpus manifest:** identifies approved source datasets, versions, licenses/permissions, and checksums.
2. **Text normalization:** deterministic Unicode normalization and conservative cleanup. Preserve Hebrew letters, punctuation, and meaningful formatting; log every transformation.
3. **Tokenizer:** train a SentencePiece tokenizer on the approved training split only. Store its vocabulary size, model file checksum, normalization settings, and training-corpus manifest.
4. **Tokenization:** convert documents into token sequences, keeping document boundaries explicit and preventing train/evaluation leakage.
5. **Model:** decoder-only Transformer with causal attention, token embeddings, positional representation, normalization, feed-forward blocks, and a language-model head.
6. **Training:** causal language modeling; predict the next token using only preceding context.
7. **Evaluation:** held-out loss/perplexity, tokenizer coverage and Hebrew-specific qualitative test cases.
8. **Inference:** load a named checkpoint and its exact tokenizer/config pair.

## Initial scale

The first milestone targets a deliberately small model (approximately 10–30 million parameters) to validate the complete engineering pipeline. This is a development target, not a claim that this scale will produce a broadly capable assistant. Parameter count, context length, vocabulary size, and batch settings must be recorded in the experiment config.

## From-scratch requirement

The initial model must use random initialization. No pretrained language-model checkpoint, embedding matrix, or transferred model weights may be loaded. Generic software libraries and tokenizer implementations are allowed; they are not model pretraining.

## Reproducibility metadata

Each training run should record:

- Git commit SHA.
- Config file and resolved configuration.
- Tokenizer artifact hash.
- Dataset manifest and split hashes.
- Random seed.
- Python, PyTorch, CUDA, and hardware details.
- Training steps, tokens seen, elapsed time, loss, and validation metrics.
- Checkpoint hash and whether training completed or stopped early.

## Design principles

- Keep model, tokenizer, dataset, training loop, evaluation, and inference as separate modules.
- Make configuration explicit and validate it before starting expensive work.
- Support checkpoint resume without silently changing optimizer or scheduler state.
- Keep CPU smoke tests small and deterministic.
- Never confuse a successful pipeline test with evidence of model quality.

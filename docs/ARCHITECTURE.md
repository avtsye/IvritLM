# Architecture

## Goal

IvritLM is a Hebrew-first decoder-only Transformer trained with next-token prediction from randomly initialized parameters.

## Implemented baseline

1. `ivritlm/config.py` validates model and training parameters.
2. `ivritlm/tokenizer.py` maps UTF-8 bytes to IDs 0–255 and reserves 256/257 for BOS/EOS. This is lossless for Hebrew Unicode but inefficient in sequence length; it is a temporary baseline.
3. `ivritlm/model.py` implements token and position embeddings, pre-normalized causal self-attention blocks, GELU feed-forward layers, final normalization, and a tied language-model head.
4. `ivritlm/training.py` samples shifted token windows, optimizes cross-entropy with AdamW, logs train/validation loss, and writes a checkpoint and metrics JSON.
5. `scripts/smoke_train.py` runs a tiny deterministic software test on synthetic Hebrew text.
6. `scripts/train.py` is the command-line entry point for a UTF-8 text corpus approved for training.

## From-scratch requirement

The model is initialized randomly. No pretrained language-model checkpoint, embedding matrix, or transferred weights are loaded. PyTorch is used as a tensor/autograd framework, not as a source of pretrained weights.

## Next pipeline stages

- Approved corpus manifest with provenance, license basis, version, and checksum.
- Deterministic text normalization, deduplication, and split isolation.
- Train a Hebrew subword tokenizer on training data only.
- Evaluation on a held-out set, including loss/perplexity and a fixed Hebrew prompt suite.
- Checkpoint resume, learning-rate scheduler, inference CLI, and complete run metadata.

## Scale and limitations

The current pretraining workflow uses a small CPU-oriented configuration: 128-dimensional hidden state, 4 layers, 4 attention heads, and 128-token context. It is designed to validate the pipeline, not to produce a capable assistant. Realistic from-scratch training requires a much larger clean corpus and suitable GPU compute.

## Reproducibility metadata

The current checkpoint stores model and training configuration, random seed, corpus SHA-256, optimizer state, step, and loss history. Git revision, hardware/software inventory, RNG state, and a signed corpus manifest are still pending.

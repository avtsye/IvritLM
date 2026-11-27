# Architecture

## Goal

IvritLM is a Hebrew-first decoder-only Transformer trained with next-token prediction from randomly initialized parameters.

## Implemented baseline

1. ivritlm/config.py validates model and training parameters.
2. ivritlm/tokenizer.py maps UTF-8 bytes to IDs 0–255 and reserves 256/257 for BOS/EOS. This is lossless for Hebrew Unicode but inefficient in sequence length; it is a temporary baseline.
3. ivritlm/model.py implements token and position embeddings, pre-normalized causal self-attention blocks, GELU feed-forward layers, final normalization, and a tied language-model head.
4. ivritlm/training.py samples shifted token windows, optimizes with AdamW, logs train/validation loss, and writes resumable checkpoints.
5. scripts/drive_storage.py restores the latest checkpoint and writes outputs under IvritLM Models/<ivritlm.__version__>/ in the user's Drive. The root-level latest.json points to the newest checkpoint and model files.
6. scripts/export_hf.py maps the custom Transformer tensors into a GPT-2-compatible intermediate format for GGUF conversion.
7. scripts/smoke_train.py runs a tiny deterministic software test on synthetic Hebrew text.

## Incremental checkpoint design

A checkpoint includes model tensors, optimizer state, global step, model/training config, tokenizer version, corpus SHA-256 history, loss history, and RNG state. On resume, the implementation verifies model and tokenizer compatibility, restores the optimizer and random generators, and applies additional optimizer steps. It refuses an incompatible architecture rather than silently starting over.

Each Python package version has a separate Drive subfolder. Checkpoint, tokenizer, manifest, metrics, and GGUF files are step-numbered inside that folder. The root latest.json remains the cross-version pointer used by the next run. It stores checkpoint and GGUF version-folder metadata separately, so a failed export cannot associate an older GGUF with a newer checkpoint version. The workflow uploads a new checkpoint before attempting GGUF conversion, then updates the latest GGUF pointer only after conversion and upload succeed. A failed export therefore does not erase the most recent trained weights.

## GGUF export bridge

The current model is a small GPT-2-like decoder. The exporter maps token and position embeddings, fused Q/K/V attention projections, layer norms, and feed-forward projections to GPT-2 tensor names. It builds a 258-entry byte vocabulary with BOS/EOS IDs. The workflow uses the official llama.cpp converter at a pinned commit.

The dedicated smoke workflow must successfully convert a synthetic checkpoint and validate the GGUF header. Runtime compatibility and generated-text quality are separate validation steps. A future subword tokenizer requires a corresponding export/tokenizer migration; byte-tokenizer checkpoints must not be silently reused with a new vocabulary.

## From-scratch requirement

The first checkpoint is initialized randomly. No pretrained language-model checkpoint, embedding matrix, or transferred weights are loaded. Subsequent runs restore only IvritLM's own previous checkpoint. PyTorch is used as a tensor/autograd framework, not as a source of pretrained weights.

## Scale and limitations

The current model is a small CPU-oriented baseline. It validates the training pipeline, not useful language ability. Realistic from-scratch training requires a much larger clean corpus and suitable GPU compute.

## Reproducibility metadata

The checkpoint stores model/training config, seed, corpus hashes, optimizer state, global step, RNG state, and loss history. A signed corpus manifest, full hardware inventory, scheduler state, and evaluation suite remain pending.

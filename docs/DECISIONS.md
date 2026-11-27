# Decision log

This file records durable project decisions. Add new entries rather than silently rewriting history. If a decision is superseded, mark it as superseded and link to the replacement.

## D-001 — Hebrew-first scope

- **Status:** accepted
- **Decision:** The initial model and tokenizer are optimized for Hebrew.
- **Reason:** Keep the first training pipeline focused and measurable.
- **Consequences:** Hebrew-specific data validation and evaluation are required.

## D-002 — Train the base model from scratch

- **Status:** accepted
- **Decision:** Initialize all language-model parameters randomly; do not use pretrained model weights.
- **Reason:** This is a core project requirement.
- **Consequences:** Data volume and compute requirements are substantial. The first model is a small engineering milestone, not a claim of competitive capability.

## D-003 — Decoder-only Transformer

- **Status:** accepted for initial implementation
- **Decision:** Use a causal decoder-only Transformer trained by next-token prediction.
- **Reason:** A straightforward architecture for autoregressive text generation.
- **Consequences:** Causal masking, context length, tokenizer, and checkpoint compatibility must be tested.

## D-004 — GitHub Actions as orchestrator

- **Status:** accepted
- **Decision:** Use Actions for CI, validation, smoke tests, and controlled training orchestration.
- **Reason:** Reproducible automation and visible run history.
- **Consequences:** Do not assume standard hosted runners provide suitable GPU resources. Heavy training requires explicitly provisioned compute.

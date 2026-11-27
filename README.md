# IvritLM

**IvritLM** is an experimental, open-source Hebrew language-model project. The long-term goal is to train a Hebrew-first autoregressive language model **from randomly initialized weights**, with a reproducible and documented training pipeline.

> **Project status: bootstrap / early development.** No trained model is published yet. The repository currently defines the project direction and engineering process; a working model must not be claimed until the smoke tests and training pipeline have passed.

## At a glance

- **Language:** Hebrew-first.
- **Training approach:** from scratch; no pretrained model weights.
- **Architecture direction:** decoder-only Transformer (GPT-style).
- **Framework direction:** PyTorch.
- **Tokenizer direction:** SentencePiece, trained on the project's approved corpus.
- **Automation:** GitHub Actions for validation, data checks, and small CPU smoke tests. Full training requires suitable compute and is not assumed to fit on a standard hosted runner.
- **Distribution goal:** versioned checkpoints and a documented local inference interface, subject to model and dataset licenses.

## Start here

| If you want to… | Read |
|---|---|
| Understand the project and its status | This README |
| Set up a development environment | [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) |
| Understand the planned architecture | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| Understand data requirements and provenance | [docs/DATA_POLICY.md](docs/DATA_POLICY.md) |
| Run or maintain automation | [docs/TRAINING.md](docs/TRAINING.md) |
| Understand tests and quality gates | [docs/TESTING.md](docs/TESTING.md) |
| Track decisions and changes | [CHANGELOG.md](CHANGELOG.md) and [docs/DECISIONS.md](docs/DECISIONS.md) |
| See the planned milestones | [ROADMAP.md](ROADMAP.md) |
| Report a bug or propose an improvement | [CONTRIBUTING.md](CONTRIBUTING.md) |

## Project principles

1. **From-scratch means from-scratch:** initialize model weights randomly. Pretrained weights are not an allowed shortcut for the base model.
2. **Data provenance matters:** every dataset source must have a documented origin, license/permission basis, processing procedure, and exclusion policy.
3. **Reproducibility:** record configuration, tokenizer version, dataset manifest/hash, code revision, random seed, and training environment for every run.
4. **Honest evaluation:** report held-out loss/perplexity and qualitative limitations. Do not describe fluent-looking samples as proof of understanding.
5. **Small verified steps:** CPU tests validate code paths; they do not establish that a model is useful or that large-scale training is feasible.
6. **Documentation is part of the product:** every meaningful behavior, configuration, workflow, and operational change must be documented.

## Repository map

The repository is being built incrementally. Planned areas:

- `.github/workflows/` — automated validation and training workflows.
- `configs/` — version-controlled experiment configurations.
- `data/` — dataset manifests and local/generated artifacts; large or restricted corpora should not be committed.
- `docs/` — operator, architecture, data, and maintenance documentation.
- `ivritlm/` — Python package containing tokenizer, model, training, and inference code.
- `tests/` — unit and integration tests.
- `scripts/` — explicit developer and maintainer commands.

The actual tree is authoritative: planned components are not considered implemented until their code and tests exist.

## Safety, licensing, and limitations

Only use data that the project is legally permitted to process and redistribute (or whose use is otherwise clearly authorized). Do not upload private, personal, confidential, or access-controlled material. Keep dataset manifests and attribution records with the project. See [the data policy](docs/DATA_POLICY.md).

Training from scratch is compute- and data-intensive. GitHub Actions is useful for CI, reproducibility checks, tokenizer/model smoke tests, and small experiments. It is not a promise of free or sufficient GPU compute. See [training operations](docs/TRAINING.md).

## License

The repository's code license will be declared in a dedicated `LICENSE` file. Dataset and model artifacts may have separate terms; a code license does not automatically license training data or resulting weights.

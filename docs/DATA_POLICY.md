# Data policy

Training data quality and lawful provenance are core project requirements.

## Allowed data

A source may be used only after its origin and legal basis have been reviewed and recorded. Examples may include:

- Public-domain material, after verifying the relevant jurisdiction and edition.
- Datasets whose license explicitly permits the intended use.
- Material created by project contributors who have authority to grant the required rights.
- Material provided under a written permission that covers the intended processing and distribution.

A page being publicly accessible does not by itself mean it may be copied, redistributed, or used for model training.

## Required source record

Every source must have a manifest entry containing:

- Dataset/source name and version.
- Original source location or stable identifier.
- Collection date and responsible contributor.
- License or permission basis, including a copy or reference to the terms.
- Allowed and prohibited uses.
- Language and expected content type.
- Processing and normalization steps.
- Deduplication method.
- Exclusion/removal procedure.
- File checksums and dataset split assignment.

Do not add a source to training until this record has been reviewed.

## Privacy and security

Never ingest private messages, personal records, credentials, confidential documents, or access-controlled material without explicit authorization and a documented lawful basis. Remove personal information where feasible and appropriate. Do not commit secrets or raw personal data to Git.

## Quality controls

- Remove exact duplicates and investigate near-duplicates.
- Detect malformed encodings and empty documents.
- Track language and script composition.
- Keep evaluation data isolated from tokenizer training and model training.
- Preserve source-level provenance through processing.
- Maintain a documented removal process for data that must be withdrawn.

## Dataset storage

Git should contain small manifests, scripts, and documentation—not large raw corpora by default. Store data in an access-controlled location appropriate to its license. Record immutable versions and checksums so runs can be reproduced.

## Before adding a dataset

A maintainer must answer: Where did it come from? What license or permission applies? Does that permission cover training and the intended distribution of weights? What personal or sensitive data might it contain? How can it be removed? If any answer is unclear, do not use the source yet.

# Training dashboard

## Purpose

The static dashboard in site/ is designed for GitHub Pages. It dispatches the train.yml workflow and reads recent workflow runs through the GitHub REST API.

## Publishing

The Pages workflow deploys the site/ directory. The expected address is:

https://avtsye.github.io/IvritLM/

GitHub Pages must be enabled once by a repository administrator: open Settings → Pages → Build and deployment → Source, then select GitHub Actions. The current Pages workflow cannot enable Pages automatically because GitHub does not grant the workflow token permission to create the Pages site. After this one-time setting is saved, rerun the Pages workflow. The address becomes active only after a successful deployment.

## GitHub token

A static GitHub Pages site has no private server-side credential store. The dashboard therefore asks the operator for a fine-grained personal access token at runtime.

Create a token limited to this repository with:
- Actions: Read and write.
- Metadata: Read-only (default).

The token is held only in JavaScript memory. It is not saved to localStorage, sessionStorage, cookies, URLs, or repository files. Clear it with the dashboard button or close the tab. Prefer a short expiration. Never paste a classic token with broad account access.

## Accepted source types

- HTTPS only.
- Public GitHub repository URLs in the form https://github.com/owner/repository.
- Public web pages serving HTML or plain text.
- No embedded credentials, private repositories, cookies, or authenticated pages.

The workflow applies download limits, validates redirect destinations, rejects local/private IP destinations, and never executes code from submitted repositories.

## Current behavior and limitations

The dashboard currently triggers **source intake validation only**. The workflow inspects repository/page metadata and publishes a JSON report as an Actions artifact. It does not yet build the training corpus or train model weights. The interface and workflow state this explicitly.

For GitHub repositories, candidate text-file counts and the repository's declared license identifier are reported; the license still requires human review. For web pages, the workflow extracts basic page metadata but does not approve the content for training.

Before any source enters a training corpus, a maintainer must review its license/permission, provenance, quality, and privacy implications, then add an approved dataset manifest. The actual corpus pipeline and from-scratch training engine are separate milestones.

## Troubleshooting

- 401: token invalid or expired.
- 403: verify Actions Read and write access and repository selection.
- 404: verify .github/workflows/train.yml exists on main and the token can access IvritLM.
- No runs immediately: GitHub may take several seconds to register a dispatched run.
- Pages 404: enable Pages with GitHub Actions as the source and verify the Pages deployment workflow.

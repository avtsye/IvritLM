# Changelog

All notable project changes are documented here. Entries describe repository changes, not aspirations. Keep newest entries first and link relevant commits, releases, and migration notes when available.

## Unreleased

### Added
- RTL web dashboard for source intake, GitHub Actions dispatch, and recent run status.
- Source inspection workflow for public GitHub repositories and public HTTPS pages, with bounded downloads and a JSON intake report artifact.
- CI checks for Python compilation and dashboard JavaScript syntax.
- Fine-grained token handling guidance; dashboard token remains in page memory only.

### Fixed
- Pages deployment now documents the one-time repository setting required to enable GitHub Pages.

### Limitations
- Source intake only; corpus construction and actual model-weight training are not implemented yet.
- GitHub Pages requires a one-time administrator setting: Settings → Pages → Source → GitHub Actions.

### Added
- Hebrew RTL training dashboard under site/, with GitHub Actions dispatch and recent-run listing.
- Manual source-intake workflow for public GitHub repositories and public HTTPS pages.
- Bounded source inspection and JSON provenance report artifact.
- Dashboard operations and credential-handling documentation.

### Limitations
- This milestone validates and inspects sources only; it does not yet build a corpus or train model weights.
- GitHub Pages must be enabled in repository settings before the dashboard URL becomes available.

## Previous bootstrap changes

### Added
- Initial project overview and navigation.
- Development, architecture, data policy, training operations, testing, and decision-log documentation.

### Notes
- Repository bootstrap only. No tokenizer, model implementation, trained checkpoint, or operational training workflow is claimed to exist yet.

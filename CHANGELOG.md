# Changelog

All notable project changes are documented here. Entries describe repository changes, not aspirations. Keep newest entries first and link relevant commits, releases, and migration notes when available.

## Unreleased

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

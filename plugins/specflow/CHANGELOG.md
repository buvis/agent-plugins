# Changelog

All notable changes to this plugin are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the plugin uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- **specflow**: package manifest and a placeholder `spec-workflow` skill.
- **specflow**: Claude Code compatibility manifest.
- **specflow**: AWS AI-DLC source record and profile mapping (`references/aws/adaptation.md`).
- **specflow**: license and attribution of the AWS sources, and a provenance section in the README.
- **specflow**: four AWS AI-DLC references, for requirements, design, implementation, and verification, adapted by hand from `awslabs/aidlc-workflows` `v2.11.0`.
- **specflow**: Kiro-compatible templates for requirements, design, tasks, bugfix specs, intake items, spikes, and cross-spec reviews, and the artifact contract reference (`references/artifact-contract.md`).
- **specflow**: versioned JSON schema for the `.specflow.json` spec state.
- **specflow**: approvals bound to a canonical SHA-256 of each artifact, so line endings, whitespace, task checkboxes (including Kiro's `[-]` and `[~]`), and task progress fields never stale an approval; the phase is derived from the files.

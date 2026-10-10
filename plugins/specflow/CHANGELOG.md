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
- **specflow**: a changed artifact stales every approval downstream of it, in both workflow orders, and names the change that caused it.
- **specflow**: reconciliation that refreshes derived hashes and statuses in `.specflow.json`, keeps unknown fields, never writes an approval, and recovers from a missing state file by asking instead of guessing.
- **specflow**: writes stop with a conflict when the file changed after it was read, leaving the other edit in place.
- **specflow**: `scripts/validate_spec.py` with `status`, `validate`, `hash`, `code-baseline`, and `reconcile`; named checks with file, rule, and fix; spec dependencies through `Depends on:`; advisory code-drift warnings; and a versioned JSON status for external runners.
- **specflow**: workspace config in `.agents/specflow.json` (workspace root, specs folder, number-scan folders), refusing absolute, `..`, and out-of-repository paths, and reporting specs left in `.kiro/specs/` or a specs folder that git ignores.

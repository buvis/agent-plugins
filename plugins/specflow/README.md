# specflow

A portable requirements, design, tasks, and implementation workflow that
writes Kiro-compatible spec artifacts.

## Status

Unreleased. The `spec-workflow` skill holds the workflow's entry point, gates,
and shared contracts; its phase references are still being written.

## Package

This folder is the whole distributable package. Maintainer tools, tests, and
skills live outside it and never ship.

## Provenance

specflow's method is adapted by hand from three public AWS AI-DLC
repositories, all MIT-0:

- AWS AI-DLC workflows, `awslabs/aidlc-workflows` (the primary method source)
- AI-powered SDLC patterns with AWS,
  `aws-samples/sample-ai-powered-sdlc-patterns-with-aws` (the original source)
- AI-DLC discovery, `aws-samples/sample-aidlc-discovery`

`skills/spec-workflow/references/aws/adaptation.md` records the commit each
is adopted from, and `references/aws/LICENSE` carries the license of every
source that text is copied from.

## Security

The package ships one optional helper,
`skills/spec-workflow/scripts/validate_spec.py`, a Python 3 standard-library
script. It reads the repository's spec artifacts and runs read-only local
`git` commands (`rev-parse`, `check-ignore`). Its only write is
`.specflow.json` inside a spec folder, through `reconcile`. It refuses paths
outside the repository. The package has no network access, MCP servers, or
authentication.

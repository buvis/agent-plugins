# specflow

A portable requirements, design, tasks, and implementation workflow that
writes Kiro-compatible spec artifacts.

## Status

Unreleased. The `spec-workflow` skill is a shell; the workflow is not written
yet.

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

This package has no scripts, network access, MCP servers, authentication, or
persistent data.

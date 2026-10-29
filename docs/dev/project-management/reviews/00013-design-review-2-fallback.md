# AP00013 design review 2 fallback

Reviewer: isolated native gpt-6.1-sol / high, OpenAI, `/root/design_review_2_fallback`.
Source design-solution outage fallback; external failure retained separately.

- **Blocker — Evidence field mismatch.** The evidence schema has `title`, `evidence`, and nullable `file`; it has no `issue` field. Define exact projection and null-file handling without changing AP00012.
- **Blocker — One-to-one linkage cannot authenticate consensus.** Each evidence finding names one result. A consolidated row can represent reports from multiple reviewers. Define nonempty `finding_ids`, coverage and duplicate-link rules; derive distinct reviewer jobs from validated results instead of trusting caller `found_by`.
- **Question — Facade policy argument is unspecified.** The library supports explicit alternate policies, while the CLI exposes no policy input. Define the default or provide an explicit input.
- **Non-blocker, checked correct — Verification bounds.** Timeout, retained output and disk log limits are explicit; overflow terminates/reaps and prevents reuse. Preserve those tests.

The adopted design records both mandatory fixes. The coordinator also resolves the missing CLI argument with optional `--policy`.

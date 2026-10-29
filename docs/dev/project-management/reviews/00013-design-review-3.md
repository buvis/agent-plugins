# AP00013 final design review

External guarded wrapper: requested Anthropic Sonnet/high, no tools. Exact served model not exposed by the text wrapper.

Review of dispatch 3: verification of the resolved blockers, plus what remains. Cardinal sins: 0. Blockers: 1. Non-blockers: 8. Questions: 3.

## Resolved items, re-checked

- **Verification log cap and timeout bounds (dispatch 1):** holds. *Verification* section: `GATE_LOG_CAP`, the process-group kill on overflow, `output_limit_exceeded` ⇒ `reusable=false`, and a finite `timeout ≤ 1800` with booleans rejected.
- **PRD byte binding (dispatch 1):** holds. *review_stage.py*: exact UTF-8 SHA-256 against `expected_context.source_bindings.prd_sha256` before any write, and the `input_texts` PRD ref must carry the same bytes.
- **Review-close artifact and attribution binding (dispatch 1):** holds. *review_close.py*: exactly one `review-file` artifact whose path equals `review_ref`, hash-checked, and every evidence finding linked exactly once.
- **Title→issue projection and many-to-one `finding_ids` (dispatch 2):** holds mechanically. See the non-blockers below for two side effects.
- **`--policy` on the facade (dispatch 2):** holds. It is consistent with the v1-alt fixture rule in *review_evidence.py*.

## Findings

```json
{
  "severity": "blocker",
  "title": "Facade and library outputs have no versioning strategy",
  "evidence": "Only the verification artifact carries schema_version=1. The outputs of --stage-review, --check-evidence, --prepare-close (task_proposals, decision_proposals, rubric_verdicts, reviewer_results) and --catchup-probe, plus their request JSON, carry no version. The Review-close section's own text says a later controller consumes these proposals. The check-evidence return `checks: \"local-contract\"` is unversioned too.",
  "suggested_fix": "Add `schema_version: 1` to every facade JSON output and request object. Make unknown or higher versions a usage error (exit 2). Have --list-capabilities report the version per operation. This is one sentence in Interfaces & contracts and a field in each return shape."
}
```

```json
{
  "severity": "non-blocker",
  "title": "Consensus guard is nearly unsatisfiable because grouping requires identical normalized titles",
  "evidence": "review_close.py: a linked finding must match the row's normalized severity/file/issue, and 'Different normalized titles remain separate rows'. found_by is derived only from findings linked to one row. LLM reviewers rarely produce the same title and the same severity. Decision-gate medium/low fixes and every tail-sweep row need two distinct finders, so they will refuse almost always. Differing severities on the same issue are not addressed at all.",
  "suggested_fix": "Record this as a known ceiling. Optionally allow a row to link findings with the same file and differing severity or title when the row's severity is the maximum of the links. Alternatively, say explicitly that two-voice paths are expected to rarely pass until the controller supplies consolidation."
}
```

```json
{
  "severity": "non-blocker",
  "title": "Title→issue normalization pipeline is not pinned to the table parser's",
  "evidence": "findings.py defines strip_lead (inline-code, link, checkbox and symbol leads) and finding_key. review_close.py says 'Normalize severity/file/title through finding_key' but not whether strip_lead and escaped-pipe handling apply to the evidence title. A title like \"`foo()` leaks…\" or one containing `|` would key differently from the same text in the parsed table and refuse legitimate evidence.",
  "suggested_fix": "State that the evidence title passes through the same function chain as the table issue cell. Add a fixture with code-span, leading-symbol and pipe-containing titles."
}
```

```json
{
  "severity": "non-blocker",
  "title": "Refusal result shapes and exit codes are undefined for several paths",
  "evidence": "(a) Tail-sweep ordered refusals (carry, missing receipt, empty, above medium, single voice, duplicate deferral) have no error token or exit code. (b) 'Missing snapshot … returns controller-required' happens after the request is read and evidence is evaluated, but Common boundary says controller-required refuses 'before request-file reads', and the `operation` value is unspecified. (c) check_evidence rejects booleans, unknown fields and so on, but Common boundary says shape errors raise ValueError, while the return contract says `invalid-evidence` with defects. 'Not invalid-policy' implies a token that the return contract and exit table never define.",
  "suggested_fix": "Add one table: condition → JSON error token → exit code. Separate lifecycle controller-required (pre-read) from snapshot-missing controller-required (post-read, with its own `operation`). Decide whether schema-shape violations on evidence become defect strings (exit 1) or ValueError (exit 2), and define invalid-policy."
}
```

```json
{
  "severity": "non-blocker",
  "title": "Staging input-reference representation and verification artifact root remain unpinned (retained from dispatch 1)",
  "evidence": "stage_review.input_texts is dict[str,str], yet 'declared explicit reference' and 'repo-tree refs must name tree_sha' have no stated encoding. run_verification has project_root but no artifact_root, so the Common boundary rule 'escape from the explicit artifact root' is vacuous for --artifact/--log. These are load-bearing for Blake's isolation (task 4) and for safe I/O (task 9).",
  "suggested_fix": "Either input_texts values are strings and a repo-tree ref's value is the 40-hex tree SHA, or add a typed `input_refs` map. For verification, require artifact and log under project_root (or add an `artifact_root` parameter) and say which."
}
```

```json
{
  "severity": "non-blocker",
  "title": "Staging writes are TOCTOU-exposed while the design claims symlink refusal",
  "evidence": "Common boundary promises refusal of 'symlink components below the supplied root'. The Review log retains that only verification mandates descriptor-relative O_NOFOLLOW writes. stage_review writes about 7 files. Overwrite versus exclusive create on a reused cycle_id, and partial-write cleanup, are unspecified.",
  "suggested_fix": "The no-follow, exclusive-leaf writer is already being ported for verification, so make it the single artifact writer for stage-review and --export-policy --out too. State exclusive creation and a unlink-on-failure rule for partially staged sets."
}
```

```json
{
  "severity": "non-blocker",
  "title": "Boundary test guard cannot see all reads, and git over the worktree reads the live state dir",
  "evidence": "Test strategy: 'guard opens and subprocesses'. Monkeypatching open misses os.open with dir_fd and child git reads. Separately, the dirty_tree and verification checks run git status/diff across project_root, which stats the autopilot store, against 'No helper reads … live autopilot state directory'.",
  "suggested_fix": "Use sys.addaudithook ('open', 'subprocess.Popen') plus chmod 000 poison files, which also stop child git. Define 'read' as content access by helper code. Allow pathspec-excluded git metadata operations and test them separately."
}
```

```json
{
  "severity": "non-blocker",
  "title": "Input size and git-subprocess bounds are missing outside verification",
  "evidence": "JSON requests, review_text, diff_text and policy are read unbounded. classify_findings, dirty_tree and the reuse checks run git with no stated timeout, unlike capture_range (30s) and catchup (15s). This is the same class as the dispatch-1 cardinal sin, but it is operator-invoked and local with no service exposure, so it is not escalated.",
  "suggested_fix": "Set one max-bytes constant for all JSON and text inputs and a timeout for every git call. Map overruns to exit 2."
}
```

```json
{
  "severity": "non-blocker",
  "title": "cap classify_findings returns [] for 'not evaluated'",
  "evidence": "cap_check.py: 'Missing previous head returns []'. A caller cannot tell 'no regressions' from 'skipped', which violates fail-loud for a gate input.",
  "suggested_fix": "Return an explicit marker such as `{\"evaluated\": false}` in the facade or controller proposal, or document that callers must check the head themselves."
}
```

```json
{
  "severity": "non-blocker",
  "title": "Portability: POSIX-only verification in a portable plugin",
  "evidence": "Verification relies on O_NOFOLLOW, dir_fd, process groups and inode identity, the 'pinned Unix source'. Repo invariants target portable Agent Plugins, and capabilities advertise 'implemented helpers only'.",
  "suggested_fix": "Add a platform guard returning a clear usage-style error on Windows, and have --list-capabilities report verify as POSIX-only."
}
```

```json
{
  "severity": "question",
  "title": "Carry matching and snapshot field semantics",
  "evidence": "review_close.py: 'one unfinished task with matching carry_refs, carry_cycle' and 'requires one task satisfy all conditions'. It is unclear whether two matching tasks pass or refuse, what carry_cycle must equal, and which `status` strings count as unfinished. Likewise `chosen_findings` versus 'every evidence finding appears in exactly one row's links' leaves open whether verify/discard rows in the table carry finding_ids.",
  "suggested_fix": "State at-least-one versus exactly-one, `carry_cycle == cycle` (or whatever the source uses), and the status enum. Say that table rows classified verify/discard still carry finding_ids, and only off-table bookkeeping rows do not."
}
```

```json
{
  "severity": "question",
  "title": "Source-map edit versus digests and concurrent PRDs",
  "evidence": "Risks section adds top-level `helper_dispositions` to a 13.66MB map shared with AP00018–21 and promises 'preserve … digest fields'. If any consumer hashes the whole file, adding a key breaks that digest. Parallel edits to one large file conflict.",
  "suggested_fix": "Confirm no whole-file digest exists. If one does, store dispositions in a sibling file such as `tools/autopilot/helper-dispositions.json`."
}
```

```json
{
  "severity": "question",
  "title": "Verification return carries no command output; purpose of GATE_OUTPUT_CAP unstated",
  "evidence": "The PRD output is 'Actual command output'. The return is `{ok, artifact, controller_required}`, the facade emits one JSON value, and output goes only to the log. The 2MB retained stdout is used for summary parsing, but this is not stated.",
  "suggested_fix": "State that stdout/stderr live only in the log (hash in the artifact) and that the 2MB tail exists for the summary parse."
}
```

## Checked correct

- **Common boundary and the cardinal-sin tally:** helpers hold no persistent state and write only regenerable local reports, so rollback is deleting those files. There are no credentials in the design. Exit codes plus a single JSON value are enough observability for a local CLI, and the controller owns production operation.
- **Evidence independence (*review_evidence.py* and *review_stage.py*):** `expected_context` is never derived from submitted evidence, clean completed results satisfy completion, missing or failed results do not, and AP00012's `accepted` token is never emitted.
- **Blind-input isolation (*review_stage.py*):** the raw PRD stays authoritative, and Blake's allowlist covers paths as well as text. Single-pass template substitution prevents token re-expansion.
- **Fix proposals (*review_close.py*):** `action=fix-proposed` rather than `auto-fixed` removes the source's premature claim. No applied-review-batch stamp or dispatch-end call is emitted.

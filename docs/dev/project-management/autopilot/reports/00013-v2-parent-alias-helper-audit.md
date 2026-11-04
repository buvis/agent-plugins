# AP 00013 v2: unresolved helper parent-alias finding

The read-only coordinator audit confirmed a helper-level contract defect at source commit `eb770e31348df5c4b669e3f8ba391ca25526d901`. `_pinned_parent_fd` resolves the whole parent when the supplied root uses another spelling. This removes below-root symlink components before its `O_NOFOLLOW` descent. The same-spelling case refuses the link; the mixed-spelling case opens its target directory. `_open_log_sink(..., preserve=True)` then returns the internal sentinel descriptor. Explicit caller truncation and writing changed the scratch sentinel. Both ordinary-directory controls open the intended directory.

Evidence: `00013-v2-parent-alias-helper-probe.py.txt` and `00013-v2-parent-alias-helper-evidence.json`. The original command exited 0. The probe used plain scratch directories, no Git repositories, no verification child, and no tracked files. Its fixture directory must be new for a rerun. Source files were read from the pinned commit into `docs/dev/tmp/ap13-parent-alias-audit-eb770e3/helper_only_source`; the JSON records their hashes.

At HEAD `3bb1403`, a diff against the pinned source changes only `_symlinked_component`, not `_pinned_parent_fd`, `_descend`, or `_open_log_sink`; the helper finding remains applicable by source inspection. No new runtime execution against that HEAD is claimed.

## Limits and disposition

This does NOT prove a full `run_verification` bypass, a tracked-file overwrite, or an outside-root write. Static verification preflight may reject the path before acquisition. The attempted full-runtime disposable Git clone failed at `.git/hooks` with an OS permission denial, including the required escalated retry. No further clone attempt was made. That larger hypothesis remains UNVERIFIED; the helper-only experiment neither creates repositories nor executes the denied operation.

Task 5 is complete and its Tess and MEDIUM Pat budgets are exhausted. Do not reopen it, reset counters, dispatch a third Pat, or hide this finding in tasks 6–8. Continue those existing tasks, retaining this unresolved evidence and the limits above in task 8's delivery report and the completion handoff. The mandatory fresh cycle-2 gate must adjudicate the remaining contract defect and any demonstrated runtime consequences under the existing cap policy. No clean delivery or defect-closure claim is authorized by the scoped green tests.

Keep this audit and every earlier review/ruling out of Blake's PRD-only input. Alice/Bob/Carl/Eve and the coordinator may use it under their normal context contracts. This is a focused implementation audit, not a substitute for any required review lens.

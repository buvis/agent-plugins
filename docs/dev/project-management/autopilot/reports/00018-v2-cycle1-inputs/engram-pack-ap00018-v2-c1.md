Portfolio freshness: NOT refreshed this cycle (PRD 00002 pending)

269 changed symbol(s) omitted (beyond the 40-symbol cap).

## Similar code

- agent-plugins:/Users/bob/git/src/github.com/buvis/agent-plugins/plugins/autopilot/controller/autopilot_state/schema.py:43-68
  def _check_json(value: object, depth: int = 0) -> None:
    if isinstance(value, str):
        if _string_size(value) > MAX_STRING_BYTES:
            raise ResourceLimitError("JSON string exceeds the byte limit")
    elif value is None or isinstance(value, bool):
        return
    elif isinstance(value, int):
        if abs(value) >= 10**MAX_JSON_INTEGER_DIGITS:
            raise ResourceLimitError("JSON integer exceeds the digit limit")
    elif isinstance(value, float):
        if not math.isfinite(value):
            raise SchemaError("JSON numbers must be finite")
    elif isinstance(value, (dict, list)):
        if depth >= MAX_JSON_DEPTH:
            raise ResourceLimitError("JSON exceeds the nesting limit")
        if isinstance(value, dict):
            for key, item in value.items():
                if not isinstance(key, str):
                    raise SchemaError("JSON object keys must be strings")
                _check_json(key, depth + 1)
                _check_json(item, depth + 1)
        else:
            for item in value:
                _check_json(item, depth + 1)
    else:
        raise SchemaError("Value is not JSON data")

- agent-plugins:/Users/bob/git/src/github.com/buvis/agent-plugins/plugins/autopilot/controller/autopilot_state/schema.py:76-105
  def decode_json(text: str, *, source: str) -> object:
    """Decode a complete JSON document without duplicate keys or excess resources."""
    if not isinstance(text, str):
        raise SchemaError(f"{source}: expected JSON text")
    if _string_size(text) > MAX_STATE_BYTES:
        raise ResourceLimitError(f"{source}: JSON document exceeds the byte limit")

    def object_pairs(pairs: list[tuple[str, object]]) -> dict:
        result = {}
        for key, value in pairs:
            if key in result:
                raise SchemaError(f"{source}: duplicate object key")
            result[key] = value
        return result

    def parse_integer(value: str) -> int:
        if len(value.lstrip("-")) > MAX_JSON_INTEGER_DIGITS:
            raise ResourceLimitError(f"{source}: JSON integer exceeds the digit limit")
        return int(value)

    def reject_constant(value: str) -> object:
        raise SchemaError(f"{source}: invalid JSON number {value}")

    try:
        value = json.loads(text, object_pairs_hook=object_pairs,
                           parse_int=parse_integer, parse_constant=reject_constant)
    except (json.JSONDecodeError, RecursionError) as error:
        raise SchemaError(f"{source}: invalid JSON document") from error
    _check_json(value)
    return value

- agent-plugins:/Users/bob/git/src/github.com/buvis/agent-plugins/tests/autopilot/test_local_boundary.py:167-169
  def one_json(proc: subprocess.CompletedProcess) -> Any:
    """json.loads rejects trailing data, so this proves exactly one JSON value."""
    return json.loads(proc.stdout.decode("utf-8"))

- agent-plugins:/Users/bob/git/src/github.com/buvis/agent-plugins/plugins/specflow/skills/spec-workflow/scripts/specflow_helper/schema.py:74-76
  def same(a: object, b: object) -> bool:
    """JSON equality: 1 and true differ."""
    return json_type(a) == json_type(b) and a == b

- agent-plugins:/Users/bob/git/src/github.com/buvis/agent-plugins/tests/autopilot/test_sessions.py:154-156
      def setUp(self) -> None:
        self.policy = json.loads((CONTRACTS / "review-policy-v1.json").read_text())
        self.hosts_declared = json.loads((CONTRACTS / "hosts.json").read_text())["hosts"]

- agent-plugins:/Users/bob/git/src/github.com/buvis/agent-plugins/plugins/autopilot/scripts/autopilot.py:295-317
  def _write_policy(out: Path, output: bytes) -> None:
    """Inspect the opened inode before truncating; aliases cannot redirect a
    write. Opens nonblocking so a FIFO with no reader refuses instead of
    hanging; refuses up front on a platform without O_NOFOLLOW rather than
    crashing on the attribute lookup."""
    if not hasattr(os, "O_NOFOLLOW"):
        raise ValueError(f"{out}: platform has no O_NOFOLLOW support")
    flags = os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK
    try:
        fd = os.open(out, flags, 0o666)
    except OSError as error:
        if error.errno == errno.ENXIO:
            raise ValueError(f"{out} has no reader (FIFO)") from error
        raise
    with os.fdopen(fd, "wb") as sink:
        # `fd` is owned by `sink` from here on: any exception below, including
        # one from set_blocking itself, still closes it via this `with` block.
        os.set_blocking(sink.fileno(), True)
        info = os.fstat(sink.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise ValueError(f"{out} must be a regular file with one hard link")
        os.ftruncate(sink.fileno(), 0)
        sink.write(output)

## Reuse precedent

- home:/Users/bob/git/src/github.com/buvis/home/.config/autocodex/test_roles.py:32-40
  def test_host_contract_uses_resolved_roles(tmp_path: Path) -> None:
    env = {"AUTOCODEX_OPUS_MODEL": "gpt-6-astra", "AUTOCODEX_OPUS_EFFORT": "high"}
    prompt = driver.host_prompt(tmp_path, tmp_path, "build", env=env)
    assert "opus = gpt-6-astra / high" in prompt
    assert "sonnet = gpt-6.1-sol / medium" in prompt
    assert "haiku = gpt-6-luna / low" in prompt
    assert "gpt-5.6-" not in prompt
    assert "{ROLE_MAPPING}" not in prompt
    assert "gpt-6.1-sol / high" in prompt

- agent-skills:/Users/bob/git/src/github.com/buvis/agent-skills/skills/use-qwen/scripts/eval_harness_evidence_helpers.py:277-279
  def _touch_json(path: Path) -> None:
    """Rewrite a JSON file with the same content and different bytes."""
    path.write_text(json.dumps(_read_json(path), indent=4), encoding="utf-8")

- agent-skills:/Users/bob/git/src/github.com/buvis/agent-skills/skills/glean/scripts/glean.py:52-58
  def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as e:
        sys.exit(f"glean: {path} is not valid JSON: {e}")

- claude-autopilot:/Users/bob/git/src/github.com/buvis/claude-autopilot/skills/run-autopilot/cli/test_custody_stall.py:123-124
      def _marker_path(self) -> Path:
        return self.autopilot_dir / "critical-on-master"

- claude-autopilot:/Users/bob/git/src/github.com/buvis/claude-autopilot/skills/run-autopilot/cli/test_custody_stall.py:576-619
      def test_exit_9_when_ledger_is_a_file_then_the_retry_completes_idempotently(
        self,
    ) -> None:
        self._put_in_wip(content=PRD_TEXT)
        self._write_state(
            self._critical_state(deferred_decisions=copy.deepcopy(DECISIONS)),
        )
        before = self._state()
        (self.autopilot_dir / "ledger").write_text("occupied", encoding="utf-8")

        rc = self._do_stall(site="cap_critical")

        self.assertEqual(rc, 9)
        self.assertTrue(self._in_hold())
        self.assertFalse(self._in_wip())
        op_id = self._assert_intent_retained_without_reset(before)
        self.assertEqual(
            self.notify.call_count,
            0,
            "no notification before every custody write succeeded",
        )

        (self.autopilot_dir / "ledger").unlink()
        rc = self._do_stall(site="cap_critical")

        self.assertEqual(rc, 0)
        entry = self._stall_entry(op_id)
        self.assertEqual(self._marker_entries(), [entry])
        self.assertEqual(custody.unresolved_from_journal(self.autopilot_dir), [entry])
        self.assertEqual(
            sorted(i["op_id"] for i in self._deferred_items()),
            sorted([op_id, f"{op_id}-dd0", f"{op_id}-dd2", f"{op_id}-dd3"]),
            "one stall record plus one migration record per pending deferral, no duplicates",
        )
        self.assertEqual(self._hold_text(), self._expected_hold(op_id))
        self.assertEqual(
            self.notify.call_count,
            1,
            "the notification fires exactly once across both attempts",
        )
        final = self._state()
        self.assertNotIn("stall_op", final)
        self.assertEqual(final["batch"]["critical_on_master"], [entry])
        self.assertEqual(final["cycle"], 1)

- claude-autopilot:/Users/bob/git/src/github.com/buvis/claude-autopilot/skills/run-autopilot/cli/test_routing_rework.py:80-84
  def test_rework_resume_with_all_tasks_completed_routes_opus(tmp_path):
    # A stale list left by a crash before phase-done is a fresh review.
    tasks = [{"id": "5", "status": "completed", "model": "sonnet"}]
    ap_dir = _rework_box(tmp_path, tasks, ["5", "9"])
    assert route("review", ap_dir, env={}).model == OPUS

## Findings precedent

- findings:/Users/bob/git/src/github.com/buvis/agent-plugins/docs/dev/project-management/reviews/00004-artifact-state-contract-review-01.md
  4. Accept: rely on the agent never recording such an approval (WF-002.7 is agent behaviour). Benefit: no change. Drawback: no tool backstop.

- findings:/Users/bob/git/src/github.com/buvis/agent-plugins/docs/dev/project-management/reviews/00004-artifact-state-contract-review-01.md
  - **If unchanged:** valid Markdown blocks the tasks phase, and the agent may "fix" correct text.

- findings:/Users/bob/git/src/github.com/buvis/agent-plugins/docs/dev/project-management/reviews/00004-artifact-state-contract-review-01.md
  - **Options:** (1, **Recommended**) Reword STATE-003.4 to "the helper writes no approval; it may compute the values the agent records". S. Against: it touches approved requirements. (2) Drop `approvedAt` and `workflowVersion` from `hash --json`. S; the agent then assembles more. (3) Accept as is.

- findings:/Users/bob/git/src/github.com/buvis/agent-plugins/docs/dev/project-management/reviews/00006-runtime-skill-review-01.md
  - Bob: ✅ Available (codex, after one retry (inlined)). His first run refused for lack of input, as in every 00004 and 00005 cycle: his `cat` of the context file was blocked by the Fact-Forcing Gate PreToolUse hook, and his own line cites `sandbox_apply: Operation not permitted`. The output had one `[BOB] ⚪ Cannot verify review criteria` line and every `R{n}` set to fail. That is the refusal shape in substance, though not the literal `Cannot statically verify` pattern, so the one retry used the inlined prompt (773 KB: context, diff, and the persona with the two edits). The first output is kept at `docs/dev/tmp/bob-output-00006c1-first.txt`. His retry put a `- ` bullet before each `[BOB]` line, so consolidation read a stripped copy (`bob-output-00006c1-lines.txt`). The `codex_thread_id` above belongs to the retry.

- findings:/Users/bob/git/src/github.com/buvis/agent-plugins/docs/dev/project-management/reviews/00012-autopilot-package-contract-v1-review-01.md
  # Review: 00012-autopilot-package-contract-v1

- findings:/Users/bob/git/src/github.com/buvis/agent-plugins/docs/dev/project-management/reviews/00012-autopilot-package-contract-v1-review-01.md
  | R2 | [1/3] | 🟠 | resource_closure leaves out many runtime script dependencies. `resource_edges` has 202 rows, yet packaged skills call scripts that are neither packaged nor declared external: `consolidate_findings.py` (plugins/autopilot/skills/run-autopilot/references/lane-solo.md:168, plugins/autopilot/skills/review-work-completion/SKILL.md:386), `compute_mech_facts.py` (plugins/autopilot/skills/fast-track/SKILL.md:270), and also `render_prompt.py`/`record_dispatch.py` in fast-track, `detect_tautological_tests.py`, `check_review_file.py`, `await_reviewer_outputs.py`, `fast_track_plan.py`, `card.py`, `fablectl.py` and `parse_review.py`. The test locks the edge count and digest (tests/autopilot/test_package.py:331), so it cannot catch the gap. The unconditional skill gates block runtime harm today, but later PRDs that restore entry points will inherit this incomplete map | tools/autopilot/source-map.json | Phase 1 task 2 | BLAKE |

- findings:/Users/bob/git/src/github.com/buvis/agent-plugins/docs/dev/project-management/reviews/00012-autopilot-package-contract-v1-review-01.md
  Verified: `uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot -q` gave 89 passed, 0 skipped. `python3 scripts/validate.py` reported "Validated 3 plugin package(s) and 15 skill(s)". `python3 tools/autopilot/check-source.py --source-root ../claude-autopilot` passed: 679 files, 92 assets, 1381 behaviors, 4950 regression cases. The policy lanes, rosters, escalation rules and rubric sets match the design tables, and the fixture file has all 55 named cases.

## Task prose

### Batch 202610250001
- [x] 00012-autopilot-package-contract-v1.md (2 cycles; 47/47 tasks)
- [x] 00013-autopilot-session-helpers-v3.md (2 cycles; 11/11 tasks; the one user-authorized bounded recovery; T1 R1 root-anchored symlink refusal, T2 R3 descriptor-bound failed-artifact invalidation, T3 git-probe timeout fail-closed, T4 delivery evidence. Dispositions: `reports/00013-v3-admission.md`; audit: `reviews/00013-autopilot-session-helpers-v3-audit.md`)
- [ ] 00013 v1 and v2: hold (exhausted caps, cap_regression); superseded by v3's completed fresh full review. v2 cycle-2 review `reviews/00013-autopilot-session-helpers-v2-review-2.md`, stubs 00034-00037.
- [ ] 00014-autopilot-host-execution-v1.md
- [ ] 00015-autopilot-workflow-parity-v1.md
- [ ] 00016-autopilot-controller-integration-v1.md
- [ ] 00017-autopilot-profile-conformance-v1.md
- [ ] 00018-autopilot-controller-kernel-v1.md (hold: replan budget 40K below 55K estimator overhead; tasks 1-6 + task 7 tests committed; do not resume t

---
default_model: opus
model_tier_rationale: Extraction equivalence, public contracts and concurrent workflow authority require judgment.
lane: full
rework_cap: 3
plan_expansion: allow
eligibility: ls docs/dev/project-management/prds/done/00012-* # link-ok: lifecycle output
---
# Autopilot canonical controller kernel and protocol

Source: [three-layer design](../../designs/00011-autopilot-standalone-design.md). Recovery revision authorized 2026-11-09 by the request to finish portable Autopilot. Supersedes the held v1 for delivery, preserving v1 and its attempt evidence. No publication, live installation, source retirement or custody acceptance.

## Overview

### Problem Statement
Standalone and supervised workflows need the same enforceable writer. The current tested writer lives inside OVCAQ; adding a second legacy backend would split authority.

The v1 attempt stopped during task 7 after prompt-size/replan exhaustion; tasks 1–6 and task-7 tests already landed. Reuse those implemen

# AP 00013 v2 cycle 2 evidence archive

The five reviewer outputs are copied without editing from the fresh completion review. `models.json` distinguishes served model IDs from configured effort. `sha256.json` binds the copied artifacts.

Review HEAD: `69ebc4b87a816020e398a05809b37d07cd290b1f`. Review gate: 19 failed, 1091 passed in 279.28s. All 19 failures are the known AP18 controller nodes.

The native review session omitted the prescribed `autopilot verify` fallback after review-stage could not parse the pytest summary. The closeout coordinator ran that exact fallback after the session exited, at `a20b31aa5eec2ff0eca8cf9a9cab9c41540a94d1`:

```
python3 /Users/bob/.claude/plugins/cache/buvis-plugins/autopilot/0.10.0/skills/run-autopilot/cli/__main__.py verify --gate-command 'uv run --no-project --python 3.12 --with-requirements tools/autopilot/requirements-test.txt python -m pytest tests/autopilot -q' --repo-root /Users/bob/git/src/github.com/buvis/agent-plugins --cycle 2 --log docs/dev/tmp/gate-00013v2-c2-fallback.log
```

Exit 1; raw pytest summary: **19 failed, 1091 passed in 269.86s**. The wrapper returned counts null, `recorded: false`, `raw_line: null`, `dirty: false`, `head_moved: false`, `timed_out: false`. No verification record was fabricated. The named fallback invocation is now complete; the parser defect and red controller suite remain. `git diff --stat 69ebc4b..a20b31a -- plugins tests tools scripts .github` returned no output, establishing unchanged product, test, tooling and CI bytes. This verification supplement is not a new review cycle and does not reopen the exhausted cap.

Alice's probe scripts and exact command/result pairs come from her isolated review transcript. The coordinator copied them without rerunning them. They require a fresh initialized scratch Git repository at `<argument>/repo`; their absolute source import reflects the original host. The runtime probe accepts the symlinked path under the aliased root; the tracked-file control refuses both spellings and preserves README bytes. These observations do not demonstrate an outside-root or tracked-file overwrite.

The canonical consolidated review is `reviews/00013-autopilot-session-helpers-v2-review-2.md`. Its two HIGH findings caused `cap_regression` hold at cycle 2/2. The raw table includes duplicate descriptions and lower-severity scope claims; the archive does not assert every row is a distinct confirmed defect. The historical task/attempt state remains recoverable at review HEAD. No v3, counter reset, additional repair or publication is authorized by this archive.

# Autopilot documented surface inventory

Companion to [the feasibility assessment](00011-autopilot-agent-plugins-port.md). Source pin: `e960ef1cc43e72bf92593b2f16c7a37c71ea7e48` (2026-10-24).

The [three-layer design](../designs/00011-autopilot-standalone-design.md) assigns workflow state/lifecycle/lanes/review acceptance/record commits to Autopilot's single controller, session/process/collaboration mechanics and operations API to OVCAQ, and presentation to Lantern (working name). Standalone uses that same controller without OVCAQ. Rows below preserve source observations and obligations; earlier OVCAQ owner labels are interpreted through this revised allocation. Client-specific hooks still require supported registration and execution evidence.

The documentation pass covered README, all eleven SKILL.md files, their immediate reference Markdown files, and the Tracon README before implementation inspection. Runtime `--help` supplied the public Autopilot CLI surface. Source-code findings are separately marked in the assessment.

Every row below is **redesign**, with **code-only: no**: it records an existing documented interface or procedure that must be re-expressed against the new runtime. This does not authorize deleting its behavior. The assessment separately identifies content and algorithms that port unchanged. Section rows include the complete linked section, including its conditions, defaults, failures and examples. Supporting-tool flags are inventoried as dependencies, not claimed as top-level Autopilot options.

AP 00012 freezes these source IDs independently of the destination map. Each row
must map to a delivery repository/PRD, target procedure/operation, observable
acceptance scenario and profile-specific evidence. Configuration/state fields
and source regression cases receive explicit additional rows. Shared tests may
cover several obligations; preserved headings or unavailable status alone never
prove a retained behavior. The corrected AP 00012 design defines this contract.

## Public CLI commands and flags

The scan found 31 top-level verbs and 45 help surfaces including the root and nested commands. `render audit/report/metrics` are value choices, not further nested parsers.

| Row | Command or flag | Reason |
| --- | --- | --- |
| CLI-001 | `autopilot` | R12: translate to the owned OVCAQ or plugin command; preserve documented semantics. |
| CLI-002 | `autopilot -h, --help` | Preserve this option’s meaning in that command’s replacement. |
| CLI-003 | `autopilot init` | R12: translate to the owned OVCAQ or plugin command; preserve documented semantics. |
| CLI-004 | `autopilot init -h, --help` | Preserve this option’s meaning in that command’s replacement. |
| CLI-005 | `autopilot init --state STATE` | Preserve this option’s meaning in that command’s replacement. |
| CLI-006 | `autopilot init --prd PRD` | Preserve this option’s meaning in that command’s replacement. |
| CLI-007 | `autopilot enter` | R12: translate to the owned OVCAQ or plugin command; preserve documented semantics. |
| CLI-008 | `autopilot enter -h, --help` | Preserve this option’s meaning in that command’s replacement. |
| CLI-009 | `autopilot enter --state STATE` | Preserve this option’s meaning in that command’s replacement. |
| CLI-010 | `autopilot enter --prd PRD` | Preserve this option’s meaning in that command’s replacement. |
| CLI-011 | `autopilot enter --prds PRDS` | Preserve this option’s meaning in that command’s replacement. |
| CLI-012 | `autopilot stall` | R12: translate to the owned OVCAQ or plugin command; preserve documented semantics. |
| CLI-013 | `autopilot stall -h, --help` | Preserve this option’s meaning in that command’s replacement. |
| CLI-014 | `autopilot stall --state STATE` | Preserve this option’s meaning in that command’s replacement. |
| CLI-015 | `autopilot stall --prd PRD` | Preserve this option’s meaning in that command’s replacement. |
| CLI-016 | `autopilot stall --site SITE` | Preserve this option’s meaning in that command’s replacement. |
| CLI-017 | `autopilot stall --detail DETAIL` | Preserve this option’s meaning in that command’s replacement. |
| CLI-018 | `autopilot stall --prds PRDS` | Preserve this option’s meaning in that command’s replacement. |
| CLI-019 | `autopilot park` | R12: translate to the owned OVCAQ or plugin command; preserve documented semantics. |
| CLI-020 | `autopilot park -h, --help` | Preserve this option’s meaning in that command’s replacement. |
| CLI-021 | `autopilot park --state STATE` | Preserve this option’s meaning in that command’s replacement. |
| CLI-022 | `autopilot park --prds PRDS` | Preserve this option’s meaning in that command’s replacement. |
| CLI-023 | `autopilot park --autopilot-dir AUTOPILOT_DIR` | Preserve this option’s meaning in that command’s replacement. |
| CLI-024 | `autopilot reset-prd` | R12: translate to the owned OVCAQ or plugin command; preserve documented semantics. |
| CLI-025 | `autopilot reset-prd -h, --help` | Preserve this option’s meaning in that command’s replacement. |
| CLI-026 | `autopilot reset-prd --state STATE` | Preserve this option’s meaning in that command’s replacement. |
| CLI-027 | `autopilot defer` | R12: translate to the owned OVCAQ or plugin command; preserve documented semantics. |
| CLI-028 | `autopilot defer -h, --help` | Preserve this option’s meaning in that command’s replacement. |
| CLI-029 | `autopilot defer --state STATE` | Preserve this option’s meaning in that command’s replacement. |
| CLI-030 | `autopilot defer --prd PRD` | Preserve this option’s meaning in that command’s replacement. |
| CLI-031 | `autopilot defer --batch BATCH` | Preserve this option’s meaning in that command’s replacement. |
| CLI-032 | `autopilot defer --json JSON` | Preserve this option’s meaning in that command’s replacement. |
| CLI-033 | `autopilot restore` | R12: translate to the owned OVCAQ or plugin command; preserve documented semantics. |
| CLI-034 | `autopilot restore -h, --help` | Preserve this option’s meaning in that command’s replacement. |
| CLI-035 | `autopilot restore --state STATE` | Preserve this option’s meaning in that command’s replacement. |
| CLI-036 | `autopilot check-plan` | R12: translate to the owned OVCAQ or plugin command; preserve documented semantics. |
| CLI-037 | `autopilot check-plan -h, --help` | Preserve this option’s meaning in that command’s replacement. |
| CLI-038 | `autopilot check-plan --state STATE` | Preserve this option’s meaning in that command’s replacement. |
| CLI-039 | `autopilot check-plan --prd PRD` | Preserve this option’s meaning in that command’s replacement. |
| CLI-040 | `autopilot check-plan --ceiling CEILING` | Preserve this option’s meaning in that command’s replacement. |
| CLI-041 | `autopilot select` | R12: translate to the owned OVCAQ or plugin command; preserve documented semantics. |
| CLI-042 | `autopilot select -h, --help` | Preserve this option’s meaning in that command’s replacement. |
| CLI-043 | `autopilot select --prds PRDS` | Preserve this option’s meaning in that command’s replacement. |
| CLI-044 | `autopilot frontmatter` | R12: translate to the owned OVCAQ or plugin command; preserve documented semantics. |
| CLI-045 | `autopilot frontmatter -h, --help` | Preserve this option’s meaning in that command’s replacement. |
| CLI-046 | `autopilot frontmatter --state STATE` | Preserve this option’s meaning in that command’s replacement. |
| CLI-047 | `autopilot frontmatter --prd PRD` | Preserve this option’s meaning in that command’s replacement. |
| CLI-048 | `autopilot lane-check` | R11: preserve code-owned escalation and lane routing. |
| CLI-049 | `autopilot lane-check -h, --help` | Preserve this option’s meaning in that command’s replacement. |
| CLI-050 | `autopilot lane-check --state STATE` | Preserve this option’s meaning in that command’s replacement. |
| CLI-051 | `autopilot lane-check --signal {critical_finding,high_unresolved,suite_red,review_failed}` | Preserve this option’s meaning in that command’s replacement. |
| CLI-052 | `autopilot phase-done` | R12: translate to the owned OVCAQ or plugin command; preserve documented semantics. |
| CLI-053 | `autopilot phase-done -h, --help` | Preserve this option’s meaning in that command’s replacement. |
| CLI-054 | `autopilot phase-done --state STATE` | Preserve this option’s meaning in that command’s replacement. |
| CLI-055 | `autopilot phase-done --outcome {converged,drained,lane_reviewed,more_prds,rework,tasks_done}` | Preserve this option’s meaning in that command’s replacement. |
| CLI-056 | `autopilot resume-target` | R12: translate to the owned OVCAQ or plugin command; preserve documented semantics. |
| CLI-057 | `autopilot resume-target -h, --help` | Preserve this option’s meaning in that command’s replacement. |
| CLI-058 | `autopilot resume-target --state STATE` | Preserve this option’s meaning in that command’s replacement. |
| CLI-059 | `autopilot gate` | R07: preserve deterministic artifact acceptance in the new command surface. |
| CLI-060 | `autopilot gate -h, --help` | Preserve this option’s meaning in that command’s replacement. |
| CLI-061 | `autopilot gate --review-file REVIEW_FILE` | Preserve this option’s meaning in that command’s replacement. |
| CLI-062 | `autopilot gate --reviewers REVIEWERS` | Preserve this option’s meaning in that command’s replacement. |
| CLI-063 | `autopilot gate --require-codex-guard` | Preserve this option’s meaning in that command’s replacement. |
| CLI-064 | `autopilot gate --assert-constraint-met` | Preserve this option’s meaning in that command’s replacement. |
| CLI-065 | `autopilot gate --findings FINDINGS` | Preserve this option’s meaning in that command’s replacement. |
| CLI-066 | `autopilot cap-check` | R12: translate to the owned OVCAQ or plugin command; preserve documented semantics. |
| CLI-067 | `autopilot cap-check -h, --help` | Preserve this option’s meaning in that command’s replacement. |
| CLI-068 | `autopilot cap-check --review-file REVIEW_FILE` | Preserve this option’s meaning in that command’s replacement. |
| CLI-069 | `autopilot cap-check --previous PREVIOUS` | Preserve this option’s meaning in that command’s replacement. |
| CLI-070 | `autopilot cap-check --repo-root REPO_ROOT` | Preserve this option’s meaning in that command’s replacement. |
| CLI-071 | `autopilot group-rework` | R12: translate to the owned OVCAQ or plugin command; preserve documented semantics. |
| CLI-072 | `autopilot group-rework -h, --help` | Preserve this option’s meaning in that command’s replacement. |
| CLI-073 | `autopilot group-rework --findings FINDINGS` | Preserve this option’s meaning in that command’s replacement. |
| CLI-074 | `autopilot verify` | R12: translate to the owned OVCAQ or plugin command; preserve documented semantics. |
| CLI-075 | `autopilot verify -h, --help` | Preserve this option’s meaning in that command’s replacement. |
| CLI-076 | `autopilot verify --gate-command GATE_COMMAND` | Preserve this option’s meaning in that command’s replacement. |
| CLI-077 | `autopilot verify --repo-root REPO_ROOT` | Preserve this option’s meaning in that command’s replacement. |
| CLI-078 | `autopilot verify --cycle CYCLE` | Preserve this option’s meaning in that command’s replacement. |
| CLI-079 | `autopilot verify --log LOG` | Preserve this option’s meaning in that command’s replacement. |
| CLI-080 | `autopilot review-stage` | R07: retain artifact staging through the new state contract. |
| CLI-081 | `autopilot review-stage -h, --help` | Preserve this option’s meaning in that command’s replacement. |
| CLI-082 | `autopilot review-stage --cycle-id CYCLE_ID` | Preserve this option’s meaning in that command’s replacement. |
| CLI-083 | `autopilot review-stage --state STATE` | Preserve this option’s meaning in that command’s replacement. |
| CLI-084 | `autopilot review-stage --since SINCE` | Preserve this option’s meaning in that command’s replacement. |
| CLI-085 | `autopilot review-stage --repo-root REPO_ROOT` | Preserve this option’s meaning in that command’s replacement. |
| CLI-086 | `autopilot review-stage --gate-command GATE_COMMAND` | Preserve this option’s meaning in that command’s replacement. |
| CLI-087 | `autopilot review-stage --replay-cmd REPLAY_CMD` | Preserve this option’s meaning in that command’s replacement. |
| CLI-088 | `autopilot review-stage --tasks-json TASKS_JSON` | Preserve this option’s meaning in that command’s replacement. |
| CLI-089 | `autopilot review-stage --prd PRD` | Preserve this option’s meaning in that command’s replacement. |
| CLI-090 | `autopilot review-stage --design-doc DESIGN_DOC` | Preserve this option’s meaning in that command’s replacement. |
| CLI-091 | `autopilot review-stage --roster ROSTER` | Preserve this option’s meaning in that command’s replacement. |
| CLI-092 | `autopilot review-stage --settled-ledger SETTLED_LEDGER` | Preserve this option’s meaning in that command’s replacement. |
| CLI-093 | `autopilot review-stage --prior-findings PRIOR_FINDINGS` | Preserve this option’s meaning in that command’s replacement. |
| CLI-094 | `autopilot review-close` | R07: retain gated review closure through the sole state writer. |
| CLI-095 | `autopilot review-close -h, --help` | Preserve this option’s meaning in that command’s replacement. |
| CLI-096 | `autopilot review-close --review-file REVIEW_FILE` | Preserve this option’s meaning in that command’s replacement. |
| CLI-097 | `autopilot review-close --state STATE` | Preserve this option’s meaning in that command’s replacement. |
| CLI-098 | `autopilot review-close --batch-id {decision-gate,tail-sweep}` | Preserve this option’s meaning in that command’s replacement. |
| CLI-099 | `autopilot review-close --findings FINDINGS` | Preserve this option’s meaning in that command’s replacement. |
| CLI-100 | `autopilot review-close --default-tier DEFAULT_TIER` | Preserve this option’s meaning in that command’s replacement. |
| CLI-101 | `autopilot review-close --require-codex-guard` | Preserve this option’s meaning in that command’s replacement. |
| CLI-102 | `autopilot render` | R12: translate to the owned OVCAQ or plugin command; preserve documented semantics. |
| CLI-103 | `autopilot render -h, --help` | Preserve this option’s meaning in that command’s replacement. |
| CLI-104 | `autopilot render --state STATE` | Preserve this option’s meaning in that command’s replacement. |
| CLI-105 | `autopilot render --metrics METRICS` | Preserve this option’s meaning in that command’s replacement. |
| CLI-106 | `autopilot render --now NOW` | Preserve this option’s meaning in that command’s replacement. |
| CLI-107 | `autopilot render --stdout` | Preserve this option’s meaning in that command’s replacement. |
| CLI-108 | `autopilot render --summary` | Preserve this option’s meaning in that command’s replacement. |
| CLI-109 | `autopilot render --stalled` | Preserve this option’s meaning in that command’s replacement. |
| CLI-110 | `autopilot render --site SITE` | Preserve this option’s meaning in that command’s replacement. |
| CLI-111 | `autopilot render --detail DETAIL` | Preserve this option’s meaning in that command’s replacement. |
| CLI-112 | `autopilot status` | R12: translate to the owned OVCAQ or plugin command; preserve documented semantics. |
| CLI-113 | `autopilot status -h, --help` | Preserve this option’s meaning in that command’s replacement. |
| CLI-114 | `autopilot status --state STATE` | Preserve this option’s meaning in that command’s replacement. |
| CLI-115 | `autopilot loop` | R13: supervision moves to OVCAQ; preserve bounded recovery and fresh sessions. |
| CLI-116 | `autopilot loop -h, --help` | Preserve this option’s meaning in that command’s replacement. |
| CLI-117 | `autopilot review-once` | R13: map isolated review/finalization launch into OVCAQ. |
| CLI-118 | `autopilot review-once -h, --help` | Preserve this option’s meaning in that command’s replacement. |
| CLI-119 | `autopilot custody` | R16: preserve durable custody and pre-push enforcement. |
| CLI-120 | `autopilot custody -h, --help` | Preserve this option’s meaning in that command’s replacement. |
| CLI-121 | `autopilot mint-stubs` | R12: translate to the owned OVCAQ or plugin command; preserve documented semantics. |
| CLI-122 | `autopilot mint-stubs -h, --help` | Preserve this option’s meaning in that command’s replacement. |
| CLI-123 | `autopilot mint-stubs --state STATE` | Preserve this option’s meaning in that command’s replacement. |
| CLI-124 | `autopilot mint-stubs --batch BATCH` | Preserve this option’s meaning in that command’s replacement. |
| CLI-125 | `autopilot mint-stubs --prds PRDS` | Preserve this option’s meaning in that command’s replacement. |
| CLI-126 | `autopilot dirty` | R12: translate to the owned OVCAQ or plugin command; preserve documented semantics. |
| CLI-127 | `autopilot dirty -h, --help` | Preserve this option’s meaning in that command’s replacement. |
| CLI-128 | `autopilot dirty --state STATE` | Preserve this option’s meaning in that command’s replacement. |
| CLI-129 | `autopilot record-store` | R12: translate to the owned OVCAQ or plugin command; preserve documented semantics. |
| CLI-130 | `autopilot record-store -h, --help` | Preserve this option’s meaning in that command’s replacement. |
| CLI-131 | `autopilot record-store --state STATE` | Preserve this option’s meaning in that command’s replacement. |
| CLI-132 | `autopilot record-store --site SITE` | Preserve this option’s meaning in that command’s replacement. |
| CLI-133 | `autopilot record-store --prd PRD` | Preserve this option’s meaning in that command’s replacement. |
| CLI-134 | `autopilot ensure-store` | R12: translate to the owned OVCAQ or plugin command; preserve documented semantics. |
| CLI-135 | `autopilot ensure-store -h, --help` | Preserve this option’s meaning in that command’s replacement. |
| CLI-136 | `autopilot ensure-store --state STATE` | Preserve this option’s meaning in that command’s replacement. |
| CLI-137 | `autopilot catchup-probe` | R12: translate to the owned OVCAQ or plugin command; preserve documented semantics. |
| CLI-138 | `autopilot catchup-probe -h, --help` | Preserve this option’s meaning in that command’s replacement. |
| CLI-139 | `autopilot catchup-probe --state STATE` | Preserve this option’s meaning in that command’s replacement. |
| CLI-140 | `autopilot wave` | R15: establish wave parity before removing the old interface. |
| CLI-141 | `autopilot wave -h, --help` | Preserve this option’s meaning in that command’s replacement. |
| CLI-142 | `autopilot markers` | R12: translate to the owned OVCAQ or plugin command; preserve documented semantics. |
| CLI-143 | `autopilot markers -h, --help` | Preserve this option’s meaning in that command’s replacement. |
| CLI-144 | `autopilot markers --state STATE` | Preserve this option’s meaning in that command’s replacement. |
| CLI-145 | `autopilot markers --check NAME [NAME ...]` | Preserve this option’s meaning in that command’s replacement. |
| CLI-146 | `autopilot markers --clear NAME [NAME ...]` | Preserve this option’s meaning in that command’s replacement. |
| CLI-147 | `autopilot render audit` | R12: translate to the owned OVCAQ or plugin command; preserve documented semantics. |
| CLI-148 | `autopilot render audit -h, --help` | Preserve this option’s meaning in that command’s replacement. |
| CLI-149 | `autopilot render audit --state STATE` | Preserve this option’s meaning in that command’s replacement. |
| CLI-150 | `autopilot render audit --metrics METRICS` | Preserve this option’s meaning in that command’s replacement. |
| CLI-151 | `autopilot render audit --now NOW` | Preserve this option’s meaning in that command’s replacement. |
| CLI-152 | `autopilot render audit --stdout` | Preserve this option’s meaning in that command’s replacement. |
| CLI-153 | `autopilot render audit --summary` | Preserve this option’s meaning in that command’s replacement. |
| CLI-154 | `autopilot render audit --stalled` | Preserve this option’s meaning in that command’s replacement. |
| CLI-155 | `autopilot render audit --site SITE` | Preserve this option’s meaning in that command’s replacement. |
| CLI-156 | `autopilot render audit --detail DETAIL` | Preserve this option’s meaning in that command’s replacement. |
| CLI-157 | `autopilot render report` | R12: translate to the owned OVCAQ or plugin command; preserve documented semantics. |
| CLI-158 | `autopilot render report -h, --help` | Preserve this option’s meaning in that command’s replacement. |
| CLI-159 | `autopilot render report --state STATE` | Preserve this option’s meaning in that command’s replacement. |
| CLI-160 | `autopilot render report --metrics METRICS` | Preserve this option’s meaning in that command’s replacement. |
| CLI-161 | `autopilot render report --now NOW` | Preserve this option’s meaning in that command’s replacement. |
| CLI-162 | `autopilot render report --stdout` | Preserve this option’s meaning in that command’s replacement. |
| CLI-163 | `autopilot render report --summary` | Preserve this option’s meaning in that command’s replacement. |
| CLI-164 | `autopilot render report --stalled` | Preserve this option’s meaning in that command’s replacement. |
| CLI-165 | `autopilot render report --site SITE` | Preserve this option’s meaning in that command’s replacement. |
| CLI-166 | `autopilot render report --detail DETAIL` | Preserve this option’s meaning in that command’s replacement. |
| CLI-167 | `autopilot render metrics` | R12: translate to the owned OVCAQ or plugin command; preserve documented semantics. |
| CLI-168 | `autopilot render metrics -h, --help` | Preserve this option’s meaning in that command’s replacement. |
| CLI-169 | `autopilot render metrics --state STATE` | Preserve this option’s meaning in that command’s replacement. |
| CLI-170 | `autopilot render metrics --metrics METRICS` | Preserve this option’s meaning in that command’s replacement. |
| CLI-171 | `autopilot render metrics --now NOW` | Preserve this option’s meaning in that command’s replacement. |
| CLI-172 | `autopilot render metrics --stdout` | Preserve this option’s meaning in that command’s replacement. |
| CLI-173 | `autopilot render metrics --summary` | Preserve this option’s meaning in that command’s replacement. |
| CLI-174 | `autopilot render metrics --stalled` | Preserve this option’s meaning in that command’s replacement. |
| CLI-175 | `autopilot render metrics --site SITE` | Preserve this option’s meaning in that command’s replacement. |
| CLI-176 | `autopilot render metrics --detail DETAIL` | Preserve this option’s meaning in that command’s replacement. |
| CLI-177 | `autopilot custody list` | R16: preserve durable custody and pre-push enforcement. |
| CLI-178 | `autopilot custody list -h, --help` | Preserve this option’s meaning in that command’s replacement. |
| CLI-179 | `autopilot custody list --state STATE` | Preserve this option’s meaning in that command’s replacement. |
| CLI-180 | `autopilot custody resolve` | R16: preserve durable custody and pre-push enforcement. |
| CLI-181 | `autopilot custody resolve -h, --help` | Preserve this option’s meaning in that command’s replacement. |
| CLI-182 | `autopilot custody resolve --state STATE` | Preserve this option’s meaning in that command’s replacement. |
| CLI-183 | `autopilot custody resolve --prd PRD` | Preserve this option’s meaning in that command’s replacement. |
| CLI-184 | `autopilot custody resolve --choice {revert,branch-and-revert,accept}` | Preserve this option’s meaning in that command’s replacement. |
| CLI-185 | `autopilot wave plan` | R15: establish wave parity before removing the old interface. |
| CLI-186 | `autopilot wave plan -h, --help` | Preserve this option’s meaning in that command’s replacement. |
| CLI-187 | `autopilot wave plan --state STATE` | Preserve this option’s meaning in that command’s replacement. |
| CLI-188 | `autopilot wave plan --max-lanes MAX_LANES` | Preserve this option’s meaning in that command’s replacement. |
| CLI-189 | `autopilot wave launch` | R15: establish wave parity before removing the old interface. |
| CLI-190 | `autopilot wave launch -h, --help` | Preserve this option’s meaning in that command’s replacement. |
| CLI-191 | `autopilot wave launch --state STATE` | Preserve this option’s meaning in that command’s replacement. |
| CLI-192 | `autopilot wave status` | R15: establish wave parity before removing the old interface. |
| CLI-193 | `autopilot wave status -h, --help` | Preserve this option’s meaning in that command’s replacement. |
| CLI-194 | `autopilot wave status --state STATE` | Preserve this option’s meaning in that command’s replacement. |
| CLI-195 | `autopilot wave abort` | R15: establish wave parity before removing the old interface. |
| CLI-196 | `autopilot wave abort -h, --help` | Preserve this option’s meaning in that command’s replacement. |
| CLI-197 | `autopilot wave abort --state STATE` | Preserve this option’s meaning in that command’s replacement. |
| CLI-198 | `autopilot wave assemble` | R15: establish wave parity before removing the old interface. |
| CLI-199 | `autopilot wave assemble -h, --help` | Preserve this option’s meaning in that command’s replacement. |
| CLI-200 | `autopilot wave assemble --state STATE` | Preserve this option’s meaning in that command’s replacement. |
| CLI-201 | `autopilot wave review` | R15: establish wave parity before removing the old interface. |
| CLI-202 | `autopilot wave review -h, --help` | Preserve this option’s meaning in that command’s replacement. |
| CLI-203 | `autopilot wave review --state STATE` | Preserve this option’s meaning in that command’s replacement. |
| CLI-204 | `autopilot wave land` | R15: establish wave parity before removing the old interface. |
| CLI-205 | `autopilot wave land -h, --help` | Preserve this option’s meaning in that command’s replacement. |
| CLI-206 | `autopilot wave land --state STATE` | Preserve this option’s meaning in that command’s replacement. |
| CLI-207 | `autopilot wave run` | R15: establish wave parity before removing the old interface. |
| CLI-208 | `autopilot wave run -h, --help` | Preserve this option’s meaning in that command’s replacement. |
| CLI-209 | `autopilot wave run --state STATE` | Preserve this option’s meaning in that command’s replacement. |
| CLI-210 | `autopilot wave run --max-lanes MAX_LANES` | Preserve this option’s meaning in that command’s replacement. |
| CLI-211 | `autopilot wave run --review-slots REVIEW_SLOTS` | Preserve this option’s meaning in that command’s replacement. |
| CLI-212 | `autopilot wave run --yes` | Preserve this option’s meaning in that command’s replacement. |

## Skill entry points and runner options

| Row | Surface | Reason |
| --- | --- | --- |
| SK-01 | `run-autopilot`: no argument; `<prd-filename>`; `status`; `review-batch` | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| SK-02 | `design-solution`: `<prd-path>`; automatic single-PRD resolution; `--rework <review-file>` | R03: Preserve design behavior while replacing host paths and reviewer dispatch. |
| SK-03 | `plan-tasks`: PRD selection and replan mode | R04: Translate task storage and tier selection while preserving planning policy. |
| SK-04 | `work`: pending tasks and rework task filter | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| SK-05 | `review-work-completion`: finished PRD and all required review lenses | R07: Preserve review rules through isolated jobs and authoritative completion gates. |
| SK-06 | `review-blindly`: spec-only standalone review | R08: Replace foreground-Claude execution while preserving the blind contract. |
| SK-07 | `review-plan`: current active plan | R09: Use the host plan and question interfaces without changing review dimensions. |
| SK-08 | `fast-track`: `<card.md> [<card.md> ...]`; `--push` | R10: Preserve card and review behavior through portable runtime interfaces. |
| SK-09 | `use-codex`: prompt file and native Codex/Copilot dispatch | R21: Keep Codex backend semantics in an explicit host/job adapter. |
| SK-10 | `use-gemini`: prompt, interactive and resume modes | R21: Keep Gemini backend semantics in an explicit host/job adapter. |
| SK-11 | `use-sonnet`: prompt, interactive and resume modes | R21: Keep Claude backend semantics in an explicit host/job adapter. |
| RUN-01 | `codex-run.sh -m / --model` | R21: retain backend-specific permission/session/output meaning; adapt invocation. |
| RUN-02 | `codex-run.sh -a / --allow-tools` | R21: retain backend-specific permission/session/output meaning; adapt invocation. |
| RUN-03 | `codex-run.sh -y / --yolo` | R21: retain backend-specific permission/session/output meaning; adapt invocation. |
| RUN-04 | `codex-run.sh -s / --silent` | R21: retain backend-specific permission/session/output meaning; adapt invocation. |
| RUN-05 | `codex-run.sh -d / --dir` | R21: retain backend-specific permission/session/output meaning; adapt invocation. |
| RUN-06 | `codex-run.sh -f / --file` | R21: retain backend-specific permission/session/output meaning; adapt invocation. |
| RUN-07 | `codex-run.sh -o / --output` | R21: retain backend-specific permission/session/output meaning; adapt invocation. |
| RUN-08 | `codex-run.sh --emit-thread-id` | R21: retain backend-specific permission/session/output meaning; adapt invocation. |
| RUN-09 | `codex-run.sh --resume-thread` | R21: retain backend-specific permission/session/output meaning; adapt invocation. |
| RUN-10 | `codex-run.sh -h / --help` | R21: retain backend-specific permission/session/output meaning; adapt invocation. |
| RUN-11 | `gemini-run.sh -m / --model` | R21: retain backend-specific permission/session/output meaning; adapt invocation. |
| RUN-12 | `gemini-run.sh -f / --file` | R21: retain backend-specific permission/session/output meaning; adapt invocation. |
| RUN-13 | `gemini-run.sh -i / --interactive` | R21: retain backend-specific permission/session/output meaning; adapt invocation. |
| RUN-14 | `gemini-run.sh -a / --allow-tools` | R21: retain backend-specific permission/session/output meaning; adapt invocation. |
| RUN-15 | `gemini-run.sh -y / --yolo` | R21: retain backend-specific permission/session/output meaning; adapt invocation. |
| RUN-16 | `gemini-run.sh -d / --dir` | R21: retain backend-specific permission/session/output meaning; adapt invocation. |
| RUN-17 | `gemini-run.sh -o / --output` | R21: retain backend-specific permission/session/output meaning; adapt invocation. |
| RUN-18 | `gemini-run.sh -s / --silent` | R21: retain backend-specific permission/session/output meaning; adapt invocation. |
| RUN-19 | `gemini-run.sh -c / --continue` | R21: retain backend-specific permission/session/output meaning; adapt invocation. |
| RUN-20 | `gemini-run.sh -r / --resume` | R21: retain backend-specific permission/session/output meaning; adapt invocation. |
| RUN-21 | `gemini-run.sh -h / --help` | R21: retain backend-specific permission/session/output meaning; adapt invocation. |
| RUN-22 | `sonnet-run.sh -m / --model` | R21: retain backend-specific permission/session/output meaning; adapt invocation. |
| RUN-23 | `sonnet-run.sh -f / --file` | R21: retain backend-specific permission/session/output meaning; adapt invocation. |
| RUN-24 | `sonnet-run.sh -i / --interactive` | R21: retain backend-specific permission/session/output meaning; adapt invocation. |
| RUN-25 | `sonnet-run.sh -a / --allow-edits` | R21: retain backend-specific permission/session/output meaning; adapt invocation. |
| RUN-26 | `sonnet-run.sh -y / --yolo` | R21: retain backend-specific permission/session/output meaning; adapt invocation. |
| RUN-27 | `sonnet-run.sh -d / --dir` | R21: retain backend-specific permission/session/output meaning; adapt invocation. |
| RUN-28 | `sonnet-run.sh -o / --output` | R21: retain backend-specific permission/session/output meaning; adapt invocation. |
| RUN-29 | `sonnet-run.sh -s / --silent` | R21: retain backend-specific permission/session/output meaning; adapt invocation. |
| RUN-30 | `sonnet-run.sh -t / --tools` | R21: retain backend-specific permission/session/output meaning; adapt invocation. |
| RUN-31 | `sonnet-run.sh -S / --session-id` | R21: retain backend-specific permission/session/output meaning; adapt invocation. |
| RUN-32 | `sonnet-run.sh -R / --resume-print` | R21: retain backend-specific permission/session/output meaning; adapt invocation. |
| RUN-33 | `sonnet-run.sh -c / --continue` | R21: retain backend-specific permission/session/output meaning; adapt invocation. |
| RUN-34 | `sonnet-run.sh -r / --resume` | R21: retain backend-specific permission/session/output meaning; adapt invocation. |
| RUN-35 | `sonnet-run.sh -h / --help` | R21: retain backend-specific permission/session/output meaning; adapt invocation. |

Codex and Gemini live help was refused by the parent-host guard. Their option rows come from skill documentation and the displayed usage definitions; no guard was disabled. Documentation-only extra flags, including `--effort`, remain in the next table for implementation reconciliation.

## Additional documented flag spellings

One row per long-option spelling in the documentation corpus. The first cited use supplies context; repeated uses remain owned by their procedure. Some belong to git, shells, provider CLIs, or test tools.

| Row | Flag | First documented use | Reason |
| --- | --- | --- | --- |
| OPT-001 | `--abbrev-ref` | [skills/work/references/gate-failure.md:63](../../../../../claude-autopilot/skills/work/references/gate-failure.md#L63) | R06: retain its owning procedure’s semantics. |
| OPT-002 | `--action` | [skills/run-autopilot/references/phase-review.md:147](../../../../../claude-autopilot/skills/run-autopilot/references/phase-review.md#L147) | R02: retain its owning procedure’s semantics. |
| OPT-003 | `--add-dir` | [skills/use-sonnet/SKILL.md:47](../../../../../claude-autopilot/skills/use-sonnet/SKILL.md#L47) | R21: retain its owning procedure’s semantics. |
| OPT-004 | `--algorithmic-risk` | [skills/plan-tasks/SKILL.md:258](../../../../../claude-autopilot/skills/plan-tasks/SKILL.md#L258) | R04: retain its owning procedure’s semantics. |
| OPT-005 | `--allow-edits` | [skills/use-sonnet/SKILL.md:45](../../../../../claude-autopilot/skills/use-sonnet/SKILL.md#L45) | R21: retain its owning procedure’s semantics. |
| OPT-006 | `--allow-tools` | [skills/use-codex/SKILL.md:52](../../../../../claude-autopilot/skills/use-codex/SKILL.md#L52) | R21: retain its owning procedure’s semantics. |
| OPT-007 | `--approval-mode` | [skills/use-gemini/SKILL.md:108](../../../../../claude-autopilot/skills/use-gemini/SKILL.md#L108) | R21: retain its owning procedure’s semantics. |
| OPT-008 | `--approved-only` | [skills/work/references/qwen-integration.md:3](../../../../../claude-autopilot/skills/work/references/qwen-integration.md#L3) | R06: retain its owning procedure’s semantics. |
| OPT-009 | `--assert-constraint-met` | [skills/run-autopilot/references/phase-review.md:170](../../../../../claude-autopilot/skills/run-autopilot/references/phase-review.md#L170) | R02: retain its owning procedure’s semantics. |
| OPT-010 | `--authorized` | [skills/run-autopilot/SKILL.md:146](../../../../../claude-autopilot/skills/run-autopilot/SKILL.md#L146) | R02: retain its owning procedure’s semantics. |
| OPT-011 | `--bash` | [skills/work/references/task-boundary-handoff.md:20](../../../../../claude-autopilot/skills/work/references/task-boundary-handoff.md#L20) | R06: retain its owning procedure’s semantics. |
| OPT-012 | `--batch` | [skills/fast-track/SKILL.md:454](../../../../../claude-autopilot/skills/fast-track/SKILL.md#L454) | R10: retain its owning procedure’s semantics. |
| OPT-013 | `--batch-id` | [skills/review-work-completion/SKILL.md:413](../../../../../claude-autopilot/skills/review-work-completion/SKILL.md#L413) | R07: retain its owning procedure’s semantics. |
| OPT-014 | `--budget` | [skills/design-solution/SKILL.md:215](../../../../../claude-autopilot/skills/design-solution/SKILL.md#L215) | R03: retain its owning procedure’s semantics. |
| OPT-015 | `--cached` | [skills/work/references/subagent-dispatch.md:187](../../../../../claude-autopilot/skills/work/references/subagent-dispatch.md#L187) | R06: retain its owning procedure’s semantics. |
| OPT-016 | `--card` | [skills/fast-track/SKILL.md:646](../../../../../claude-autopilot/skills/fast-track/SKILL.md#L646) | R10: retain its owning procedure’s semantics. |
| OPT-017 | `--carl-available` | [skills/fast-track/SKILL.md:105](../../../../../claude-autopilot/skills/fast-track/SKILL.md#L105) | R10: retain its owning procedure’s semantics. |
| OPT-018 | `--ceiling` | [skills/plan-tasks/SKILL.md:391](../../../../../claude-autopilot/skills/plan-tasks/SKILL.md#L391) | R04: retain its owning procedure’s semantics. |
| OPT-019 | `--check` | [skills/work/SKILL.md:458](../../../../../claude-autopilot/skills/work/SKILL.md#L458) | R06: retain its owning procedure’s semantics. |
| OPT-020 | `--choice` | [skills/run-autopilot/references/phase-build.md:165](../../../../../claude-autopilot/skills/run-autopilot/references/phase-build.md#L165) | R02: retain its owning procedure’s semantics. |
| OPT-021 | `--clear` | [skills/run-autopilot/references/phase-build.md:94](../../../../../claude-autopilot/skills/run-autopilot/references/phase-build.md#L94) | R02: retain its owning procedure’s semantics. |
| OPT-022 | `--clear-cap` | [skills/work/SKILL.md:188](../../../../../claude-autopilot/skills/work/SKILL.md#L188) | R06: retain its owning procedure’s semantics. |
| OPT-023 | `--confirmed` | [skills/fast-track/SKILL.md:646](../../../../../claude-autopilot/skills/fast-track/SKILL.md#L646) | R10: retain its owning procedure’s semantics. |
| OPT-024 | `--continue` | [skills/use-sonnet/SKILL.md:49](../../../../../claude-autopilot/skills/use-sonnet/SKILL.md#L49) | R21: retain its owning procedure’s semantics. |
| OPT-025 | `--contract-edit` | [skills/plan-tasks/SKILL.md:258](../../../../../claude-autopilot/skills/plan-tasks/SKILL.md#L258) | R04: retain its owning procedure’s semantics. |
| OPT-026 | `--cost` | [skills/fast-track/SKILL.md:649](../../../../../claude-autopilot/skills/fast-track/SKILL.md#L649) | R10: retain its owning procedure’s semantics. |
| OPT-027 | `--cycle` | [skills/review-work-completion/SKILL.md:403](../../../../../claude-autopilot/skills/review-work-completion/SKILL.md#L403) | R07: retain its owning procedure’s semantics. |
| OPT-028 | `--cycle-id` | [skills/review-work-completion/SKILL.md:153](../../../../../claude-autopilot/skills/review-work-completion/SKILL.md#L153) | R07: retain its owning procedure’s semantics. |
| OPT-029 | `--dangerously-bypass-approvals-and-sandbox` | [skills/use-codex/references/host-markers.md:31](../../../../../claude-autopilot/skills/use-codex/references/host-markers.md#L31) | R21: retain its owning procedure’s semantics. |
| OPT-030 | `--default-model` | [skills/plan-tasks/SKILL.md:258](../../../../../claude-autopilot/skills/plan-tasks/SKILL.md#L258) | R04: retain its owning procedure’s semantics. |
| OPT-031 | `--default-tier` | [skills/run-autopilot/references/phase-review.md:195](../../../../../claude-autopilot/skills/run-autopilot/references/phase-review.md#L195) | R02: retain its owning procedure’s semantics. |
| OPT-032 | `--design-doc` | [skills/review-work-completion/SKILL.md:163](../../../../../claude-autopilot/skills/review-work-completion/SKILL.md#L163) | R07: retain its owning procedure’s semantics. |
| OPT-033 | `--detail` | [skills/fast-track/SKILL.md:397](../../../../../claude-autopilot/skills/fast-track/SKILL.md#L397) | R10: retain its owning procedure’s semantics. |
| OPT-034 | `--diff` | [skills/work/SKILL.md:236](../../../../../claude-autopilot/skills/work/SKILL.md#L236) | R06: retain its owning procedure’s semantics. |
| OPT-035 | `--diff-filter` | [skills/work/references/style-gate.md:21](../../../../../claude-autopilot/skills/work/references/style-gate.md#L21) | R06: retain its owning procedure’s semantics. |
| OPT-036 | `--dir` | [skills/use-codex/SKILL.md:54](../../../../../claude-autopilot/skills/use-codex/SKILL.md#L54) | R21: retain its owning procedure’s semantics. |
| OPT-037 | `--dispatch-kind` | [skills/work/SKILL.md:83](../../../../../claude-autopilot/skills/work/SKILL.md#L83) | R06: retain its owning procedure’s semantics. |
| OPT-038 | `--dispatch-task` | [skills/work/SKILL.md:83](../../../../../claude-autopilot/skills/work/SKILL.md#L83) | R06: retain its owning procedure’s semantics. |
| OPT-039 | `--doc` | [skills/work/references/final-verification.md:16](../../../../../claude-autopilot/skills/work/references/final-verification.md#L16) | R06: retain its owning procedure’s semantics. |
| OPT-040 | `--dry-run` | [skills/use-codex/SKILL.md:107](../../../../../claude-autopilot/skills/use-codex/SKILL.md#L107) | R21: retain its owning procedure’s semantics. |
| OPT-041 | `--edge` | [skills/run-autopilot/SKILL.md:201](../../../../../claude-autopilot/skills/run-autopilot/SKILL.md#L201) | R02: retain its owning procedure’s semantics. |
| OPT-042 | `--effort` | [README.md:147](../../../../../claude-autopilot/README.md#L147) | R01: retain its owning procedure’s semantics. |
| OPT-043 | `--emit-thread-id` | [skills/use-codex/SKILL.md:57](../../../../../claude-autopilot/skills/use-codex/SKILL.md#L57) | R21: retain its owning procedure’s semantics. |
| OPT-044 | `--ephemeral` | [skills/review-work-completion/references/agent-invocation.md:47](../../../../../claude-autopilot/skills/review-work-completion/references/agent-invocation.md#L47) | R07: retain its owning procedure’s semantics. |
| OPT-045 | `--exclude-standard` | [skills/work/references/style-gate.md:17](../../../../../claude-autopilot/skills/work/references/style-gate.md#L17) | R06: retain its owning procedure’s semantics. |
| OPT-046 | `--file` | [skills/use-codex/SKILL.md:51](../../../../../claude-autopilot/skills/use-codex/SKILL.md#L51) | R21: retain its owning procedure’s semantics. |
| OPT-047 | `--files` | [skills/fast-track/SKILL.md:315](../../../../../claude-autopilot/skills/fast-track/SKILL.md#L315) | R10: retain its owning procedure’s semantics. |
| OPT-048 | `--files-file` | [skills/plan-tasks/SKILL.md:258](../../../../../claude-autopilot/skills/plan-tasks/SKILL.md#L258) | R04: retain its owning procedure’s semantics. |
| OPT-049 | `--findings` | [skills/fast-track/SKILL.md:646](../../../../../claude-autopilot/skills/fast-track/SKILL.md#L646) | R10: retain its owning procedure’s semantics. |
| OPT-050 | `--force` | [skills/run-autopilot/references/waves.md:94](../../../../../claude-autopilot/skills/run-autopilot/references/waves.md#L94) | R02: retain its owning procedure’s semantics. |
| OPT-051 | `--format` | [skills/work/SKILL.md:193](../../../../../claude-autopilot/skills/work/SKILL.md#L193) | R06: retain its owning procedure’s semantics. |
| OPT-052 | `--gate-command` | [skills/review-work-completion/SKILL.md:153](../../../../../claude-autopilot/skills/review-work-completion/SKILL.md#L153) | R07: retain its owning procedure’s semantics. |
| OPT-053 | `--git-dir` | [skills/review-work-completion/SKILL.md:190](../../../../../claude-autopilot/skills/review-work-completion/SKILL.md#L190) | R07: retain its owning procedure’s semantics. |
| OPT-054 | `--hard` | [skills/work/references/gate-failure.md:58](../../../../../claude-autopilot/skills/work/references/gate-failure.md#L58) | R06: retain its owning procedure’s semantics. |
| OPT-055 | `--help` | [skills/use-codex/SKILL.md:90](../../../../../claude-autopilot/skills/use-codex/SKILL.md#L90) | R21: retain its owning procedure’s semantics. |
| OPT-056 | `--interactive` | [skills/use-gemini/SKILL.md:107](../../../../../claude-autopilot/skills/use-gemini/SKILL.md#L107) | R21: retain its owning procedure’s semantics. |
| OPT-057 | `--issue` | [skills/run-autopilot/references/phase-review.md:147](../../../../../claude-autopilot/skills/run-autopilot/references/phase-review.md#L147) | R02: retain its owning procedure’s semantics. |
| OPT-058 | `--item` | [skills/fast-track/SKILL.md:646](../../../../../claude-autopilot/skills/fast-track/SKILL.md#L646) | R10: retain its owning procedure’s semantics. |
| OPT-059 | `--jobs` | [skills/work/references/design-rationale.md:26](../../../../../claude-autopilot/skills/work/references/design-rationale.md#L26) | R06: retain its owning procedure’s semantics. |
| OPT-060 | `--json` | [skills/fast-track/SKILL.md:454](../../../../../claude-autopilot/skills/fast-track/SKILL.md#L454) | R10: retain its owning procedure’s semantics. |
| OPT-061 | `--keep` | [skills/fast-track/SKILL.md:609](../../../../../claude-autopilot/skills/fast-track/SKILL.md#L609) | R10: retain its owning procedure’s semantics. |
| OPT-062 | `--kind` | [skills/fast-track/SKILL.md:142](../../../../../claude-autopilot/skills/fast-track/SKILL.md#L142) | R10: retain its owning procedure’s semantics. |
| OPT-063 | `--ledger` | [skills/fast-track/SKILL.md:425](../../../../../claude-autopilot/skills/fast-track/SKILL.md#L425) | R10: retain its owning procedure’s semantics. |
| OPT-064 | `--ledger-dismiss` | [skills/review-work-completion/SKILL.md:230](../../../../../claude-autopilot/skills/review-work-completion/SKILL.md#L230) | R07: retain its owning procedure’s semantics. |
| OPT-065 | `--lenses` | [skills/fast-track/SKILL.md:452](../../../../../claude-autopilot/skills/fast-track/SKILL.md#L452) | R10: retain its owning procedure’s semantics. |
| OPT-066 | `--lines` | [skills/plan-tasks/SKILL.md:258](../../../../../claude-autopilot/skills/plan-tasks/SKILL.md#L258) | R04: retain its owning procedure’s semantics. |
| OPT-067 | `--local` | [skills/run-autopilot/references/state-schema.md:279](../../../../../claude-autopilot/skills/run-autopilot/references/state-schema.md#L279) | R02: retain its owning procedure’s semantics. |
| OPT-068 | `--log` | [skills/use-sonnet/SKILL.md:29](../../../../../claude-autopilot/skills/use-sonnet/SKILL.md#L29) | R21: retain its owning procedure’s semantics. |
| OPT-069 | `--max-lanes` | [skills/run-autopilot/references/waves.md:14](../../../../../claude-autopilot/skills/run-autopilot/references/waves.md#L14) | R02: retain its owning procedure’s semantics. |
| OPT-070 | `--max-level` | [skills/work/SKILL.md:309](../../../../../claude-autopilot/skills/work/SKILL.md#L309) | R06: retain its owning procedure’s semantics. |
| OPT-071 | `--maxprocesses` | [skills/work/references/final-verification.md:16](../../../../../claude-autopilot/skills/work/references/final-verification.md#L16) | R06: retain its owning procedure’s semantics. |
| OPT-072 | `--mcp-config` | [skills/run-autopilot/SKILL.md:171](../../../../../claude-autopilot/skills/run-autopilot/SKILL.md#L171) | R02: retain its owning procedure’s semantics. |
| OPT-073 | `--model` | [skills/fast-track/SKILL.md:646](../../../../../claude-autopilot/skills/fast-track/SKILL.md#L646) | R10: retain its owning procedure’s semantics. |
| OPT-074 | `--name-only` | [skills/work/SKILL.md:389](../../../../../claude-autopilot/skills/work/SKILL.md#L389) | R06: retain its owning procedure’s semantics. |
| OPT-075 | `--no-commit-id` | [skills/work/SKILL.md:395](../../../../../claude-autopilot/skills/work/SKILL.md#L395) | R06: retain its owning procedure’s semantics. |
| OPT-076 | `--no-hooks` | [skills/run-autopilot/references/hook-recovery.md:26](../../../../../claude-autopilot/skills/run-autopilot/references/hook-recovery.md#L26) | R02: retain its owning procedure’s semantics. |
| OPT-077 | `--no-index` | [skills/work/SKILL.md:408](../../../../../claude-autopilot/skills/work/SKILL.md#L408) | R06: retain its owning procedure’s semantics. |
| OPT-078 | `--no-project` | [skills/review-work-completion/SKILL.md:160](../../../../../claude-autopilot/skills/review-work-completion/SKILL.md#L160) | R07: retain its owning procedure’s semantics. |
| OPT-079 | `--no-verify` | [skills/work/SKILL.md:367](../../../../../claude-autopilot/skills/work/SKILL.md#L367) | R06: retain its owning procedure’s semantics. |
| OPT-080 | `--once` | [skills/run-autopilot/scripts/README.md:16](../../../../../claude-autopilot/skills/run-autopilot/scripts/README.md#L16) | R02: retain its owning procedure’s semantics. |
| OPT-081 | `--others` | [skills/work/references/style-gate.md:17](../../../../../claude-autopilot/skills/work/references/style-gate.md#L17) | R06: retain its owning procedure’s semantics. |
| OPT-082 | `--out` | [skills/fast-track/SKILL.md:126](../../../../../claude-autopilot/skills/fast-track/SKILL.md#L126) | R10: retain its owning procedure’s semantics. |
| OPT-083 | `--outcome` | [skills/fast-track/SKILL.md:156](../../../../../claude-autopilot/skills/fast-track/SKILL.md#L156) | R10: retain its owning procedure’s semantics. |
| OPT-084 | `--output` | [skills/use-codex/SKILL.md:55](../../../../../claude-autopilot/skills/use-codex/SKILL.md#L55) | R21: retain its owning procedure’s semantics. |
| OPT-085 | `--permission-mode` | [skills/use-sonnet/SKILL.md:45](../../../../../claude-autopilot/skills/use-sonnet/SKILL.md#L45) | R21: retain its owning procedure’s semantics. |
| OPT-086 | `--phase` | [skills/run-autopilot/SKILL.md:200](../../../../../claude-autopilot/skills/run-autopilot/SKILL.md#L200) | R02: retain its owning procedure’s semantics. |
| OPT-087 | `--porcelain` | [skills/work/SKILL.md:350](../../../../../claude-autopilot/skills/work/SKILL.md#L350) | R06: retain its owning procedure’s semantics. |
| OPT-088 | `--prd` | [skills/fast-track/SKILL.md:454](../../../../../claude-autopilot/skills/fast-track/SKILL.md#L454) | R10: retain its owning procedure’s semantics. |
| OPT-089 | `--prds` | [skills/run-autopilot/references/phase-build.md:34](../../../../../claude-autopilot/skills/run-autopilot/references/phase-build.md#L34) | R02: retain its owning procedure’s semantics. |
| OPT-090 | `--preflight` | [skills/work/references/qwen-integration.md:33](../../../../../claude-autopilot/skills/work/references/qwen-integration.md#L33) | R06: retain its owning procedure’s semantics. |
| OPT-091 | `--previous` | [skills/run-autopilot/references/phase-review.md:59](../../../../../claude-autopilot/skills/run-autopilot/references/phase-review.md#L59) | R02: retain its owning procedure’s semantics. |
| OPT-092 | `--print` | [skills/use-codex/references/dispatch-contract.md:21](../../../../../claude-autopilot/skills/use-codex/references/dispatch-contract.md#L21) | R21: retain its owning procedure’s semantics. |
| OPT-093 | `--prior-findings` | [skills/review-work-completion/SKILL.md:153](../../../../../claude-autopilot/skills/review-work-completion/SKILL.md#L153) | R07: retain its owning procedure’s semantics. |
| OPT-094 | `--prompt-file` | [skills/fast-track/SKILL.md:142](../../../../../claude-autopilot/skills/fast-track/SKILL.md#L142) | R10: retain its owning procedure’s semantics. |
| OPT-095 | `--push` | [skills/fast-track/SKILL.md:17](../../../../../claude-autopilot/skills/fast-track/SKILL.md#L17) | R10: retain its owning procedure’s semantics. |
| OPT-096 | `--reason` | [skills/run-autopilot/references/phase-review.md:147](../../../../../claude-autopilot/skills/run-autopilot/references/phase-review.md#L147) | R02: retain its owning procedure’s semantics. |
| OPT-097 | `--replay-cmd` | [skills/review-work-completion/SKILL.md:153](../../../../../claude-autopilot/skills/review-work-completion/SKILL.md#L153) | R07: retain its owning procedure’s semantics. |
| OPT-098 | `--repo-root` | [skills/run-autopilot/references/state-schema.md:547](../../../../../claude-autopilot/skills/run-autopilot/references/state-schema.md#L547) | R02: retain its owning procedure’s semantics. |
| OPT-099 | `--require-codex-guard` | [skills/review-work-completion/SKILL.md:438](../../../../../claude-autopilot/skills/review-work-completion/SKILL.md#L438) | R07: retain its owning procedure’s semantics. |
| OPT-100 | `--require-file` | [skills/fast-track/SKILL.md:133](../../../../../claude-autopilot/skills/fast-track/SKILL.md#L133) | R10: retain its owning procedure’s semantics. |
| OPT-101 | `--require-parent` | [skills/fast-track/SKILL.md:183](../../../../../claude-autopilot/skills/fast-track/SKILL.md#L183) | R10: retain its owning procedure’s semantics. |
| OPT-102 | `--restore-tests` | [skills/work/references/gate-failure.md:156](../../../../../claude-autopilot/skills/work/references/gate-failure.md#L156) | R06: retain its owning procedure’s semantics. |
| OPT-103 | `--resume` | [skills/run-autopilot/SKILL.md:136](../../../../../claude-autopilot/skills/run-autopilot/SKILL.md#L136) | R02: retain its owning procedure’s semantics. |
| OPT-104 | `--resume-thread` | [skills/review-work-completion/SKILL.md:144](../../../../../claude-autopilot/skills/review-work-completion/SKILL.md#L144) | R07: retain its owning procedure’s semantics. |
| OPT-105 | `--review-file` | [skills/review-blindly/SKILL.md:118](../../../../../claude-autopilot/skills/review-blindly/SKILL.md#L118) | R08: retain its owning procedure’s semantics. |
| OPT-106 | `--review-slots` | [skills/run-autopilot/references/waves.md:200](../../../../../claude-autopilot/skills/run-autopilot/references/waves.md#L200) | R02: retain its owning procedure’s semantics. |
| OPT-107 | `--reviewers` | [skills/review-work-completion/SKILL.md:429](../../../../../claude-autopilot/skills/review-work-completion/SKILL.md#L429) | R07: retain its owning procedure’s semantics. |
| OPT-108 | `--rework` | [skills/design-solution/SKILL.md:4](../../../../../claude-autopilot/skills/design-solution/SKILL.md#L4) | R03: retain its owning procedure’s semantics. |
| OPT-109 | `--root` | [skills/run-autopilot/references/dashboard-format.md:21](../../../../../claude-autopilot/skills/run-autopilot/references/dashboard-format.md#L21) | R02: retain its owning procedure’s semantics. |
| OPT-110 | `--roster` | [skills/review-work-completion/SKILL.md:153](../../../../../claude-autopilot/skills/review-work-completion/SKILL.md#L153) | R07: retain its owning procedure’s semantics. |
| OPT-111 | `--sandbox` | [skills/design-solution/SKILL.md:212](../../../../../claude-autopilot/skills/design-solution/SKILL.md#L212) | R03: retain its owning procedure’s semantics. |
| OPT-112 | `--send` | [skills/run-autopilot/references/phase-done.md:75](../../../../../claude-autopilot/skills/run-autopilot/references/phase-done.md#L75) | R02: retain its owning procedure’s semantics. |
| OPT-113 | `--set` | [skills/fast-track/SKILL.md:127](../../../../../claude-autopilot/skills/fast-track/SKILL.md#L127) | R10: retain its owning procedure’s semantics. |
| OPT-114 | `--set-cmd` | [skills/fast-track/SKILL.md:128](../../../../../claude-autopilot/skills/fast-track/SKILL.md#L128) | R10: retain its owning procedure’s semantics. |
| OPT-115 | `--set-file` | [skills/fast-track/SKILL.md:129](../../../../../claude-autopilot/skills/fast-track/SKILL.md#L129) | R10: retain its owning procedure’s semantics. |
| OPT-116 | `--settled-ledger` | [skills/review-work-completion/SKILL.md:153](../../../../../claude-autopilot/skills/review-work-completion/SKILL.md#L153) | R07: retain its owning procedure’s semantics. |
| OPT-117 | `--severity` | [skills/run-autopilot/references/phase-review.md:147](../../../../../claude-autopilot/skills/run-autopilot/references/phase-review.md#L147) | R02: retain its owning procedure’s semantics. |
| OPT-118 | `--short` | [skills/review-work-completion/references/output-formats.md:256](../../../../../claude-autopilot/skills/review-work-completion/references/output-formats.md#L256) | R07: retain its owning procedure’s semantics. |
| OPT-119 | `--shortstat` | [skills/work/SKILL.md:392](../../../../../claude-autopilot/skills/work/SKILL.md#L392) | R06: retain its owning procedure’s semantics. |
| OPT-120 | `--show-toplevel` | [skills/review-work-completion/SKILL.md:194](../../../../../claude-autopilot/skills/review-work-completion/SKILL.md#L194) | R07: retain its owning procedure’s semantics. |
| OPT-121 | `--signal` | [skills/run-autopilot/references/lane-solo.md:126](../../../../../claude-autopilot/skills/run-autopilot/references/lane-solo.md#L126) | R02: retain its owning procedure’s semantics. |
| OPT-122 | `--silent` | [skills/use-codex/SKILL.md:56](../../../../../claude-autopilot/skills/use-codex/SKILL.md#L56) | R21: retain its owning procedure’s semantics. |
| OPT-123 | `--since` | [skills/review-work-completion/SKILL.md:140](../../../../../claude-autopilot/skills/review-work-completion/SKILL.md#L140) | R07: retain its owning procedure’s semantics. |
| OPT-124 | `--site` | [skills/plan-tasks/SKILL.md:374](../../../../../claude-autopilot/skills/plan-tasks/SKILL.md#L374) | R04: retain its owning procedure’s semantics. |
| OPT-125 | `--snapshot` | [skills/work/references/gate-failure.md:156](../../../../../claude-autopilot/skills/work/references/gate-failure.md#L156) | R06: retain its owning procedure’s semantics. |
| OPT-126 | `--stalled` | [skills/run-autopilot/references/batch-report-format.md:22](../../../../../claude-autopilot/skills/run-autopilot/references/batch-report-format.md#L22) | R02: retain its owning procedure’s semantics. |
| OPT-127 | `--started` | [skills/fast-track/SKILL.md:646](../../../../../claude-autopilot/skills/fast-track/SKILL.md#L646) | R10: retain its owning procedure’s semantics. |
| OPT-128 | `--stat` | [skills/design-solution/SKILL.md:73](../../../../../claude-autopilot/skills/design-solution/SKILL.md#L73) | R03: retain its owning procedure’s semantics. |
| OPT-129 | `--state` | [skills/fast-track/SKILL.md:46](../../../../../claude-autopilot/skills/fast-track/SKILL.md#L46) | R10: retain its owning procedure’s semantics. |
| OPT-130 | `--strict-mcp-config` | [skills/run-autopilot/SKILL.md:171](../../../../../claude-autopilot/skills/run-autopilot/SKILL.md#L171) | R02: retain its owning procedure’s semantics. |
| OPT-131 | `--summary` | [skills/run-autopilot/references/batch-report-format.md:19](../../../../../claude-autopilot/skills/run-autopilot/references/batch-report-format.md#L19) | R02: retain its owning procedure’s semantics. |
| OPT-132 | `--task` | [skills/fast-track/SKILL.md:142](../../../../../claude-autopilot/skills/fast-track/SKILL.md#L142) | R10: retain its owning procedure’s semantics. |
| OPT-133 | `--tasks-json` | [skills/review-work-completion/SKILL.md:163](../../../../../claude-autopilot/skills/review-work-completion/SKILL.md#L163) | R07: retain its owning procedure’s semantics. |
| OPT-134 | `--tb` | [skills/work/references/adversarial-test-prompt.md:31](../../../../../claude-autopilot/skills/work/references/adversarial-test-prompt.md#L31) | R06: retain its owning procedure’s semantics. |
| OPT-135 | `--test` | [skills/work/references/gate-failure.md:252](../../../../../claude-autopilot/skills/work/references/gate-failure.md#L252) | R06: retain its owning procedure’s semantics. |
| OPT-136 | `--test-commit` | [skills/work/references/qwen-integration.md:90](../../../../../claude-autopilot/skills/work/references/qwen-integration.md#L90) | R06: retain its owning procedure’s semantics. |
| OPT-137 | `--tests-file` | [skills/work/references/qwen-integration.md:90](../../../../../claude-autopilot/skills/work/references/qwen-integration.md#L90) | R06: retain its owning procedure’s semantics. |
| OPT-138 | `--tests-only` | [skills/work/SKILL.md:334](../../../../../claude-autopilot/skills/work/SKILL.md#L334) | R06: retain its owning procedure’s semantics. |
| OPT-139 | `--tests-present` | [skills/fast-track/SKILL.md:103](../../../../../claude-autopilot/skills/fast-track/SKILL.md#L103) | R10: retain its owning procedure’s semantics. |
| OPT-140 | `--text-file` | [skills/plan-tasks/SKILL.md:258](../../../../../claude-autopilot/skills/plan-tasks/SKILL.md#L258) | R04: retain its owning procedure’s semantics. |
| OPT-141 | `--threshold` | [skills/work/references/subagent-dispatch.md:179](../../../../../claude-autopilot/skills/work/references/subagent-dispatch.md#L179) | R06: retain its owning procedure’s semantics. |
| OPT-142 | `--unset` | [skills/run-autopilot/references/state-schema.md:279](../../../../../claude-autopilot/skills/run-autopilot/references/state-schema.md#L279) | R02: retain its owning procedure’s semantics. |
| OPT-143 | `--version` | [skills/work/references/final-verification.md:16](../../../../../claude-autopilot/skills/work/references/final-verification.md#L16) | R06: retain its owning procedure’s semantics. |
| OPT-144 | `--with` | [skills/review-work-completion/SKILL.md:160](../../../../../claude-autopilot/skills/review-work-completion/SKILL.md#L160) | R07: retain its owning procedure’s semantics. |
| OPT-145 | `--work-tree` | [skills/review-work-completion/SKILL.md:190](../../../../../claude-autopilot/skills/review-work-completion/SKILL.md#L190) | R07: retain its owning procedure’s semantics. |
| OPT-146 | `--workflow-available` | [skills/fast-track/SKILL.md:104](../../../../../claude-autopilot/skills/fast-track/SKILL.md#L104) | R10: retain its owning procedure’s semantics. |
| OPT-147 | `--workspace` | [skills/work/SKILL.md:377](../../../../../claude-autopilot/skills/work/SKILL.md#L377) | R06: retain its owning procedure’s semantics. |
| OPT-148 | `--yes` | [skills/run-autopilot/references/waves.md:200](../../../../../claude-autopilot/skills/run-autopilot/references/waves.md#L200) | R02: retain its owning procedure’s semantics. |
| OPT-149 | `--yolo` | [skills/use-codex/SKILL.md:53](../../../../../claude-autopilot/skills/use-codex/SKILL.md#L53) | R21: retain its owning procedure’s semantics. |

## Statectl surface

The statectl replacement changes command names and field paths. These rows retain the documented operation, not a permanent compatibility alias.

| Row | Operation | Reason |
| --- | --- | --- |
| STATE-01 | `get <path> [--default <json>]` | R12: use OVCAQ’s sole writer or read-only renderer; preserve atomic operation intent. |
| STATE-02 | `set <path> <json>` | R12: use OVCAQ’s sole writer or read-only renderer; preserve atomic operation intent. |
| STATE-03 | `append <path> <json>` | R12: use OVCAQ’s sole writer or read-only renderer; preserve atomic operation intent. |
| STATE-04 | `del <path>` | R12: use OVCAQ’s sole writer or read-only renderer; preserve atomic operation intent. |
| STATE-05 | `decide --issue --severity --cycle --action --reason [--type]` | R12: use OVCAQ’s sole writer or read-only renderer; preserve atomic operation intent. |
| STATE-06 | `task-start <id>` | R12: use OVCAQ’s sole writer or read-only renderer; preserve atomic operation intent. |
| STATE-07 | `task-done <id> <attempt-file>` | R12: use OVCAQ’s sole writer or read-only renderer; preserve atomic operation intent. |
| STATE-08 | `append-attempt <id> <attempt-file>` | R12: use OVCAQ’s sole writer or read-only renderer; preserve atomic operation intent. |
| STATE-09 | `set-contract-card <file>` | R12: use OVCAQ’s sole writer or read-only renderer; preserve atomic operation intent. |
| STATE-10 | `task-add <file>` | R12: use OVCAQ’s sole writer or read-only renderer; preserve atomic operation intent. |
| STATE-11 | `task-set-body <id> <file>` | R12: use OVCAQ’s sole writer or read-only renderer; preserve atomic operation intent. |
| STATE-12 | `task-set-meta <id> <file>` | R12: use OVCAQ’s sole writer or read-only renderer; preserve atomic operation intent. |
| STATE-13 | `task-set-status <id> <status>` | R12: use OVCAQ’s sole writer or read-only renderer; preserve atomic operation intent. |
| STATE-14 | `tasks-clear` | R12: use OVCAQ’s sole writer or read-only renderer; preserve atomic operation intent. |
| STATE-15 | `complete-prd <prd>` | R12: use OVCAQ’s sole writer or read-only renderer; preserve atomic operation intent. |
| STATE-16 | `write-brief <file>` | R12: use OVCAQ’s sole writer or read-only renderer; preserve atomic operation intent. |

## Documented behavior sections

Fenced sample headings and non-normative design-rationale history are excluded; retired incident workarounds are not new port obligations. Repeated headings in different procedures are distinct rows. The principal matrix supplies the portability decision; these rows preserve the section-level obligations for later parity checks.

| Row | Behavior | Source | Reason |
| --- | --- | --- | --- |
| BEH-001 | What's inside | [README.md:11](../../../../../claude-autopilot/README.md#L11) | R01: Preserve the documented capability in the portable package and its adapters. |
| BEH-002 | Recursion guard | [README.md:57](../../../../../claude-autopilot/README.md#L57) | R01: Preserve the documented capability in the portable package and its adapters. |
| BEH-003 | Paths | [README.md:76](../../../../../claude-autopilot/README.md#L76) | R01: Preserve the documented capability in the portable package and its adapters. |
| BEH-004 | Install | [README.md:84](../../../../../claude-autopilot/README.md#L84) | R01: Preserve the documented capability in the portable package and its adapters. |
| BEH-005 | Update | [README.md:91](../../../../../claude-autopilot/README.md#L91) | R01: Preserve the documented capability in the portable package and its adapters. |
| BEH-006 | Alternative: install directly from this repo | [README.md:97](../../../../../claude-autopilot/README.md#L97) | R01: Preserve the documented capability in the portable package and its adapters. |
| BEH-007 | What intentionally stays out | [README.md:103](../../../../../claude-autopilot/README.md#L103) | R01: Preserve the documented capability in the portable package and its adapters. |
| BEH-008 | Development | [README.md:125](../../../../../claude-autopilot/README.md#L125) | R01: Preserve the documented capability in the portable package and its adapters. |
| BEH-009 | License | [README.md:132](../../../../../claude-autopilot/README.md#L132) | R01: Preserve the documented capability in the portable package and its adapters. |
| BEH-010 | Autoclaude role effort | [README.md:136](../../../../../claude-autopilot/README.md#L136) | R01: Preserve the documented capability in the portable package and its adapters. |
| BEH-011 | Dependencies | [skills/design-solution/SKILL.md:23](../../../../../claude-autopilot/skills/design-solution/SKILL.md#L23) | R03: Preserve design behavior while replacing host paths and reviewer dispatch. |
| BEH-012 | Inputs | [skills/design-solution/SKILL.md:37](../../../../../claude-autopilot/skills/design-solution/SKILL.md#L37) | R03: Preserve design behavior while replacing host paths and reviewer dispatch. |
| BEH-013 | Output | [skills/design-solution/SKILL.md:51](../../../../../claude-autopilot/skills/design-solution/SKILL.md#L51) | R03: Preserve design behavior while replacing host paths and reviewer dispatch. |
| BEH-014 | Rework mode | [skills/design-solution/SKILL.md:60](../../../../../claude-autopilot/skills/design-solution/SKILL.md#L60) | R03: Preserve design behavior while replacing host paths and reviewer dispatch. |
| BEH-015 | Workflow | [skills/design-solution/SKILL.md:114](../../../../../claude-autopilot/skills/design-solution/SKILL.md#L114) | R03: Preserve design behavior while replacing host paths and reviewer dispatch. |
| BEH-016 | 1. Resolve the PRD and load context | [skills/design-solution/SKILL.md:116](../../../../../claude-autopilot/skills/design-solution/SKILL.md#L116) | R03: Preserve design behavior while replacing host paths and reviewer dispatch. |
| BEH-017 | 2. Reuse sweep (before designing any new code) | [skills/design-solution/SKILL.md:122](../../../../../claude-autopilot/skills/design-solution/SKILL.md#L122) | R03: Preserve design behavior while replacing host paths and reviewer dispatch. |
| BEH-018 | 3. Write the design doc | [skills/design-solution/SKILL.md:138](../../../../../claude-autopilot/skills/design-solution/SKILL.md#L138) | R03: Preserve design behavior while replacing host paths and reviewer dispatch. |
| BEH-019 | 4. Autonomous adversarial review (up to 3 dispatches) | [skills/design-solution/SKILL.md:164](../../../../../claude-autopilot/skills/design-solution/SKILL.md#L164) | R03: Preserve design behavior while replacing host paths and reviewer dispatch. |
| BEH-020 | 5. Terminate | [skills/design-solution/SKILL.md:261](../../../../../claude-autopilot/skills/design-solution/SKILL.md#L261) | R03: Preserve design behavior while replacing host paths and reviewer dispatch. |
| BEH-021 | Exit report (always printed) | [skills/design-solution/SKILL.md:271](../../../../../claude-autopilot/skills/design-solution/SKILL.md#L271) | R03: Preserve design behavior while replacing host paths and reviewer dispatch. |
| BEH-022 | Notes | [skills/design-solution/SKILL.md:288](../../../../../claude-autopilot/skills/design-solution/SKILL.md#L288) | R03: Preserve design behavior while replacing host paths and reviewer dispatch. |
| BEH-023 | Preconditions | [skills/fast-track/SKILL.md:25](../../../../../claude-autopilot/skills/fast-track/SKILL.md#L25) | R10: Preserve card and review behavior through portable runtime interfaces. |
| BEH-024 | Card | [skills/fast-track/SKILL.md:65](../../../../../claude-autopilot/skills/fast-track/SKILL.md#L65) | R10: Preserve card and review behavior through portable runtime interfaces. |
| BEH-025 | Tests | [skills/fast-track/SKILL.md:118](../../../../../claude-autopilot/skills/fast-track/SKILL.md#L118) | R10: Preserve card and review behavior through portable runtime interfaces. |
| BEH-026 | Implement | [skills/fast-track/SKILL.md:173](../../../../../claude-autopilot/skills/fast-track/SKILL.md#L173) | R10: Preserve card and review behavior through portable runtime interfaces. |
| BEH-027 | Gates | [skills/fast-track/SKILL.md:227](../../../../../claude-autopilot/skills/fast-track/SKILL.md#L227) | R10: Preserve card and review behavior through portable runtime interfaces. |
| BEH-028 | Roster | [skills/fast-track/SKILL.md:244](../../../../../claude-autopilot/skills/fast-track/SKILL.md#L244) | R10: Preserve card and review behavior through portable runtime interfaces. |
| BEH-029 | Verify | [skills/fast-track/SKILL.md:430](../../../../../claude-autopilot/skills/fast-track/SKILL.md#L430) | R10: Preserve card and review behavior through portable runtime interfaces. |
| BEH-030 | Rework | [skills/fast-track/SKILL.md:493](../../../../../claude-autopilot/skills/fast-track/SKILL.md#L493) | R10: Preserve card and review behavior through portable runtime interfaces. |
| BEH-031 | Delta | [skills/fast-track/SKILL.md:549](../../../../../claude-autopilot/skills/fast-track/SKILL.md#L549) | R10: Preserve card and review behavior through portable runtime interfaces. |
| BEH-032 | Exit | [skills/fast-track/SKILL.md:583](../../../../../claude-autopilot/skills/fast-track/SKILL.md#L583) | R10: Preserve card and review behavior through portable runtime interfaces. |
| BEH-033 | Ledgers | [skills/fast-track/SKILL.md:628](../../../../../claude-autopilot/skills/fast-track/SKILL.md#L628) | R10: Preserve card and review behavior through portable runtime interfaces. |
| BEH-034 | Report | [skills/fast-track/SKILL.md:665](../../../../../claude-autopilot/skills/fast-track/SKILL.md#L665) | R10: Preserve card and review behavior through portable runtime interfaces. |
| BEH-035 | Dependencies | [skills/plan-tasks/SKILL.md:11](../../../../../claude-autopilot/skills/plan-tasks/SKILL.md#L11) | R04: Translate task storage and tier selection while preserving planning policy. |
| BEH-036 | Workflow | [skills/plan-tasks/SKILL.md:17](../../../../../claude-autopilot/skills/plan-tasks/SKILL.md#L17) | R04: Translate task storage and tier selection while preserving planning policy. |
| BEH-037 | 1. List available PRDs | [skills/plan-tasks/SKILL.md:19](../../../../../claude-autopilot/skills/plan-tasks/SKILL.md#L19) | R04: Translate task storage and tier selection while preserving planning policy. |
| BEH-038 | 2. Select PRD | [skills/plan-tasks/SKILL.md:33](../../../../../claude-autopilot/skills/plan-tasks/SKILL.md#L33) | R04: Translate task storage and tier selection while preserving planning policy. |
| BEH-039 | 2.5. Detect replan mode | [skills/plan-tasks/SKILL.md:39](../../../../../claude-autopilot/skills/plan-tasks/SKILL.md#L39) | R04: Translate task storage and tier selection while preserving planning policy. |
| BEH-040 | 3. Analyze PRD | [skills/plan-tasks/SKILL.md:52](../../../../../claude-autopilot/skills/plan-tasks/SKILL.md#L52) | R04: Translate task storage and tier selection while preserving planning policy. |
| BEH-041 | 4. Create tasks | [skills/plan-tasks/SKILL.md:67](../../../../../claude-autopilot/skills/plan-tasks/SKILL.md#L67) | R04: Translate task storage and tier selection while preserving planning policy. |
| BEH-042 | 4.5. Estimate per-task context budget | [skills/plan-tasks/SKILL.md:152](../../../../../claude-autopilot/skills/plan-tasks/SKILL.md#L152) | R04: Translate task storage and tier selection while preserving planning policy. |
| BEH-043 | 4.6. Split tasks (context + eligibility) | [skills/plan-tasks/SKILL.md:192](../../../../../claude-autopilot/skills/plan-tasks/SKILL.md#L192) | R04: Translate task storage and tier selection while preserving planning policy. |
| BEH-044 | Estimator caveats | [skills/plan-tasks/SKILL.md:236](../../../../../claude-autopilot/skills/plan-tasks/SKILL.md#L236) | R04: Translate task storage and tier selection while preserving planning policy. |
| BEH-045 | 4.7. Assign per-task model tier | [skills/plan-tasks/SKILL.md:244](../../../../../claude-autopilot/skills/plan-tasks/SKILL.md#L244) | R04: Translate task storage and tier selection while preserving planning policy. |
| BEH-046 | 5. Set dependencies | [skills/plan-tasks/SKILL.md:352](../../../../../claude-autopilot/skills/plan-tasks/SKILL.md#L352) | R04: Translate task storage and tier selection while preserving planning policy. |
| BEH-047 | 5.5. Check the plan against the plan-expansion gate (F5) | [skills/plan-tasks/SKILL.md:363](../../../../../claude-autopilot/skills/plan-tasks/SKILL.md#L363) | R04: Translate task storage and tier selection while preserving planning policy. |
| BEH-048 | 6. Report summary | [skills/plan-tasks/SKILL.md:393](../../../../../claude-autopilot/skills/plan-tasks/SKILL.md#L393) | R04: Translate task storage and tier selection while preserving planning policy. |
| BEH-049 | Granularity Guide | [skills/plan-tasks/SKILL.md:403](../../../../../claude-autopilot/skills/plan-tasks/SKILL.md#L403) | R04: Translate task storage and tier selection while preserving planning policy. |
| BEH-050 | Reference Files | [skills/plan-tasks/SKILL.md:413](../../../../../claude-autopilot/skills/plan-tasks/SKILL.md#L413) | R04: Translate task storage and tier selection while preserving planning policy. |
| BEH-051 | Dependencies | [skills/review-blindly/SKILL.md:13](../../../../../claude-autopilot/skills/review-blindly/SKILL.md#L13) | R08: Replace foreground-Claude execution while preserving the blind contract. |
| BEH-052 | The Process | [skills/review-blindly/SKILL.md:26](../../../../../claude-autopilot/skills/review-blindly/SKILL.md#L26) | R08: Replace foreground-Claude execution while preserving the blind contract. |
| BEH-053 | Step 1: Gather the Spec and Rubric | [skills/review-blindly/SKILL.md:28](../../../../../claude-autopilot/skills/review-blindly/SKILL.md#L28) | R08: Replace foreground-Claude execution while preserving the blind contract. |
| BEH-054 | Step 2: Run the Blind Reviewer (Sonnet, direct foreground CLI) | [skills/review-blindly/SKILL.md:38](../../../../../claude-autopilot/skills/review-blindly/SKILL.md#L38) | R08: Replace foreground-Claude execution while preserving the blind contract. |
| BEH-055 | Step 2.5: Write and Gate the Review File | [skills/review-blindly/SKILL.md:110](../../../../../claude-autopilot/skills/review-blindly/SKILL.md#L110) | R08: Replace foreground-Claude execution while preserving the blind contract. |
| BEH-056 | Step 3: Act on Findings | [skills/review-blindly/SKILL.md:122](../../../../../claude-autopilot/skills/review-blindly/SKILL.md#L122) | R08: Replace foreground-Claude execution while preserving the blind contract. |
| BEH-057 | Integration | [skills/review-blindly/SKILL.md:129](../../../../../claude-autopilot/skills/review-blindly/SKILL.md#L129) | R08: Replace foreground-Claude execution while preserving the blind contract. |
| BEH-058 | Common Mistakes | [skills/review-blindly/SKILL.md:136](../../../../../claude-autopilot/skills/review-blindly/SKILL.md#L136) | R08: Replace foreground-Claude execution while preserving the blind contract. |
| BEH-059 | Red Flags | [skills/review-blindly/SKILL.md:146](../../../../../claude-autopilot/skills/review-blindly/SKILL.md#L146) | R08: Replace foreground-Claude execution while preserving the blind contract. |
| BEH-060 | Prerequisites | [skills/review-plan/SKILL.md:10](../../../../../claude-autopilot/skills/review-plan/SKILL.md#L10) | R09: Use the host plan and question interfaces without changing review dimensions. |
| BEH-061 | Review Dimensions | [skills/review-plan/SKILL.md:14](../../../../../claude-autopilot/skills/review-plan/SKILL.md#L14) | R09: Use the host plan and question interfaces without changing review dimensions. |
| BEH-062 | Output Format | [skills/review-plan/SKILL.md:29](../../../../../claude-autopilot/skills/review-plan/SKILL.md#L29) | R09: Use the host plan and question interfaces without changing review dimensions. |
| BEH-063 | Guidelines | [skills/review-plan/SKILL.md:43](../../../../../claude-autopilot/skills/review-plan/SKILL.md#L43) | R09: Use the host plan and question interfaces without changing review dimensions. |
| BEH-064 | Reference Files | [skills/review-plan/SKILL.md:51](../../../../../claude-autopilot/skills/review-plan/SKILL.md#L51) | R09: Use the host plan and question interfaces without changing review dimensions. |
| BEH-065 | What This Does | [skills/review-work-completion/SKILL.md:22](../../../../../claude-autopilot/skills/review-work-completion/SKILL.md#L22) | R07: Preserve review rules through isolated jobs and authoritative completion gates. |
| BEH-066 | Dependencies | [skills/review-work-completion/SKILL.md:32](../../../../../claude-autopilot/skills/review-work-completion/SKILL.md#L32) | R07: Preserve review rules through isolated jobs and authoritative completion gates. |
| BEH-067 | Reviewers | [skills/review-work-completion/SKILL.md:49](../../../../../claude-autopilot/skills/review-work-completion/SKILL.md#L49) | R07: Preserve review rules through isolated jobs and authoritative completion gates. |
| BEH-068 | Workflow | [skills/review-work-completion/SKILL.md:60](../../../../../claude-autopilot/skills/review-work-completion/SKILL.md#L60) | R07: Preserve review rules through isolated jobs and authoritative completion gates. |
| BEH-069 | 1. Validate prerequisites | [skills/review-work-completion/SKILL.md:62](../../../../../claude-autopilot/skills/review-work-completion/SKILL.md#L62) | R07: Preserve review rules through isolated jobs and authoritative completion gates. |
| BEH-070 | 2. Check task status | [skills/review-work-completion/SKILL.md:115](../../../../../claude-autopilot/skills/review-work-completion/SKILL.md#L115) | R07: Preserve review rules through isolated jobs and authoritative completion gates. |
| BEH-071 | 3. Gather context | [skills/review-work-completion/SKILL.md:134](../../../../../claude-autopilot/skills/review-work-completion/SKILL.md#L134) | R07: Preserve review rules through isolated jobs and authoritative completion gates. |
| BEH-072 | 4. Prepare agent prompts | [skills/review-work-completion/SKILL.md:197](../../../../../claude-autopilot/skills/review-work-completion/SKILL.md#L197) | R07: Preserve review rules through isolated jobs and authoritative completion gates. |
| BEH-073 | 5. Run agent review | [skills/review-work-completion/SKILL.md:256](../../../../../claude-autopilot/skills/review-work-completion/SKILL.md#L256) | R07: Preserve review rules through isolated jobs and authoritative completion gates. |
| BEH-074 | 6. Consolidate findings | [skills/review-work-completion/SKILL.md:348](../../../../../claude-autopilot/skills/review-work-completion/SKILL.md#L348) | R07: Preserve review rules through isolated jobs and authoritative completion gates. |
| BEH-075 | 7. Follow-up tasks (removed, PRD 00249) | [skills/review-work-completion/SKILL.md:411](../../../../../claude-autopilot/skills/review-work-completion/SKILL.md#L411) | R07: Preserve review rules through isolated jobs and authoritative completion gates. |
| BEH-076 | 8. Save review file | [skills/review-work-completion/SKILL.md:415](../../../../../claude-autopilot/skills/review-work-completion/SKILL.md#L415) | R07: Preserve review rules through isolated jobs and authoritative completion gates. |
| BEH-077 | Dependencies | [skills/run-autopilot/SKILL.md:30](../../../../../claude-autopilot/skills/run-autopilot/SKILL.md#L30) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-078 | Execution Model | [skills/run-autopilot/SKILL.md:49](../../../../../claude-autopilot/skills/run-autopilot/SKILL.md#L49) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-079 | Entry Points | [skills/run-autopilot/SKILL.md:55](../../../../../claude-autopilot/skills/run-autopilot/SKILL.md#L55) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-080 | Gate Dispatch | [skills/run-autopilot/SKILL.md:68](../../../../../claude-autopilot/skills/run-autopilot/SKILL.md#L68) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-081 | State Management | [skills/run-autopilot/SKILL.md:83](../../../../../claude-autopilot/skills/run-autopilot/SKILL.md#L83) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-082 | Retention | [skills/run-autopilot/SKILL.md:107](../../../../../claude-autopilot/skills/run-autopilot/SKILL.md#L107) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-083 | Resuming | [skills/run-autopilot/SKILL.md:121](../../../../../claude-autopilot/skills/run-autopilot/SKILL.md#L121) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-084 | Operator runbook (unattended batches) | [skills/run-autopilot/SKILL.md:127](../../../../../claude-autopilot/skills/run-autopilot/SKILL.md#L127) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-085 | Task Counts | [skills/run-autopilot/SKILL.md:148](../../../../../claude-autopilot/skills/run-autopilot/SKILL.md#L148) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-086 | Live Dashboard | [skills/run-autopilot/SKILL.md:152](../../../../../claude-autopilot/skills/run-autopilot/SKILL.md#L152) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-087 | Phase Banners | [skills/run-autopilot/SKILL.md:156](../../../../../claude-autopilot/skills/run-autopilot/SKILL.md#L156) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-088 | Session Loop | [skills/run-autopilot/SKILL.md:169](../../../../../claude-autopilot/skills/run-autopilot/SKILL.md#L169) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-089 | Session handoff procedure (canonical — gate files invoke it by site name) | [skills/run-autopilot/SKILL.md:196](../../../../../claude-autopilot/skills/run-autopilot/SKILL.md#L196) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-090 | Contract card (compaction re-anchor) | [skills/run-autopilot/SKILL.md:215](../../../../../claude-autopilot/skills/run-autopilot/SKILL.md#L215) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-091 | Loop Detection | [skills/run-autopilot/SKILL.md:230](../../../../../claude-autopilot/skills/run-autopilot/SKILL.md#L230) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-092 | Phase 0 invariants (selection — full procedure: `references/phase-build.md`) | [skills/run-autopilot/SKILL.md:249](../../../../../claude-autopilot/skills/run-autopilot/SKILL.md#L249) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-093 | Phase 3 invariants (work — full procedure: `references/phase-build.md`) | [skills/run-autopilot/SKILL.md:277](../../../../../claude-autopilot/skills/run-autopilot/SKILL.md#L277) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-094 | Phase 9 invariants (completion — full procedure: `references/phase-done.md`) | [skills/run-autopilot/SKILL.md:281](../../../../../claude-autopilot/skills/run-autopilot/SKILL.md#L281) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-095 | Design-gate invariant: empty-review-log gate (Phase 1.5 — full procedure: `references/phase-build.md`) | [skills/run-autopilot/SKILL.md:287](../../../../../claude-autopilot/skills/run-autopilot/SKILL.md#L287) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-096 | Shell Command Rules | [skills/run-autopilot/SKILL.md:300](../../../../../claude-autopilot/skills/run-autopilot/SKILL.md#L300) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-097 | Error Handling | [skills/run-autopilot/SKILL.md:308](../../../../../claude-autopilot/skills/run-autopilot/SKILL.md#L308) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-098 | Reference Files | [skills/run-autopilot/SKILL.md:345](../../../../../claude-autopilot/skills/run-autopilot/SKILL.md#L345) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-099 | Dependencies | [skills/use-codex/SKILL.md:21](../../../../../claude-autopilot/skills/use-codex/SKILL.md#L21) | R21: Keep Codex backend semantics in an explicit host/job adapter. |
| BEH-100 | Dispatch Contract (shared) | [skills/use-codex/SKILL.md:29](../../../../../claude-autopilot/skills/use-codex/SKILL.md#L29) | R21: Keep Codex backend semantics in an explicit host/job adapter. |
| BEH-101 | Multiplier Policy (copilot backend only) | [skills/use-codex/SKILL.md:35](../../../../../claude-autopilot/skills/use-codex/SKILL.md#L35) | R21: Keep Codex backend semantics in an explicit host/job adapter. |
| BEH-102 | Running a Task | [skills/use-codex/SKILL.md:44](../../../../../claude-autopilot/skills/use-codex/SKILL.md#L44) | R21: Keep Codex backend semantics in an explicit host/job adapter. |
| BEH-103 | Quick Reference (helper flags) | [skills/use-codex/SKILL.md:61](../../../../../claude-autopilot/skills/use-codex/SKILL.md#L61) | R21: Keep Codex backend semantics in an explicit host/job adapter. |
| BEH-104 | Helper Script | [skills/use-codex/SKILL.md:71](../../../../../claude-autopilot/skills/use-codex/SKILL.md#L71) | R21: Keep Codex backend semantics in an explicit host/job adapter. |
| BEH-105 | Hook doctor | [skills/use-codex/SKILL.md:92](../../../../../claude-autopilot/skills/use-codex/SKILL.md#L92) | R21: Keep Codex backend semantics in an explicit host/job adapter. |
| BEH-106 | Dependencies | [skills/use-gemini/SKILL.md:18](../../../../../claude-autopilot/skills/use-gemini/SKILL.md#L18) | R21: Keep Gemini backend semantics in an explicit host/job adapter. |
| BEH-107 | Dispatch Contract (shared) | [skills/use-gemini/SKILL.md:26](../../../../../claude-autopilot/skills/use-gemini/SKILL.md#L26) | R21: Keep Gemini backend semantics in an explicit host/job adapter. |
| BEH-108 | Model Selection | [skills/use-gemini/SKILL.md:46](../../../../../claude-autopilot/skills/use-gemini/SKILL.md#L46) | R21: Keep Gemini backend semantics in an explicit host/job adapter. |
| BEH-109 | Check the pin (opt-in, live) | [skills/use-gemini/SKILL.md:62](../../../../../claude-autopilot/skills/use-gemini/SKILL.md#L62) | R21: Keep Gemini backend semantics in an explicit host/job adapter. |
| BEH-110 | Exit codes and output | [skills/use-gemini/SKILL.md:83](../../../../../claude-autopilot/skills/use-gemini/SKILL.md#L83) | R21: Keep Gemini backend semantics in an explicit host/job adapter. |
| BEH-111 | Running a Task | [skills/use-gemini/SKILL.md:101](../../../../../claude-autopilot/skills/use-gemini/SKILL.md#L101) | R21: Keep Gemini backend semantics in an explicit host/job adapter. |
| BEH-112 | Quick Reference | [skills/use-gemini/SKILL.md:116](../../../../../claude-autopilot/skills/use-gemini/SKILL.md#L116) | R21: Keep Gemini backend semantics in an explicit host/job adapter. |
| BEH-113 | Helper Script | [skills/use-gemini/SKILL.md:130](../../../../../claude-autopilot/skills/use-gemini/SKILL.md#L130) | R21: Keep Gemini backend semantics in an explicit host/job adapter. |
| BEH-114 | Dependencies | [skills/use-sonnet/SKILL.md:11](../../../../../claude-autopilot/skills/use-sonnet/SKILL.md#L11) | R21: Keep Claude backend semantics in an explicit host/job adapter. |
| BEH-115 | Dispatch Contract (shared) | [skills/use-sonnet/SKILL.md:21](../../../../../claude-autopilot/skills/use-sonnet/SKILL.md#L21) | R21: Keep Claude backend semantics in an explicit host/job adapter. |
| BEH-116 | Usage-limit banner (claude backend only) | [skills/use-sonnet/SKILL.md:25](../../../../../claude-autopilot/skills/use-sonnet/SKILL.md#L25) | R21: Keep Claude backend semantics in an explicit host/job adapter. |
| BEH-117 | Model Policy | [skills/use-sonnet/SKILL.md:33](../../../../../claude-autopilot/skills/use-sonnet/SKILL.md#L33) | R21: Keep Claude backend semantics in an explicit host/job adapter. |
| BEH-118 | Running a Task | [skills/use-sonnet/SKILL.md:38](../../../../../claude-autopilot/skills/use-sonnet/SKILL.md#L38) | R21: Keep Claude backend semantics in an explicit host/job adapter. |
| BEH-119 | Quick Reference | [skills/use-sonnet/SKILL.md:53](../../../../../claude-autopilot/skills/use-sonnet/SKILL.md#L53) | R21: Keep Claude backend semantics in an explicit host/job adapter. |
| BEH-120 | Helper Script | [skills/use-sonnet/SKILL.md:66](../../../../../claude-autopilot/skills/use-sonnet/SKILL.md#L66) | R21: Keep Claude backend semantics in an explicit host/job adapter. |
| BEH-121 | Dependencies | [skills/work/SKILL.md:18](../../../../../claude-autopilot/skills/work/SKILL.md#L18) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-122 | CRITICAL: Never Ask the User to Run Commands | [skills/work/SKILL.md:40](../../../../../claude-autopilot/skills/work/SKILL.md#L40) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-123 | CRITICAL: One Task at a Time | [skills/work/SKILL.md:49](../../../../../claude-autopilot/skills/work/SKILL.md#L49) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-124 | Subagent Dispatch Budget and Watchdog | [skills/work/SKILL.md:77](../../../../../claude-autopilot/skills/work/SKILL.md#L77) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-125 | Per-task model dispatch | [skills/work/SKILL.md:85](../../../../../claude-autopilot/skills/work/SKILL.md#L85) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-126 | Assumptions footer | [skills/work/SKILL.md:107](../../../../../claude-autopilot/skills/work/SKILL.md#L107) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-127 | Dispatch prologue | [skills/work/SKILL.md:121](../../../../../claude-autopilot/skills/work/SKILL.md#L121) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-128 | Passing values to render_prompt.py | [skills/work/SKILL.md:127](../../../../../claude-autopilot/skills/work/SKILL.md#L127) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-129 | Attempt logging | [skills/work/SKILL.md:135](../../../../../claude-autopilot/skills/work/SKILL.md#L135) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-130 | Implementor Selection | [skills/work/SKILL.md:144](../../../../../claude-autopilot/skills/work/SKILL.md#L144) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-131 | Dashboard State Sync | [skills/work/SKILL.md:152](../../../../../claude-autopilot/skills/work/SKILL.md#L152) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-132 | Workflow | [skills/work/SKILL.md:156](../../../../../claude-autopilot/skills/work/SKILL.md#L156) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-133 | 1. Get pending tasks | [skills/work/SKILL.md:158](../../../../../claude-autopilot/skills/work/SKILL.md#L158) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-134 | 1.5. Rework-mode task filter | [skills/work/SKILL.md:168](../../../../../claude-autopilot/skills/work/SKILL.md#L168) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-135 | 2. Claim and start task | [skills/work/SKILL.md:179](../../../../../claude-autopilot/skills/work/SKILL.md#L179) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-136 | 2.5. Load project context | [skills/work/SKILL.md:195](../../../../../claude-autopilot/skills/work/SKILL.md#L195) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-137 | 2.7. Write tests first (Tess - test author) | [skills/work/SKILL.md:207](../../../../../claude-autopilot/skills/work/SKILL.md#L207) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-138 | 2.8. Test quality gate (main session) | [skills/work/SKILL.md:234](../../../../../claude-autopilot/skills/work/SKILL.md#L234) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-139 | 2.85. Commit tests | [skills/work/SKILL.md:240](../../../../../claude-autopilot/skills/work/SKILL.md#L240) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-140 | 2.9. Adversarial validation (Devon - devil's advocate) | [skills/work/SKILL.md:248](../../../../../claude-autopilot/skills/work/SKILL.md#L248) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-141 | 2.95. Red-check — watch the tests fail | [skills/work/SKILL.md:266](../../../../../claude-autopilot/skills/work/SKILL.md#L266) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-142 | 3. Implement against tests (Ivan - implementor) | [skills/work/SKILL.md:272](../../../../../claude-autopilot/skills/work/SKILL.md#L272) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-143 | 4. Handle result | [skills/work/SKILL.md:332](../../../../../claude-autopilot/skills/work/SKILL.md#L332) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-144 | 4.2. Infrastructure-failure circuit breaker | [skills/work/SKILL.md:336](../../../../../claude-autopilot/skills/work/SKILL.md#L336) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-145 | 4.5. Debug on error | [skills/work/SKILL.md:342](../../../../../claude-autopilot/skills/work/SKILL.md#L342) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-146 | 5. Commit changes | [skills/work/SKILL.md:346](../../../../../claude-autopilot/skills/work/SKILL.md#L346) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-147 | 5.5. Verify THIS task's tests pass | [skills/work/SKILL.md:369](../../../../../claude-autopilot/skills/work/SKILL.md#L369) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-148 | 5.6. Self-deslop pre-commit pass | [skills/work/SKILL.md:385](../../../../../claude-autopilot/skills/work/SKILL.md#L385) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-149 | 5.65. Per-task style limits | [skills/work/SKILL.md:406](../../../../../claude-autopilot/skills/work/SKILL.md#L406) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-150 | 5.7. Per-task code review | [skills/work/SKILL.md:410](../../../../../claude-autopilot/skills/work/SKILL.md#L410) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-151 | 6. Mark complete and sync | [skills/work/SKILL.md:441](../../../../../claude-autopilot/skills/work/SKILL.md#L441) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-152 | 6.5. Task-boundary handoff check | [skills/work/SKILL.md:454](../../../../../claude-autopilot/skills/work/SKILL.md#L454) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-153 | 7. Final verification (once per work phase) | [skills/work/SKILL.md:460](../../../../../claude-autopilot/skills/work/SKILL.md#L460) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-154 | Reference Files | [skills/work/SKILL.md:470](../../../../../claude-autopilot/skills/work/SKILL.md#L470) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-155 | Tess: the test author | [skills/fast-track/references/lane-dispatch.md:19](../../../../../claude-autopilot/skills/fast-track/references/lane-dispatch.md#L19) | R10: Preserve card and review behavior through portable runtime interfaces. |
| BEH-156 | Ivan: the implementor | [skills/fast-track/references/lane-dispatch.md:46](../../../../../claude-autopilot/skills/fast-track/references/lane-dispatch.md#L46) | R10: Preserve card and review behavior through portable runtime interfaces. |
| BEH-157 | The roster: five lenses in one message | [skills/fast-track/references/lane-dispatch.md:81](../../../../../claude-autopilot/skills/fast-track/references/lane-dispatch.md#L81) | R10: Preserve card and review behavior through portable runtime interfaces. |
| BEH-158 | Consensus: fanout, or alice | [skills/fast-track/references/lane-dispatch.md:102](../../../../../claude-autopilot/skills/fast-track/references/lane-dispatch.md#L102) | R10: Preserve card and review behavior through portable runtime interfaces. |
| BEH-159 | Blake: the blind lens | [skills/fast-track/references/lane-dispatch.md:131](../../../../../claude-autopilot/skills/fast-track/references/lane-dispatch.md#L131) | R10: Preserve card and review behavior through portable runtime interfaces. |
| BEH-160 | Eve: the doubt lens | [skills/fast-track/references/lane-dispatch.md:150](../../../../../claude-autopilot/skills/fast-track/references/lane-dispatch.md#L150) | R10: Preserve card and review behavior through portable runtime interfaces. |
| BEH-161 | Bob: codex | [skills/fast-track/references/lane-dispatch.md:170](../../../../../claude-autopilot/skills/fast-track/references/lane-dispatch.md#L170) | R10: Preserve card and review behavior through portable runtime interfaces. |
| BEH-162 | Carl: gemini | [skills/fast-track/references/lane-dispatch.md:199](../../../../../claude-autopilot/skills/fast-track/references/lane-dispatch.md#L199) | R10: Preserve card and review behavior through portable runtime interfaces. |
| BEH-163 | Victor: adversarial verification | [skills/fast-track/references/lane-dispatch.md:215](../../../../../claude-autopilot/skills/fast-track/references/lane-dispatch.md#L215) | R10: Preserve card and review behavior through portable runtime interfaces. |
| BEH-164 | Delta: the review after a rework | [skills/fast-track/references/lane-dispatch.md:243](../../../../../claude-autopilot/skills/fast-track/references/lane-dispatch.md#L243) | R10: Preserve card and review behavior through portable runtime interfaces. |
| BEH-165 | Close every row | [skills/fast-track/references/lane-dispatch.md:266](../../../../../claude-autopilot/skills/fast-track/references/lane-dispatch.md#L266) | R10: Preserve card and review behavior through portable runtime interfaces. |
| BEH-166 | The item row | [skills/fast-track/references/lane-dispatch.md:278](../../../../../claude-autopilot/skills/fast-track/references/lane-dispatch.md#L278) | R10: Preserve card and review behavior through portable runtime interfaces. |
| BEH-167 | Frontmatter | [skills/fast-track/references/spec-card.md:22](../../../../../claude-autopilot/skills/fast-track/references/spec-card.md#L22) | R10: Preserve card and review behavior through portable runtime interfaces. |
| BEH-168 | Sections | [skills/fast-track/references/spec-card.md:37](../../../../../claude-autopilot/skills/fast-track/references/spec-card.md#L37) | R10: Preserve card and review behavior through portable runtime interfaces. |
| BEH-169 | A worked card | [skills/fast-track/references/spec-card.md:56](../../../../../claude-autopilot/skills/fast-track/references/spec-card.md#L56) | R10: Preserve card and review behavior through portable runtime interfaces. |
| BEH-170 | An empty `## Tests` section | [skills/fast-track/references/spec-card.md:100](../../../../../claude-autopilot/skills/fast-track/references/spec-card.md#L100) | R10: Preserve card and review behavior through portable runtime interfaces. |
| BEH-171 | Refusals | [skills/fast-track/references/spec-card.md:108](../../../../../claude-autopilot/skills/fast-track/references/spec-card.md#L108) | R10: Preserve card and review behavior through portable runtime interfaces. |
| BEH-174 | Example 1: Database Model | [skills/plan-tasks/references/task-examples.md:5](../../../../../claude-autopilot/skills/plan-tasks/references/task-examples.md#L5) | R04: Translate task storage and tier selection while preserving planning policy. |
| BEH-175 | Bad | [skills/plan-tasks/references/task-examples.md:7](../../../../../claude-autopilot/skills/plan-tasks/references/task-examples.md#L7) | R04: Translate task storage and tier selection while preserving planning policy. |
| BEH-176 | Good | [skills/plan-tasks/references/task-examples.md:13](../../../../../claude-autopilot/skills/plan-tasks/references/task-examples.md#L13) | R04: Translate task storage and tier selection while preserving planning policy. |
| BEH-177 | Example 2: API Endpoint | [skills/plan-tasks/references/task-examples.md:29](../../../../../claude-autopilot/skills/plan-tasks/references/task-examples.md#L29) | R04: Translate task storage and tier selection while preserving planning policy. |
| BEH-178 | Bad | [skills/plan-tasks/references/task-examples.md:31](../../../../../claude-autopilot/skills/plan-tasks/references/task-examples.md#L31) | R04: Translate task storage and tier selection while preserving planning policy. |
| BEH-179 | Good | [skills/plan-tasks/references/task-examples.md:37](../../../../../claude-autopilot/skills/plan-tasks/references/task-examples.md#L37) | R04: Translate task storage and tier selection while preserving planning policy. |
| BEH-180 | Example 3: Refactoring | [skills/plan-tasks/references/task-examples.md:55](../../../../../claude-autopilot/skills/plan-tasks/references/task-examples.md#L55) | R04: Translate task storage and tier selection while preserving planning policy. |
| BEH-181 | Bad | [skills/plan-tasks/references/task-examples.md:57](../../../../../claude-autopilot/skills/plan-tasks/references/task-examples.md#L57) | R04: Translate task storage and tier selection while preserving planning policy. |
| BEH-182 | Good | [skills/plan-tasks/references/task-examples.md:63](../../../../../claude-autopilot/skills/plan-tasks/references/task-examples.md#L63) | R04: Translate task storage and tier selection while preserving planning policy. |
| BEH-183 | Example 4: Bug Fix | [skills/plan-tasks/references/task-examples.md:78](../../../../../claude-autopilot/skills/plan-tasks/references/task-examples.md#L78) | R04: Translate task storage and tier selection while preserving planning policy. |
| BEH-184 | Bad | [skills/plan-tasks/references/task-examples.md:80](../../../../../claude-autopilot/skills/plan-tasks/references/task-examples.md#L80) | R04: Translate task storage and tier selection while preserving planning policy. |
| BEH-185 | Good | [skills/plan-tasks/references/task-examples.md:86](../../../../../claude-autopilot/skills/plan-tasks/references/task-examples.md#L86) | R04: Translate task storage and tier selection while preserving planning policy. |
| BEH-186 | Example 5: Separable vs Coupled Splits (Step 4.6 Eligibility Trigger) | [skills/plan-tasks/references/task-examples.md:100](../../../../../claude-autopilot/skills/plan-tasks/references/task-examples.md#L100) | R04: Translate task storage and tier selection while preserving planning policy. |
| BEH-187 | Separable — independently gated one-file pieces | [skills/plan-tasks/references/task-examples.md:107](../../../../../claude-autopilot/skills/plan-tasks/references/task-examples.md#L107) | R04: Translate task storage and tier selection while preserving planning policy. |
| BEH-188 | Coupled — stays whole and routes above Qwen | [skills/plan-tasks/references/task-examples.md:119](../../../../../claude-autopilot/skills/plan-tasks/references/task-examples.md#L119) | R04: Translate task storage and tier selection while preserving planning policy. |
| BEH-189 | Rules | [skills/review-blindly/references/rubric.md:11](../../../../../claude-autopilot/skills/review-blindly/references/rubric.md#L11) | R08: Replace foreground-Claude execution while preserving the blind contract. |
| BEH-190 | Spec Compliance | [skills/review-blindly/references/rubric.md:13](../../../../../claude-autopilot/skills/review-blindly/references/rubric.md#L13) | R08: Replace foreground-Claude execution while preserving the blind contract. |
| BEH-191 | Scope Creep | [skills/review-blindly/references/rubric.md:25](../../../../../claude-autopilot/skills/review-blindly/references/rubric.md#L25) | R08: Replace foreground-Claude execution while preserving the blind contract. |
| BEH-192 | Security | [skills/review-blindly/references/rubric.md:33](../../../../../claude-autopilot/skills/review-blindly/references/rubric.md#L33) | R08: Replace foreground-Claude execution while preserving the blind contract. |
| BEH-193 | Data Safety | [skills/review-blindly/references/rubric.md:41](../../../../../claude-autopilot/skills/review-blindly/references/rubric.md#L41) | R08: Replace foreground-Claude execution while preserving the blind contract. |
| BEH-194 | Acceptance Criteria | [skills/review-blindly/references/rubric.md:49](../../../../../claude-autopilot/skills/review-blindly/references/rubric.md#L49) | R08: Replace foreground-Claude execution while preserving the blind contract. |
| BEH-195 | Out-of-Scope | [skills/review-blindly/references/rubric.md:57](../../../../../claude-autopilot/skills/review-blindly/references/rubric.md#L57) | R08: Replace foreground-Claude execution while preserving the blind contract. |
| BEH-196 | Completeness | [skills/review-plan/references/question-examples.md:5](../../../../../claude-autopilot/skills/review-plan/references/question-examples.md#L5) | R09: Use the host plan and question interfaces without changing review dimensions. |
| BEH-197 | Missing error handling | [skills/review-plan/references/question-examples.md:7](../../../../../claude-autopilot/skills/review-plan/references/question-examples.md#L7) | R09: Use the host plan and question interfaces without changing review dimensions. |
| BEH-198 | Missing edge cases | [skills/review-plan/references/question-examples.md:24](../../../../../claude-autopilot/skills/review-plan/references/question-examples.md#L24) | R09: Use the host plan and question interfaces without changing review dimensions. |
| BEH-199 | Technical Feasibility | [skills/review-plan/references/question-examples.md:41](../../../../../claude-autopilot/skills/review-plan/references/question-examples.md#L41) | R09: Use the host plan and question interfaces without changing review dimensions. |
| BEH-200 | Performance concern | [skills/review-plan/references/question-examples.md:43](../../../../../claude-autopilot/skills/review-plan/references/question-examples.md#L43) | R09: Use the host plan and question interfaces without changing review dimensions. |
| BEH-201 | Architecture concern | [skills/review-plan/references/question-examples.md:59](../../../../../claude-autopilot/skills/review-plan/references/question-examples.md#L59) | R09: Use the host plan and question interfaces without changing review dimensions. |
| BEH-202 | Implementation Clarity | [skills/review-plan/references/question-examples.md:74](../../../../../claude-autopilot/skills/review-plan/references/question-examples.md#L74) | R09: Use the host plan and question interfaces without changing review dimensions. |
| BEH-203 | Ambiguous requirement | [skills/review-plan/references/question-examples.md:76](../../../../../claude-autopilot/skills/review-plan/references/question-examples.md#L76) | R09: Use the host plan and question interfaces without changing review dimensions. |
| BEH-204 | Missing decision | [skills/review-plan/references/question-examples.md:91](../../../../../claude-autopilot/skills/review-plan/references/question-examples.md#L91) | R09: Use the host plan and question interfaces without changing review dimensions. |
| BEH-205 | Dependencies | [skills/review-plan/references/question-examples.md:106](../../../../../claude-autopilot/skills/review-plan/references/question-examples.md#L106) | R09: Use the host plan and question interfaces without changing review dimensions. |
| BEH-206 | External dependency risk | [skills/review-plan/references/question-examples.md:108](../../../../../claude-autopilot/skills/review-plan/references/question-examples.md#L108) | R09: Use the host plan and question interfaces without changing review dimensions. |
| BEH-207 | Asking Good Questions | [skills/review-plan/references/question-examples.md:123](../../../../../claude-autopilot/skills/review-plan/references/question-examples.md#L123) | R09: Use the host plan and question interfaces without changing review dimensions. |
| BEH-208 | Alice (Claude subagent) | [skills/review-work-completion/references/agent-invocation.md:8](../../../../../claude-autopilot/skills/review-work-completion/references/agent-invocation.md#L8) | R07: Preserve review rules through isolated jobs and authoritative completion gates. |
| BEH-209 | Bob (Codex) | [skills/review-work-completion/references/agent-invocation.md:25](../../../../../claude-autopilot/skills/review-work-completion/references/agent-invocation.md#L25) | R07: Preserve review rules through isolated jobs and authoritative completion gates. |
| BEH-210 | Carl (Gemini) | [skills/review-work-completion/references/agent-invocation.md:51](../../../../../claude-autopilot/skills/review-work-completion/references/agent-invocation.md#L51) | R07: Preserve review rules through isolated jobs and authoritative completion gates. |
| BEH-211 | Blake: Test gate | [skills/review-work-completion/references/agent-invocation.md:75](../../../../../claude-autopilot/skills/review-work-completion/references/agent-invocation.md#L75) | R07: Preserve review rules through isolated jobs and authoritative completion gates. |
| BEH-212 | Blake: Filesystem notes | [skills/review-work-completion/references/agent-invocation.md:87](../../../../../claude-autopilot/skills/review-work-completion/references/agent-invocation.md#L87) | R07: Preserve review rules through isolated jobs and authoritative completion gates. |
| BEH-213 | Eve (Fable 5) | [skills/review-work-completion/references/agent-invocation.md:114](../../../../../claude-autopilot/skills/review-work-completion/references/agent-invocation.md#L114) | R07: Preserve review rules through isolated jobs and authoritative completion gates. |
| BEH-214 | File format | [skills/review-work-completion/references/agent-registry.md:8](../../../../../claude-autopilot/skills/review-work-completion/references/agent-registry.md#L8) | R07: Preserve review rules through isolated jobs and authoritative completion gates. |
| BEH-215 | Tool sets | [skills/review-work-completion/references/agent-registry.md:22](../../../../../claude-autopilot/skills/review-work-completion/references/agent-registry.md#L22) | R07: Preserve review rules through isolated jobs and authoritative completion gates. |
| BEH-216 | No personal paths in bodies | [skills/review-work-completion/references/agent-registry.md:63](../../../../../claude-autopilot/skills/review-work-completion/references/agent-registry.md#L63) | R07: Preserve review rules through isolated jobs and authoritative completion gates. |
| BEH-217 | Dispatch mechanism | [skills/review-work-completion/references/agent-registry.md:98](../../../../../claude-autopilot/skills/review-work-completion/references/agent-registry.md#L98) | R07: Preserve review rules through isolated jobs and authoritative completion gates. |
| BEH-218 | Fail-closed | [skills/review-work-completion/references/agent-registry.md:161](../../../../../claude-autopilot/skills/review-work-completion/references/agent-registry.md#L161) | R07: Preserve review rules through isolated jobs and authoritative completion gates. |
| BEH-219 | The roster | [skills/review-work-completion/references/agent-registry.md:170](../../../../../claude-autopilot/skills/review-work-completion/references/agent-registry.md#L170) | R07: Preserve review rules through isolated jobs and authoritative completion gates. |
| BEH-237 | Contents | [skills/review-work-completion/references/output-formats.md:3](../../../../../claude-autopilot/skills/review-work-completion/references/output-formats.md#L3) | R07: Preserve review rules through isolated jobs and authoritative completion gates. |
| BEH-238 | Agent Output Format (Single Source of Truth) | [skills/review-work-completion/references/output-formats.md:16](../../../../../claude-autopilot/skills/review-work-completion/references/output-formats.md#L16) | R07: Preserve review rules through isolated jobs and authoritative completion gates. |
| BEH-239 | Per-Rule Verdict Format | [skills/review-work-completion/references/output-formats.md:39](../../../../../claude-autopilot/skills/review-work-completion/references/output-formats.md#L39) | R07: Preserve review rules through isolated jobs and authoritative completion gates. |
| BEH-240 | Consolidation Rules | [skills/review-work-completion/references/output-formats.md:77](../../../../../claude-autopilot/skills/review-work-completion/references/output-formats.md#L77) | R07: Preserve review rules through isolated jobs and authoritative completion gates. |
| BEH-241 | Consolidated Findings Table | [skills/review-work-completion/references/output-formats.md:88](../../../../../claude-autopilot/skills/review-work-completion/references/output-formats.md#L88) | R07: Preserve review rules through isolated jobs and authoritative completion gates. |
| BEH-242 | Issue Documentation Format | [skills/review-work-completion/references/output-formats.md:105](../../../../../claude-autopilot/skills/review-work-completion/references/output-formats.md#L105) | R07: Preserve review rules through isolated jobs and authoritative completion gates. |
| BEH-243 | Task Description Format | [skills/review-work-completion/references/output-formats.md:115](../../../../../claude-autopilot/skills/review-work-completion/references/output-formats.md#L115) | R07: Preserve review rules through isolated jobs and authoritative completion gates. |
| BEH-244 | Review Summary Format | [skills/review-work-completion/references/output-formats.md:132](../../../../../claude-autopilot/skills/review-work-completion/references/output-formats.md#L132) | R07: Preserve review rules through isolated jobs and authoritative completion gates. |
| BEH-245 | Zero Issues Handling | [skills/review-work-completion/references/output-formats.md:162](../../../../../claude-autopilot/skills/review-work-completion/references/output-formats.md#L162) | R07: Preserve review rules through isolated jobs and authoritative completion gates. |
| BEH-246 | Verification-check queue | [skills/review-work-completion/references/output-formats.md:170](../../../../../claude-autopilot/skills/review-work-completion/references/output-formats.md#L170) | R07: Preserve review rules through isolated jobs and authoritative completion gates. |
| BEH-247 | Review File Format | [skills/review-work-completion/references/output-formats.md:245](../../../../../claude-autopilot/skills/review-work-completion/references/output-formats.md#L245) | R07: Preserve review rules through isolated jobs and authoritative completion gates. |
| BEH-248 | When to Retry | [skills/review-work-completion/references/retry-policy.md:3](../../../../../claude-autopilot/skills/review-work-completion/references/retry-policy.md#L3) | R07: Preserve review rules through isolated jobs and authoritative completion gates. |
| BEH-249 | Retry Mechanism (CLI reviewers vs Alice) | [skills/review-work-completion/references/retry-policy.md:14](../../../../../claude-autopilot/skills/review-work-completion/references/retry-policy.md#L14) | R07: Preserve review rules through isolated jobs and authoritative completion gates. |
| BEH-250 | Inlined prompt (Bob's first dispatch) | [skills/review-work-completion/references/retry-policy.md:21](../../../../../claude-autopilot/skills/review-work-completion/references/retry-policy.md#L21) | R07: Preserve review rules through isolated jobs and authoritative completion gates. |
| BEH-251 | Format Compliance | [skills/review-work-completion/references/retry-policy.md:50](../../../../../claude-autopilot/skills/review-work-completion/references/retry-policy.md#L50) | R07: Preserve review rules through isolated jobs and authoritative completion gates. |
| BEH-252 | Per-Rule Verdict Completeness | [skills/review-work-completion/references/retry-policy.md:57](../../../../../claude-autopilot/skills/review-work-completion/references/retry-policy.md#L57) | R07: Preserve review rules through isolated jobs and authoritative completion gates. |
| BEH-253 | Required shape | [skills/review-work-completion/references/review-coverage-format.md:9](../../../../../claude-autopilot/skills/review-work-completion/references/review-coverage-format.md#L9) | R07: Preserve review rules through isolated jobs and authoritative completion gates. |
| BEH-254 | Gate contract | [skills/review-work-completion/references/review-coverage-format.md:27](../../../../../claude-autopilot/skills/review-work-completion/references/review-coverage-format.md#L27) | R07: Preserve review rules through isolated jobs and authoritative completion gates. |
| BEH-255 | Plan Compliance | [skills/review-work-completion/references/review-dimensions.md:5](../../../../../claude-autopilot/skills/review-work-completion/references/review-dimensions.md#L5) | R07: Preserve review rules through isolated jobs and authoritative completion gates. |
| BEH-256 | PRD Coverage | [skills/review-work-completion/references/review-dimensions.md:12](../../../../../claude-autopilot/skills/review-work-completion/references/review-dimensions.md#L12) | R07: Preserve review rules through isolated jobs and authoritative completion gates. |
| BEH-257 | Simplification | [skills/review-work-completion/references/review-dimensions.md:19](../../../../../claude-autopilot/skills/review-work-completion/references/review-dimensions.md#L19) | R07: Preserve review rules through isolated jobs and authoritative completion gates. |
| BEH-258 | Testing | [skills/review-work-completion/references/review-dimensions.md:50](../../../../../claude-autopilot/skills/review-work-completion/references/review-dimensions.md#L50) | R07: Preserve review rules through isolated jobs and authoritative completion gates. |
| BEH-259 | Security | [skills/review-work-completion/references/review-dimensions.md:61](../../../../../claude-autopilot/skills/review-work-completion/references/review-dimensions.md#L61) | R07: Preserve review rules through isolated jobs and authoritative completion gates. |
| BEH-260 | Documentation | [skills/review-work-completion/references/review-dimensions.md:69](../../../../../claude-autopilot/skills/review-work-completion/references/review-dimensions.md#L69) | R07: Preserve review rules through isolated jobs and authoritative completion gates. |
| BEH-261 | Rules | [skills/review-work-completion/references/rubric.md:5](../../../../../claude-autopilot/skills/review-work-completion/references/rubric.md#L5) | R07: Preserve review rules through isolated jobs and authoritative completion gates. |
| BEH-262 | Tests | [skills/review-work-completion/references/rubric.md:7](../../../../../claude-autopilot/skills/review-work-completion/references/rubric.md#L7) | R07: Preserve review rules through isolated jobs and authoritative completion gates. |
| BEH-263 | Integration | [skills/review-work-completion/references/rubric.md:13](../../../../../claude-autopilot/skills/review-work-completion/references/rubric.md#L13) | R07: Preserve review rules through isolated jobs and authoritative completion gates. |
| BEH-264 | Security | [skills/review-work-completion/references/rubric.md:17](../../../../../claude-autopilot/skills/review-work-completion/references/rubric.md#L17) | R07: Preserve review rules through isolated jobs and authoritative completion gates. |
| BEH-265 | Domain | [skills/review-work-completion/references/rubric.md:23](../../../../../claude-autopilot/skills/review-work-completion/references/rubric.md#L23) | R07: Preserve review rules through isolated jobs and authoritative completion gates. |
| BEH-266 | Code Quality | [skills/review-work-completion/references/rubric.md:29](../../../../../claude-autopilot/skills/review-work-completion/references/rubric.md#L29) | R07: Preserve review rules through isolated jobs and authoritative completion gates. |
| BEH-267 | Rendering (mechanic — lives in the CLI) | [skills/run-autopilot/references/audit-log-format.md:7](../../../../../claude-autopilot/skills/run-autopilot/references/audit-log-format.md#L7) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-268 | Decision Sources | [skills/run-autopilot/references/audit-log-format.md:17](../../../../../claude-autopilot/skills/run-autopilot/references/audit-log-format.md#L17) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-269 | decisions.md Projection (judgment — stays with the model) | [skills/run-autopilot/references/audit-log-format.md:34](../../../../../claude-autopilot/skills/run-autopilot/references/audit-log-format.md#L34) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-270 | Relationship to state.json | [skills/run-autopilot/references/audit-log-format.md:55](../../../../../claude-autopilot/skills/run-autopilot/references/audit-log-format.md#L55) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-271 | Rendering (mechanic — lives in the CLI) | [skills/run-autopilot/references/batch-report-format.md:12](../../../../../claude-autopilot/skills/run-autopilot/references/batch-report-format.md#L12) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-272 | What the batch summary carries about skips | [skills/run-autopilot/references/batch-report-format.md:25](../../../../../claude-autopilot/skills/run-autopilot/references/batch-report-format.md#L25) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-273 | What a completed-PRD section carries | [skills/run-autopilot/references/batch-report-format.md:46](../../../../../claude-autopilot/skills/run-autopilot/references/batch-report-format.md#L46) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-274 | Wave summary report | [skills/run-autopilot/references/batch-report-format.md:101](../../../../../claude-autopilot/skills/run-autopilot/references/batch-report-format.md#L101) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-275 | Operator keys (foreground tracon) | [skills/run-autopilot/references/dashboard-format.md:17](../../../../../claude-autopilot/skills/run-autopilot/references/dashboard-format.md#L17) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-276 | Loop registry | [skills/run-autopilot/references/dashboard-format.md:36](../../../../../claude-autopilot/skills/run-autopilot/references/dashboard-format.md#L36) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-277 | What tracon shows | [skills/run-autopilot/references/dashboard-format.md:46](../../../../../claude-autopilot/skills/run-autopilot/references/dashboard-format.md#L46) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-278 | State contract | [skills/run-autopilot/references/dashboard-format.md:53](../../../../../claude-autopilot/skills/run-autopilot/references/dashboard-format.md#L53) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-279 | Fallback: render_stream | [skills/run-autopilot/references/dashboard-format.md:61](../../../../../claude-autopilot/skills/run-autopilot/references/dashboard-format.md#L61) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-280 | Autonomy in loop mode (hard rule) | [skills/run-autopilot/references/decision-framework.md:5](../../../../../claude-autopilot/skills/run-autopilot/references/decision-framework.md#L5) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-281 | Auto-fix (proceed without asking) | [skills/run-autopilot/references/decision-framework.md:20](../../../../../claude-autopilot/skills/run-autopilot/references/decision-framework.md#L20) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-282 | Research-then-decide (conditional autonomy) | [skills/run-autopilot/references/decision-framework.md:33](../../../../../claude-autopilot/skills/run-autopilot/references/decision-framework.md#L33) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-283 | Protocol A: New dependency | [skills/run-autopilot/references/decision-framework.md:44](../../../../../claude-autopilot/skills/run-autopilot/references/decision-framework.md#L44) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-284 | Protocol B: Recurring issue | [skills/run-autopilot/references/decision-framework.md:53](../../../../../claude-autopilot/skills/run-autopilot/references/decision-framework.md#L53) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-285 | Protocol C: High + data model change | [skills/run-autopilot/references/decision-framework.md:61](../../../../../claude-autopilot/skills/run-autopilot/references/decision-framework.md#L61) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-286 | Protocol D: High + public API | [skills/run-autopilot/references/decision-framework.md:68](../../../../../claude-autopilot/skills/run-autopilot/references/decision-framework.md#L68) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-287 | Research tool requirements | [skills/run-autopilot/references/decision-framework.md:75](../../../../../claude-autopilot/skills/run-autopilot/references/decision-framework.md#L75) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-288 | Defer to batch end (log, don't PAUSE) | [skills/run-autopilot/references/decision-framework.md:81](../../../../../claude-autopilot/skills/run-autopilot/references/decision-framework.md#L81) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-289 | PAUSE (present to user, block progress) | [skills/run-autopilot/references/decision-framework.md:91](../../../../../claude-autopilot/skills/run-autopilot/references/decision-framework.md#L91) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-290 | Classification Process | [skills/run-autopilot/references/decision-framework.md:102](../../../../../claude-autopilot/skills/run-autopilot/references/decision-framework.md#L102) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-291 | Decision Logging | [skills/run-autopilot/references/decision-framework.md:116](../../../../../claude-autopilot/skills/run-autopilot/references/decision-framework.md#L116) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-292 | Presenting Escalated Issues | [skills/run-autopilot/references/decision-framework.md:125](../../../../../claude-autopilot/skills/run-autopilot/references/decision-framework.md#L125) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-309 | Rules | [skills/run-autopilot/references/doubt-review-rubric.md:11](../../../../../claude-autopilot/skills/run-autopilot/references/doubt-review-rubric.md#L11) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-310 | Full Categorization | [skills/run-autopilot/references/doubt-review-rubric.md:13](../../../../../claude-autopilot/skills/run-autopilot/references/doubt-review-rubric.md#L13) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-311 | FIX Validity | [skills/run-autopilot/references/doubt-review-rubric.md:17](../../../../../claude-autopilot/skills/run-autopilot/references/doubt-review-rubric.md#L17) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-312 | VERIFY Validity | [skills/run-autopilot/references/doubt-review-rubric.md:21](../../../../../claude-autopilot/skills/run-autopilot/references/doubt-review-rubric.md#L21) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-313 | KNOWN Validity | [skills/run-autopilot/references/doubt-review-rubric.md:25](../../../../../claude-autopilot/skills/run-autopilot/references/doubt-review-rubric.md#L25) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-314 | Count Conservation | [skills/run-autopilot/references/doubt-review-rubric.md:29](../../../../../claude-autopilot/skills/run-autopilot/references/doubt-review-rubric.md#L29) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-315 | Symptom: python3 is broken (mise upgrade, venv drift, PATH change) | [skills/run-autopilot/references/hook-recovery.md:6](../../../../../claude-autopilot/skills/run-autopilot/references/hook-recovery.md#L6) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-316 | 1. Confirm it | [skills/run-autopilot/references/hook-recovery.md:14](../../../../../claude-autopilot/skills/run-autopilot/references/hook-recovery.md#L14) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-317 | 2. Work without hooks (recovery only) | [skills/run-autopilot/references/hook-recovery.md:23](../../../../../claude-autopilot/skills/run-autopilot/references/hook-recovery.md#L23) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-318 | 3. Where hook stderr lands when hooks degrade | [skills/run-autopilot/references/hook-recovery.md:34](../../../../../claude-autopilot/skills/run-autopilot/references/hook-recovery.md#L34) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-319 | Prevention wired into autoclaude | [skills/run-autopilot/references/hook-recovery.md:45](../../../../../claude-autopilot/skills/run-autopilot/references/hook-recovery.md#L45) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-320 | settings.json backup-before-edit convention | [skills/run-autopilot/references/hook-recovery.md:52](../../../../../claude-autopilot/skills/run-autopilot/references/hook-recovery.md#L52) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-321 | 1. Render | [skills/run-autopilot/references/lane-fast-track.md:11](../../../../../claude-autopilot/skills/run-autopilot/references/lane-fast-track.md#L11) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-322 | 2. Mirror | [skills/run-autopilot/references/lane-fast-track.md:33](../../../../../claude-autopilot/skills/run-autopilot/references/lane-fast-track.md#L33) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-323 | 3. Run | [skills/run-autopilot/references/lane-fast-track.md:57](../../../../../claude-autopilot/skills/run-autopilot/references/lane-fast-track.md#L57) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-324 | Stall | [skills/run-autopilot/references/lane-fast-track.md:90](../../../../../claude-autopilot/skills/run-autopilot/references/lane-fast-track.md#L90) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-325 | 4. Consolidate | [skills/run-autopilot/references/lane-fast-track.md:110](../../../../../claude-autopilot/skills/run-autopilot/references/lane-fast-track.md#L110) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-326 | 5. Close | [skills/run-autopilot/references/lane-fast-track.md:152](../../../../../claude-autopilot/skills/run-autopilot/references/lane-fast-track.md#L152) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-327 | 1. Mirror | [skills/run-autopilot/references/lane-solo.md:16](../../../../../claude-autopilot/skills/run-autopilot/references/lane-solo.md#L16) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-328 | 2. Implement | [skills/run-autopilot/references/lane-solo.md:44](../../../../../claude-autopilot/skills/run-autopilot/references/lane-solo.md#L44) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-329 | 3. Suite | [skills/run-autopilot/references/lane-solo.md:85](../../../../../claude-autopilot/skills/run-autopilot/references/lane-solo.md#L85) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-330 | 4. Escalation checks | [skills/run-autopilot/references/lane-solo.md:96](../../../../../claude-autopilot/skills/run-autopilot/references/lane-solo.md#L96) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-331 | 5. Review | [skills/run-autopilot/references/lane-solo.md:136](../../../../../claude-autopilot/skills/run-autopilot/references/lane-solo.md#L136) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-332 | Disposition | [skills/run-autopilot/references/lane-solo.md:205](../../../../../claude-autopilot/skills/run-autopilot/references/lane-solo.md#L205) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-333 | 6. Close | [skills/run-autopilot/references/lane-solo.md:238](../../../../../claude-autopilot/skills/run-autopilot/references/lane-solo.md#L238) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-334 | Rungs | [skills/run-autopilot/references/model-ladder.md:8](../../../../../claude-autopilot/skills/run-autopilot/references/model-ladder.md#L8) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-335 | Tier -> backend map | [skills/run-autopilot/references/model-ladder.md:28](../../../../../claude-autopilot/skills/run-autopilot/references/model-ladder.md#L28) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-336 | Per-rung budgets | [skills/run-autopilot/references/model-ladder.md:44](../../../../../claude-autopilot/skills/run-autopilot/references/model-ladder.md#L44) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-337 | Capability ladders | [skills/run-autopilot/references/model-ladder.md:64](../../../../../claude-autopilot/skills/run-autopilot/references/model-ladder.md#L64) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-338 | Fable rescue | [skills/run-autopilot/references/model-ladder.md:82](../../../../../claude-autopilot/skills/run-autopilot/references/model-ladder.md#L82) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-339 | Infra vs capability | [skills/run-autopilot/references/model-ladder.md:103](../../../../../claude-autopilot/skills/run-autopilot/references/model-ladder.md#L103) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-340 | Codex rung | [skills/run-autopilot/references/model-ladder.md:112](../../../../../claude-autopilot/skills/run-autopilot/references/model-ladder.md#L112) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-341 | Memory gate | [skills/run-autopilot/references/model-ladder.md:178](../../../../../claude-autopilot/skills/run-autopilot/references/model-ladder.md#L178) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-342 | Ordering | [skills/run-autopilot/references/model-ladder.md:226](../../../../../claude-autopilot/skills/run-autopilot/references/model-ladder.md#L226) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-343 | Kill-switches | [skills/run-autopilot/references/model-ladder.md:242](../../../../../claude-autopilot/skills/run-autopilot/references/model-ladder.md#L242) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-344 | Tuning | [skills/run-autopilot/references/model-ladder.md:276](../../../../../claude-autopilot/skills/run-autopilot/references/model-ladder.md#L276) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-345 | Decay | [skills/run-autopilot/references/model-ladder.md:286](../../../../../claude-autopilot/skills/run-autopilot/references/model-ladder.md#L286) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-346 | Phase 0: PRD Selection | [skills/run-autopilot/references/phase-build.md:10](../../../../../claude-autopilot/skills/run-autopilot/references/phase-build.md#L10) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-347 | Enter in one call | [skills/run-autopilot/references/phase-build.md:14](../../../../../claude-autopilot/skills/run-autopilot/references/phase-build.md#L14) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-348 | Ensure lifecycle directories exist | [skills/run-autopilot/references/phase-build.md:77](../../../../../claude-autopilot/skills/run-autopilot/references/phase-build.md#L77) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-349 | Clear inherited hand-off markers | [skills/run-autopilot/references/phase-build.md:92](../../../../../claude-autopilot/skills/run-autopilot/references/phase-build.md#L92) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-350 | Handle park request (FIRST abort-handler check) | [skills/run-autopilot/references/phase-build.md:111](../../../../../claude-autopilot/skills/run-autopilot/references/phase-build.md#L111) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-351 | Handle Work-phase abort (from a prior session) | [skills/run-autopilot/references/phase-build.md:144](../../../../../claude-autopilot/skills/run-autopilot/references/phase-build.md#L144) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-352 | Handle pending custody | [skills/run-autopilot/references/phase-build.md:159](../../../../../claude-autopilot/skills/run-autopilot/references/phase-build.md#L159) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-353 | Normal PRD selection | [skills/run-autopilot/references/phase-build.md:171](../../../../../claude-autopilot/skills/run-autopilot/references/phase-build.md#L171) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-354 | Frontmatter parse (step 5) | [skills/run-autopilot/references/phase-build.md:206](../../../../../claude-autopilot/skills/run-autopilot/references/phase-build.md#L206) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-355 | 5.5. Route by lane | [skills/run-autopilot/references/phase-build.md:258](../../../../../claude-autopilot/skills/run-autopilot/references/phase-build.md#L258) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-356 | Phase 1: Catchup | [skills/run-autopilot/references/phase-build.md:277](../../../../../claude-autopilot/skills/run-autopilot/references/phase-build.md#L277) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-357 | Batch cache check | [skills/run-autopilot/references/phase-build.md:285](../../../../../claude-autopilot/skills/run-autopilot/references/phase-build.md#L285) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-358 | Phase 1.5: Design (build-gate sub-step) | [skills/run-autopilot/references/phase-build.md:312](../../../../../claude-autopilot/skills/run-autopilot/references/phase-build.md#L312) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-359 | Gate-edge headroom check (design->plan and plan->work edges, PRD 00200) | [skills/run-autopilot/references/phase-build.md:340](../../../../../claude-autopilot/skills/run-autopilot/references/phase-build.md#L340) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-360 | Phase 2: Planning | [skills/run-autopilot/references/phase-build.md:344](../../../../../claude-autopilot/skills/run-autopilot/references/phase-build.md#L344) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-361 | Replan mode | [skills/run-autopilot/references/phase-build.md:348](../../../../../claude-autopilot/skills/run-autopilot/references/phase-build.md#L348) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-362 | Handle plan-tasks stall (oversized task) | [skills/run-autopilot/references/phase-build.md:361](../../../../../claude-autopilot/skills/run-autopilot/references/phase-build.md#L361) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-363 | Phase 3: Work | [skills/run-autopilot/references/phase-build.md:372](../../../../../claude-autopilot/skills/run-autopilot/references/phase-build.md#L372) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-364 | Hand off to a fresh session for reviews | [skills/run-autopilot/references/phase-build.md:397](../../../../../claude-autopilot/skills/run-autopilot/references/phase-build.md#L397) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-365 | Phase 9: Completion | [skills/run-autopilot/references/phase-done.md:10](../../../../../claude-autopilot/skills/run-autopilot/references/phase-done.md#L10) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-366 | Continuation | [skills/run-autopilot/references/phase-done.md:66](../../../../../claude-autopilot/skills/run-autopilot/references/phase-done.md#L66) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-367 | Batch-End Review | [skills/run-autopilot/references/phase-done.md:86](../../../../../claude-autopilot/skills/run-autopilot/references/phase-done.md#L86) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-368 | Phase 4: Review | [skills/run-autopilot/references/phase-review.md:12](../../../../../claude-autopilot/skills/run-autopilot/references/phase-review.md#L12) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-369 | Phase 5: Decision Gate | [skills/run-autopilot/references/phase-review.md:28](../../../../../claude-autopilot/skills/run-autopilot/references/phase-review.md#L28) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-370 | Cap check — evaluate after reading review, before rework dispatch | [skills/run-autopilot/references/phase-review.md:30](../../../../../claude-autopilot/skills/run-autopilot/references/phase-review.md#L30) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-371 | Cap-pause behavior | [skills/run-autopilot/references/phase-review.md:64](../../../../../claude-autopilot/skills/run-autopilot/references/phase-review.md#L64) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-372 | Safety Checks — evaluate BEFORE classifying individual issues: | [skills/run-autopilot/references/phase-review.md:97](../../../../../claude-autopilot/skills/run-autopilot/references/phase-review.md#L97) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-373 | Classification (per finding): | [skills/run-autopilot/references/phase-review.md:106](../../../../../claude-autopilot/skills/run-autopilot/references/phase-review.md#L106) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-374 | Settled-decisions ledger (PRD 00095) | [skills/run-autopilot/references/phase-review.md:149](../../../../../claude-autopilot/skills/run-autopilot/references/phase-review.md#L149) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-375 | Outcomes: | [skills/run-autopilot/references/phase-review.md:161](../../../../../claude-autopilot/skills/run-autopilot/references/phase-review.md#L161) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-376 | Convergence metric | [skills/run-autopilot/references/phase-review.md:172](../../../../../claude-autopilot/skills/run-autopilot/references/phase-review.md#L172) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-377 | Tail sweep | [skills/run-autopilot/references/phase-review.md:191](../../../../../claude-autopilot/skills/run-autopilot/references/phase-review.md#L191) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-378 | Hand off to the finalize session | [skills/run-autopilot/references/phase-review.md:217](../../../../../claude-autopilot/skills/run-autopilot/references/phase-review.md#L217) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-379 | Phase 6: Rework | [skills/run-autopilot/references/phase-review.md:228](../../../../../claude-autopilot/skills/run-autopilot/references/phase-review.md#L228) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-380 | Escalate review-flagged tasks by tier (PRD 00025) | [skills/run-autopilot/references/phase-review.md:239](../../../../../claude-autopilot/skills/run-autopilot/references/phase-review.md#L239) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-381 | Dispatch rework | [skills/run-autopilot/references/phase-review.md:284](../../../../../claude-autopilot/skills/run-autopilot/references/phase-review.md#L284) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-382 | After /autopilot:work returns | [skills/run-autopilot/references/phase-review.md:319](../../../../../claude-autopilot/skills/run-autopilot/references/phase-review.md#L319) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-383 | De-slop is part of the doubt lens | [skills/run-autopilot/references/phase-review.md:341](../../../../../claude-autopilot/skills/run-autopilot/references/phase-review.md#L341) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-384 | Loop-mode stall procedure (PRD 00017) | [skills/run-autopilot/references/recovery.md:5](../../../../../claude-autopilot/skills/run-autopilot/references/recovery.md#L5) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-385 | Stall `site` slugs | [skills/run-autopilot/references/recovery.md:39](../../../../../claude-autopilot/skills/run-autopilot/references/recovery.md#L39) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-386 | Systemic-park breaker interaction (`batch.parks_consecutive`) | [skills/run-autopilot/references/recovery.md:133](../../../../../claude-autopilot/skills/run-autopilot/references/recovery.md#L133) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-387 | Cap rotation | [skills/run-autopilot/references/recovery.md:145](../../../../../claude-autopilot/skills/run-autopilot/references/recovery.md#L145) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-388 | Work-phase abort: replan procedure | [skills/run-autopilot/references/recovery.md:153](../../../../../claude-autopilot/skills/run-autopilot/references/recovery.md#L153) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-389 | Crash recovery: escalation_exhausted seen at Phase 0 | [skills/run-autopilot/references/recovery.md:213](../../../../../claude-autopilot/skills/run-autopilot/references/recovery.md#L213) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-390 | plan-tasks stall: oversized task | [skills/run-autopilot/references/recovery.md:217](../../../../../claude-autopilot/skills/run-autopilot/references/recovery.md#L217) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-391 | Rework escalation exhausted | [skills/run-autopilot/references/recovery.md:240](../../../../../claude-autopilot/skills/run-autopilot/references/recovery.md#L240) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-392 | Fable rescue gate (PRD 00076) | [skills/run-autopilot/references/recovery.md:252](../../../../../claude-autopilot/skills/run-autopilot/references/recovery.md#L252) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-393 | Stall move | [skills/run-autopilot/references/recovery.md:281](../../../../../claude-autopilot/skills/run-autopilot/references/recovery.md#L281) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-394 | Cap-Pause Resume Handler | [skills/run-autopilot/references/recovery.md:302](../../../../../claude-autopilot/skills/run-autopilot/references/recovery.md#L302) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-395 | Schema | [skills/run-autopilot/references/state-schema.md:5](../../../../../claude-autopilot/skills/run-autopilot/references/state-schema.md#L5) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-396 | Field Descriptions | [skills/run-autopilot/references/state-schema.md:162](../../../../../claude-autopilot/skills/run-autopilot/references/state-schema.md#L162) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-397 | Marker files | [skills/run-autopilot/references/state-schema.md:246](../../../../../claude-autopilot/skills/run-autopilot/references/state-schema.md#L246) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-398 | Custody journal | [skills/run-autopilot/references/state-schema.md:271](../../../../../claude-autopilot/skills/run-autopilot/references/state-schema.md#L271) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-399 | Attempt ledger | [skills/run-autopilot/references/state-schema.md:281](../../../../../claude-autopilot/skills/run-autopilot/references/state-schema.md#L281) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-400 | Convergence rows | [skills/run-autopilot/references/state-schema.md:308](../../../../../claude-autopilot/skills/run-autopilot/references/state-schema.md#L308) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-401 | Fable rescue ledger | [skills/run-autopilot/references/state-schema.md:350](../../../../../claude-autopilot/skills/run-autopilot/references/state-schema.md#L350) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-402 | `fablectl.py` - the sole writer | [skills/run-autopilot/references/state-schema.md:392](../../../../../claude-autopilot/skills/run-autopilot/references/state-schema.md#L392) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-403 | Research Evidence Schema | [skills/run-autopilot/references/state-schema.md:438](../../../../../claude-autopilot/skills/run-autopilot/references/state-schema.md#L438) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-404 | Batch Deferred Log | [skills/run-autopilot/references/state-schema.md:451](../../../../../claude-autopilot/skills/run-autopilot/references/state-schema.md#L451) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-405 | Build-Session Model Promotion Signals | [skills/run-autopilot/references/state-schema.md:515](../../../../../claude-autopilot/skills/run-autopilot/references/state-schema.md#L515) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-406 | Two more CLI verbs | [skills/run-autopilot/references/state-schema.md:543](../../../../../claude-autopilot/skills/run-autopilot/references/state-schema.md#L543) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-407 | Skip Logic | [skills/run-autopilot/references/state-schema.md:549](../../../../../claude-autopilot/skills/run-autopilot/references/state-schema.md#L549) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-408 | Detection | [skills/run-autopilot/references/unattended-contract.md:6](../../../../../claude-autopilot/skills/run-autopilot/references/unattended-contract.md#L6) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-409 | Rules (unattended sessions) | [skills/run-autopilot/references/unattended-contract.md:17](../../../../../claude-autopilot/skills/run-autopilot/references/unattended-contract.md#L17) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-410 | For skill authors | [skills/run-autopilot/references/unattended-contract.md:35](../../../../../claude-autopilot/skills/run-autopilot/references/unattended-contract.md#L35) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-411 | `autopilot wave plan [--max-lanes N]` | [skills/run-autopilot/references/waves.md:14](../../../../../claude-autopilot/skills/run-autopilot/references/waves.md#L14) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-412 | `autopilot wave launch` | [skills/run-autopilot/references/waves.md:42](../../../../../claude-autopilot/skills/run-autopilot/references/waves.md#L42) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-413 | `autopilot wave status` | [skills/run-autopilot/references/waves.md:62](../../../../../claude-autopilot/skills/run-autopilot/references/waves.md#L62) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-414 | `autopilot wave abort` | [skills/run-autopilot/references/waves.md:76](../../../../../claude-autopilot/skills/run-autopilot/references/waves.md#L76) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-415 | `autopilot wave assemble` | [skills/run-autopilot/references/waves.md:115](../../../../../claude-autopilot/skills/run-autopilot/references/waves.md#L115) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-416 | What a lane worktree holds | [skills/run-autopilot/references/waves.md:148](../../../../../claude-autopilot/skills/run-autopilot/references/waves.md#L148) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-417 | Review and land | [skills/run-autopilot/references/waves.md:165](../../../../../claude-autopilot/skills/run-autopilot/references/waves.md#L165) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-418 | `autopilot wave review` | [skills/run-autopilot/references/waves.md:167](../../../../../claude-autopilot/skills/run-autopilot/references/waves.md#L167) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-419 | `autopilot wave land` | [skills/run-autopilot/references/waves.md:184](../../../../../claude-autopilot/skills/run-autopilot/references/waves.md#L184) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-420 | wave run | [skills/run-autopilot/references/waves.md:198](../../../../../claude-autopilot/skills/run-autopilot/references/waves.md#L198) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-421 | Operator notes | [skills/run-autopilot/references/waves.md:245](../../../../../claude-autopilot/skills/run-autopilot/references/waves.md#L245) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-422 | Prompt Delivery | [skills/use-codex/references/dispatch-contract.md:7](../../../../../claude-autopilot/skills/use-codex/references/dispatch-contract.md#L7) | R21: Keep Codex backend semantics in an explicit host/job adapter. |
| BEH-423 | Child Stdin Policy | [skills/use-codex/references/dispatch-contract.md:19](../../../../../claude-autopilot/skills/use-codex/references/dispatch-contract.md#L19) | R21: Keep Codex backend semantics in an explicit host/job adapter. |
| BEH-424 | Error Stream Convention | [skills/use-codex/references/dispatch-contract.md:23](../../../../../claude-autopilot/skills/use-codex/references/dispatch-contract.md#L23) | R21: Keep Codex backend semantics in an explicit host/job adapter. |
| BEH-425 | Background Dispatch and Waiting | [skills/use-codex/references/dispatch-contract.md:27](../../../../../claude-autopilot/skills/use-codex/references/dispatch-contract.md#L27) | R21: Keep Codex backend semantics in an explicit host/job adapter. |
| BEH-426 | Following Up | [skills/use-codex/references/dispatch-contract.md:37](../../../../../claude-autopilot/skills/use-codex/references/dispatch-contract.md#L37) | R21: Keep Codex backend semantics in an explicit host/job adapter. |
| BEH-427 | Error Handling | [skills/use-codex/references/dispatch-contract.md:44](../../../../../claude-autopilot/skills/use-codex/references/dispatch-contract.md#L44) | R21: Keep Codex backend semantics in an explicit host/job adapter. |
| BEH-428 | Error taxonomy | [skills/use-codex/references/dispatch-contract.md:50](../../../../../claude-autopilot/skills/use-codex/references/dispatch-contract.md#L50) | R21: Keep Codex backend semantics in an explicit host/job adapter. |
| BEH-429 | Implementor-mode divergence (codex, PRD 00105) | [skills/use-codex/references/dispatch-contract.md:63](../../../../../claude-autopilot/skills/use-codex/references/dispatch-contract.md#L63) | R21: Keep Codex backend semantics in an explicit host/job adapter. |
| BEH-430 | Scrubbed at loop spawn | [skills/use-codex/references/host-markers.md:11](../../../../../claude-autopilot/skills/use-codex/references/host-markers.md#L11) | R21: Keep Codex backend semantics in an explicit host/job adapter. |
| BEH-431 | codex (native `codex exec`) | [skills/use-codex/references/host-markers.md:18](../../../../../claude-autopilot/skills/use-codex/references/host-markers.md#L18) | R21: Keep Codex backend semantics in an explicit host/job adapter. |
| BEH-432 | copilot (`copilot -p`) | [skills/use-codex/references/host-markers.md:35](../../../../../claude-autopilot/skills/use-codex/references/host-markers.md#L35) | R21: Keep Codex backend semantics in an explicit host/job adapter. |
| BEH-433 | gemini (native `gemini -p`) | [skills/use-codex/references/host-markers.md:50](../../../../../claude-autopilot/skills/use-codex/references/host-markers.md#L50) | R21: Keep Codex backend semantics in an explicit host/job adapter. |
| BEH-434 | Procedure | [skills/work/references/adversarial-test-prompt.md:5](../../../../../claude-autopilot/skills/work/references/adversarial-test-prompt.md#L5) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-435 | Prompt Template | [skills/work/references/adversarial-test-prompt.md:20](../../../../../claude-autopilot/skills/work/references/adversarial-test-prompt.md#L20) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-436 | Context Selection | [skills/work/references/adversarial-test-prompt.md:63](../../../../../claude-autopilot/skills/work/references/adversarial-test-prompt.md#L63) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-437 | Feedback to Tess (when Devon succeeds) | [skills/work/references/adversarial-test-prompt.md:77](../../../../../claude-autopilot/skills/work/references/adversarial-test-prompt.md#L77) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-438 | Dispatch-provenance fields (moved from SKILL.md, PRD 00119-v2) | [skills/work/references/attempt-logging.md:107](../../../../../claude-autopilot/skills/work/references/attempt-logging.md#L107) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-439 | task-done semantics (moved from SKILL.md step 6, PRD 00119-v2) | [skills/work/references/attempt-logging.md:113](../../../../../claude-autopilot/skills/work/references/attempt-logging.md#L113) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-440 | Assumption ledger (moved from SKILL.md § Assumptions footer, PRD 00119-v2) | [skills/work/references/attempt-logging.md:117](../../../../../claude-autopilot/skills/work/references/attempt-logging.md#L117) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-441 | 1. Hidden assumptions worth surfacing | [skills/work/references/code-quality-examples.md:6](../../../../../claude-autopilot/skills/work/references/code-quality-examples.md#L6) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-442 | Example 1 - ambiguous task description | [skills/work/references/code-quality-examples.md:30](../../../../../claude-autopilot/skills/work/references/code-quality-examples.md#L30) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-443 | 2. Speculative abstraction (Simplicity) | [skills/work/references/code-quality-examples.md:51](../../../../../claude-autopilot/skills/work/references/code-quality-examples.md#L51) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-444 | 3. Drive-by refactoring (Surgical) | [skills/work/references/code-quality-examples.md:80](../../../../../claude-autopilot/skills/work/references/code-quality-examples.md#L80) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-445 | 4. Style drift (Goal-driven) | [skills/work/references/code-quality-examples.md:93](../../../../../claude-autopilot/skills/work/references/code-quality-examples.md#L93) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-446 | Prompt Snippet | [skills/work/references/code-quality-principles.md:18](../../../../../claude-autopilot/skills/work/references/code-quality-principles.md#L18) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-447 | Code quality rules (mandatory) | [skills/work/references/code-quality-principles.md:24](../../../../../claude-autopilot/skills/work/references/code-quality-principles.md#L24) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-448 | Why these four | [skills/work/references/code-quality-principles.md:57](../../../../../claude-autopilot/skills/work/references/code-quality-principles.md#L57) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-449 | Codex rung interception | [skills/work/references/codex-implementor.md:9](../../../../../claude-autopilot/skills/work/references/codex-implementor.md#L9) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-450 | Codex batch health probe | [skills/work/references/codex-implementor.md:39](../../../../../claude-autopilot/skills/work/references/codex-implementor.md#L39) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-451 | Codex dispatch | [skills/work/references/codex-implementor.md:166](../../../../../claude-autopilot/skills/work/references/codex-implementor.md#L166) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-452 | Hook interaction | [skills/work/references/codex-implementor.md:222](../../../../../claude-autopilot/skills/work/references/codex-implementor.md#L222) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-453 | Where Codex is invoked today | [skills/work/references/codex-integration.md:5](../../../../../claude-autopilot/skills/work/references/codex-integration.md#L5) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-454 | Invocation | [skills/work/references/codex-integration.md:11](../../../../../claude-autopilot/skills/work/references/codex-integration.md#L11) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-455 | Prompt-template note | [skills/work/references/codex-integration.md:25](../../../../../claude-autopilot/skills/work/references/codex-integration.md#L25) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-456 | Common Issues | [skills/work/references/codex-integration.md:34](../../../../../claude-autopilot/skills/work/references/codex-integration.md#L34) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-457 | Timeout | [skills/work/references/codex-integration.md:36](../../../../../claude-autopilot/skills/work/references/codex-integration.md#L36) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-458 | Context exceeded | [skills/work/references/codex-integration.md:42](../../../../../claude-autopilot/skills/work/references/codex-integration.md#L42) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-459 | Wrong approach | [skills/work/references/codex-integration.md:48](../../../../../claude-autopilot/skills/work/references/codex-integration.md#L48) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-471 | What to run | [skills/work/references/final-verification.md:9](../../../../../claude-autopilot/skills/work/references/final-verification.md#L9) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-472 | Timed-out commands | [skills/work/references/final-verification.md:29](../../../../../claude-autopilot/skills/work/references/final-verification.md#L29) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-473 | Queued verification checks | [skills/work/references/final-verification.md:51](../../../../../claude-autopilot/skills/work/references/final-verification.md#L51) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-474 | Recorded verification result | [skills/work/references/final-verification.md:103](../../../../../claude-autopilot/skills/work/references/final-verification.md#L103) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-475 | Handling failures at this step | [skills/work/references/final-verification.md:191](../../../../../claude-autopilot/skills/work/references/final-verification.md#L191) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-476 | 5.5. Verify THIS task's tests pass | [skills/work/references/gate-failure.md:5](../../../../../claude-autopilot/skills/work/references/gate-failure.md#L5) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-477 | Qwen output rejection | [skills/work/references/gate-failure.md:131](../../../../../claude-autopilot/skills/work/references/gate-failure.md#L131) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-478 | Retry render (step 5.5) | [skills/work/references/gate-failure.md:173](../../../../../claude-autopilot/skills/work/references/gate-failure.md#L173) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-479 | Style-fix render (step 5.65) | [skills/work/references/gate-failure.md:190](../../../../../claude-autopilot/skills/work/references/gate-failure.md#L190) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-480 | Legacy escalation branch (step 5.5) | [skills/work/references/gate-failure.md:213](../../../../../claude-autopilot/skills/work/references/gate-failure.md#L213) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-481 | Infrastructure-failure circuit breaker (step 4.2) | [skills/work/references/gate-failure.md:222](../../../../../claude-autopilot/skills/work/references/gate-failure.md#L222) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-482 | Step 4 result table | [skills/work/references/gate-failure.md:231](../../../../../claude-autopilot/skills/work/references/gate-failure.md#L231) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-483 | Narrow scope (step 5.5) | [skills/work/references/gate-failure.md:248](../../../../../claude-autopilot/skills/work/references/gate-failure.md#L248) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-484 | Test-commit SHA (step 2.85) | [skills/work/references/gate-failure.md:258](../../../../../claude-autopilot/skills/work/references/gate-failure.md#L258) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-485 | Prompt Template | [skills/work/references/gemini-integration.md:5](../../../../../claude-autopilot/skills/work/references/gemini-integration.md#L5) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-486 | Permission Modes | [skills/work/references/gemini-integration.md:41](../../../../../claude-autopilot/skills/work/references/gemini-integration.md#L41) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-487 | Execution Modes | [skills/work/references/gemini-integration.md:52](../../../../../claude-autopilot/skills/work/references/gemini-integration.md#L52) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-488 | TDD Implementation Mode (Ivan) | [skills/work/references/gemini-integration.md:59](../../../../../claude-autopilot/skills/work/references/gemini-integration.md#L59) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-489 | Common Issues | [skills/work/references/gemini-integration.md:88](../../../../../claude-autopilot/skills/work/references/gemini-integration.md#L88) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-490 | Session needs context | [skills/work/references/gemini-integration.md:90](../../../../../claude-autopilot/skills/work/references/gemini-integration.md#L90) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-491 | Tool approval interrupts | [skills/work/references/gemini-integration.md:96](../../../../../claude-autopilot/skills/work/references/gemini-integration.md#L96) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-492 | Wrong approach | [skills/work/references/gemini-integration.md:102](../../../../../claude-autopilot/skills/work/references/gemini-integration.md#L102) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-493 | Resume needed | [skills/work/references/gemini-integration.md:111](../../../../../claude-autopilot/skills/work/references/gemini-integration.md#L111) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-494 | Design Authority (visual tasks) | [skills/work/references/gemini-integration.md:117](../../../../../claude-autopilot/skills/work/references/gemini-integration.md#L117) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-495 | Availability (moved from SKILL.md step 3, PRD 00119-v2) | [skills/work/references/gemini-integration.md:136](../../../../../claude-autopilot/skills/work/references/gemini-integration.md#L136) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-496 | Findings you raised, sent to the implementor | [skills/work/references/pat-rerun-prompt.md:6](../../../../../claude-autopilot/skills/work/references/pat-rerun-prompt.md#L6) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-497 | What changed since your last review | [skills/work/references/pat-rerun-prompt.md:10](../../../../../claude-autopilot/skills/work/references/pat-rerun-prompt.md#L10) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-498 | Why the lane is tier-gated | [skills/work/references/per-task-review.md:9](../../../../../claude-autopilot/skills/work/references/per-task-review.md#L9) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-499 | Test-only diffs | [skills/work/references/per-task-review.md:13](../../../../../claude-autopilot/skills/work/references/per-task-review.md#L13) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-500 | Recorded verification | [skills/work/references/per-task-review.md:29](../../../../../claude-autopilot/skills/work/references/per-task-review.md#L29) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-501 | Dispatch | [skills/work/references/per-task-review.md:40](../../../../../claude-autopilot/skills/work/references/per-task-review.md#L40) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-502 | Delta re-runs | [skills/work/references/per-task-review.md:66](../../../../../claude-autopilot/skills/work/references/per-task-review.md#L66) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-503 | Resume failure | [skills/work/references/per-task-review.md:114](../../../../../claude-autopilot/skills/work/references/per-task-review.md#L114) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-504 | Result handling | [skills/work/references/per-task-review.md:133](../../../../../claude-autopilot/skills/work/references/per-task-review.md#L133) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-505 | Preflight | [skills/work/references/qwen-integration.md:20](../../../../../claude-autopilot/skills/work/references/qwen-integration.md#L20) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-506 | Batch-scoped preflight | [skills/work/references/qwen-integration.md:45](../../../../../claude-autopilot/skills/work/references/qwen-integration.md#L45) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-507 | One-shot attempt budget — and why it always escalates to Sonnet | [skills/work/references/qwen-integration.md:66](../../../../../claude-autopilot/skills/work/references/qwen-integration.md#L66) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-508 | Output guards | [skills/work/references/qwen-integration.md:77](../../../../../claude-autopilot/skills/work/references/qwen-integration.md#L77) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-509 | Prompt Template | [skills/work/references/qwen-integration.md:124](../../../../../claude-autopilot/skills/work/references/qwen-integration.md#L124) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-510 | Permission Modes | [skills/work/references/qwen-integration.md:160](../../../../../claude-autopilot/skills/work/references/qwen-integration.md#L160) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-511 | Execution Modes | [skills/work/references/qwen-integration.md:172](../../../../../claude-autopilot/skills/work/references/qwen-integration.md#L172) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-512 | TDD Implementation Mode (Ivan) | [skills/work/references/qwen-integration.md:180](../../../../../claude-autopilot/skills/work/references/qwen-integration.md#L180) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-513 | Common Issues | [skills/work/references/qwen-integration.md:209](../../../../../claude-autopilot/skills/work/references/qwen-integration.md#L209) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-514 | Under-coverage on multi-file tasks | [skills/work/references/qwen-integration.md:211](../../../../../claude-autopilot/skills/work/references/qwen-integration.md#L211) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-515 | Over-claims completeness | [skills/work/references/qwen-integration.md:217](../../../../../claude-autopilot/skills/work/references/qwen-integration.md#L217) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-516 | Slow dispatch | [skills/work/references/qwen-integration.md:223](../../../../../claude-autopilot/skills/work/references/qwen-integration.md#L223) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-517 | Wrong model loaded | [skills/work/references/qwen-integration.md:227](../../../../../claude-autopilot/skills/work/references/qwen-integration.md#L227) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-518 | Backend lists the model but can't serve it | [skills/work/references/qwen-integration.md:233](../../../../../claude-autopilot/skills/work/references/qwen-integration.md#L233) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-519 | Helper exits non-zero | [skills/work/references/qwen-integration.md:239](../../../../../claude-autopilot/skills/work/references/qwen-integration.md#L239) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-520 | Scope (moved from SKILL.md step 3, PRD 00119-v2) | [skills/work/references/qwen-integration.md:245](../../../../../claude-autopilot/skills/work/references/qwen-integration.md#L245) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-521 | New-module pre-check | [skills/work/references/red-check.md:8](../../../../../claude-autopilot/skills/work/references/red-check.md#L8) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-522 | Outcomes | [skills/work/references/red-check.md:20](../../../../../claude-autopilot/skills/work/references/red-check.md#L20) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-523 | Micro lane (PRD 00148) | [skills/work/references/rework-mode.md:16](../../../../../claude-autopilot/skills/work/references/rework-mode.md#L16) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-524 | Prompt Template | [skills/work/references/self-deslop-prompt.md:36](../../../../../claude-autopilot/skills/work/references/self-deslop-prompt.md#L36) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-525 | Test-only diffs | [skills/work/references/self-deslop-prompt.md:108](../../../../../claude-autopilot/skills/work/references/self-deslop-prompt.md#L108) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-526 | Procedure | [skills/work/references/self-deslop-prompt.md:122](../../../../../claude-autopilot/skills/work/references/self-deslop-prompt.md#L122) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-527 | Dispatch contract reminders | [skills/work/references/self-deslop-prompt.md:149](../../../../../claude-autopilot/skills/work/references/self-deslop-prompt.md#L149) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-528 | Diff construction | [skills/work/references/style-gate.md:15](../../../../../claude-autopilot/skills/work/references/style-gate.md#L15) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-529 | Invocation | [skills/work/references/style-gate.md:19](../../../../../claude-autopilot/skills/work/references/style-gate.md#L19) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-530 | Outcome ladder | [skills/work/references/style-gate.md:30](../../../../../claude-autopilot/skills/work/references/style-gate.md#L30) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-531 | Fix dispatch | [skills/work/references/style-gate.md:53](../../../../../claude-autopilot/skills/work/references/style-gate.md#L53) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-532 | Split hygiene | [skills/work/references/style-gate.md:77](../../../../../claude-autopilot/skills/work/references/style-gate.md#L77) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-533 | Split-hygiene outcome ladder | [skills/work/references/style-gate.md:110](../../../../../claude-autopilot/skills/work/references/style-gate.md#L110) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-534 | Split-hygiene fix dispatch | [skills/work/references/style-gate.md:128](../../../../../claude-autopilot/skills/work/references/style-gate.md#L128) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-535 | Role effort | [skills/work/references/subagent-dispatch.md:9](../../../../../claude-autopilot/skills/work/references/subagent-dispatch.md#L9) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-536 | Subagent Dispatch Budget | [skills/work/references/subagent-dispatch.md:24](../../../../../claude-autopilot/skills/work/references/subagent-dispatch.md#L24) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-537 | Subagent Watchdog | [skills/work/references/subagent-dispatch.md:73](../../../../../claude-autopilot/skills/work/references/subagent-dispatch.md#L73) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-538 | Foreground command budgets | [skills/work/references/subagent-dispatch.md:111](../../../../../claude-autopilot/skills/work/references/subagent-dispatch.md#L111) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-539 | Never combine inspection with verification | [skills/work/references/subagent-dispatch.md:129](../../../../../claude-autopilot/skills/work/references/subagent-dispatch.md#L129) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-540 | Blocked verification and backgrounded commands | [skills/work/references/subagent-dispatch.md:135](../../../../../claude-autopilot/skills/work/references/subagent-dispatch.md#L135) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-541 | Passing values to render_prompt.py | [skills/work/references/subagent-dispatch.md:144](../../../../../claude-autopilot/skills/work/references/subagent-dispatch.md#L144) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-542 | Mechanism and tier (moved from SKILL.md, PRD 00119-v2) | [skills/work/references/subagent-dispatch.md:163](../../../../../claude-autopilot/skills/work/references/subagent-dispatch.md#L163) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-543 | Reflow tripwire (step 5, PRD 00148) | [skills/work/references/subagent-dispatch.md:169](../../../../../claude-autopilot/skills/work/references/subagent-dispatch.md#L169) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-544 | Dispatch telemetry (PRD 00168) | [skills/work/references/subagent-dispatch.md:189](../../../../../claude-autopilot/skills/work/references/subagent-dispatch.md#L189) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-545 | Row catalogue | [skills/work/references/subagent-dispatch.md:195](../../../../../claude-autopilot/skills/work/references/subagent-dispatch.md#L195) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-546 | The start row: two flags on every render | [skills/work/references/subagent-dispatch.md:209](../../../../../claude-autopilot/skills/work/references/subagent-dispatch.md#L209) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-547 | The end row: one call when the dispatch returns | [skills/work/references/subagent-dispatch.md:229](../../../../../claude-autopilot/skills/work/references/subagent-dispatch.md#L229) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-548 | Handoff rows | [skills/work/references/subagent-dispatch.md:249](../../../../../claude-autopilot/skills/work/references/subagent-dispatch.md#L249) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-549 | Marker format | [skills/work/references/task-boundary-handoff.md:9](../../../../../claude-autopilot/skills/work/references/task-boundary-handoff.md#L9) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-550 | Procedure | [skills/work/references/task-boundary-handoff.md:15](../../../../../claude-autopilot/skills/work/references/task-boundary-handoff.md#L15) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-551 | Split criteria | [skills/work/references/task-splitting.md:22](../../../../../claude-autopilot/skills/work/references/task-splitting.md#L22) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-552 | Parallel dispatch for independent rework fixes | [skills/work/references/task-splitting.md:31](../../../../../claude-autopilot/skills/work/references/task-splitting.md#L31) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-553 | Prompt Template | [skills/work/references/test-author-prompt.md:5](../../../../../claude-autopilot/skills/work/references/test-author-prompt.md#L5) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-554 | Context Selection | [skills/work/references/test-author-prompt.md:11](../../../../../claude-autopilot/skills/work/references/test-author-prompt.md#L11) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-555 | Quality gate (step 2.8) | [skills/work/references/test-author-prompt.md:49](../../../../../claude-autopilot/skills/work/references/test-author-prompt.md#L49) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-556 | Style limits on the test files | [skills/work/references/test-author-prompt.md:83](../../../../../claude-autopilot/skills/work/references/test-author-prompt.md#L83) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-557 | Retry Prompt (after quality gate failure) | [skills/work/references/test-author-prompt.md:93](../../../../../claude-autopilot/skills/work/references/test-author-prompt.md#L93) | R06: Replace dispatch and state APIs while retaining task gates and evidence. |
| BEH-558 | Start, attach, detach | [skills/run-autopilot/scripts/README.md:9](../../../../../claude-autopilot/skills/run-autopilot/scripts/README.md#L9) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-559 | Orphans: who continues the loop | [skills/run-autopilot/scripts/README.md:29](../../../../../claude-autopilot/skills/run-autopilot/scripts/README.md#L29) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-560 | Keys | [skills/run-autopilot/scripts/README.md:44](../../../../../claude-autopilot/skills/run-autopilot/scripts/README.md#L44) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-561 | Status legend | [skills/run-autopilot/scripts/README.md:66](../../../../../claude-autopilot/skills/run-autopilot/scripts/README.md#L66) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-562 | Reading the detail header | [skills/run-autopilot/scripts/README.md:80](../../../../../claude-autopilot/skills/run-autopilot/scripts/README.md#L80) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-563 | Agent board (`a`) | [skills/run-autopilot/scripts/README.md:103](../../../../../claude-autopilot/skills/run-autopilot/scripts/README.md#L103) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-564 | On-disk sources (all under `<root>/docs/dev/project-management/autopilot/`) | [skills/run-autopilot/scripts/README.md:133](../../../../../claude-autopilot/skills/run-autopilot/scripts/README.md#L133) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-565 | Code map | [skills/run-autopilot/scripts/README.md:144](../../../../../claude-autopilot/skills/run-autopilot/scripts/README.md#L144) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |
| BEH-566 | Troubleshooting | [skills/run-autopilot/scripts/README.md:165](../../../../../claude-autopilot/skills/run-autopilot/scripts/README.md#L165) | R02: Rebind phase behavior to OVCAQ and tested host capabilities. |

## Named helpers and dependencies

This table records bundled helpers/modules and external integration references named in the docs. Filenames used only as illustrative project files are excluded. A module reference does not imply a separately supported CLI command.

| Row | Helper or dependency | Source | Reason |
| --- | --- | --- | --- |
| UTIL-001 | `__main__.py` | [skills/fast-track/SKILL.md:46](../../../../../claude-autopilot/skills/fast-track/SKILL.md#L46) | R10: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-002 | `_walk_up.py` | [skills/run-autopilot/SKILL.md:97](../../../../../claude-autopilot/skills/run-autopilot/SKILL.md#L97) | R02: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-003 | `autopilot_context_cap_hook.py` | [README.md:39](../../../../../claude-autopilot/README.md#L39) | R01: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-004 | `autopilot_stop_hook.py` | [skills/run-autopilot/references/state-schema.md:227](../../../../../claude-autopilot/skills/run-autopilot/references/state-schema.md#L227) | R26: Declare and test the external integration or its existing fallback. |
| UTIL-005 | `await_reviewer_outputs.py` | [skills/design-solution/SKILL.md:215](../../../../../claude-autopilot/skills/design-solution/SKILL.md#L215) | R03: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-006 | `block_force_push.py` | [skills/run-autopilot/references/model-ladder.md:171](../../../../../claude-autopilot/skills/run-autopilot/references/model-ladder.md#L171) | R26: Declare and test the external integration or its existing fallback. |
| UTIL-007 | `block_poll_loops.py` | [skills/run-autopilot/references/model-ladder.md:171](../../../../../claude-autopilot/skills/run-autopilot/references/model-ladder.md#L171) | R26: Declare and test the external integration or its existing fallback. |
| UTIL-008 | `block_working_document_redirects.py` | [skills/run-autopilot/references/model-ladder.md:168](../../../../../claude-autopilot/skills/run-autopilot/references/model-ladder.md#L168) | R26: Declare and test the external integration or its existing fallback. |
| UTIL-009 | `cap_check.py` | [skills/run-autopilot/references/state-schema.md:547](../../../../../claude-autopilot/skills/run-autopilot/references/state-schema.md#L547) | R02: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-010 | `card.py` | [skills/fast-track/SKILL.md:68](../../../../../claude-autopilot/skills/fast-track/SKILL.md#L68) | R10: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-011 | `cards_from_prd.py` | [skills/fast-track/SKILL.md:231](../../../../../claude-autopilot/skills/fast-track/SKILL.md#L231) | R10: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-012 | `check_memory_pressure.py` | [skills/work/SKILL.md:309](../../../../../claude-autopilot/skills/work/SKILL.md#L309) | R06: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-013 | `check_qwen_output.py` | [skills/work/SKILL.md:316](../../../../../claude-autopilot/skills/work/SKILL.md#L316) | R06: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-014 | `check_reflow.py` | [skills/work/SKILL.md:352](../../../../../claude-autopilot/skills/work/SKILL.md#L352) | R06: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-015 | `check_review_file.py` | [skills/review-blindly/SKILL.md:19](../../../../../claude-autopilot/skills/review-blindly/SKILL.md#L19) | R08: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-016 | `check_split_hygiene.py` | [skills/work/SKILL.md:408](../../../../../claude-autopilot/skills/work/SKILL.md#L408) | R06: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-017 | `check_style_limits.py` | [skills/work/SKILL.md:32](../../../../../claude-autopilot/skills/work/SKILL.md#L32) | R06: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-018 | `classify_tier.py` | [skills/plan-tasks/SKILL.md:246](../../../../../claude-autopilot/skills/plan-tasks/SKILL.md#L246) | R04: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-019 | `codex-run.sh` | [README.md:59](../../../../../claude-autopilot/README.md#L59) | R01: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-020 | `codex_hook_doctor.py` | [skills/use-codex/SKILL.md:94](../../../../../claude-autopilot/skills/use-codex/SKILL.md#L94) | R21: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-021 | `codex_review_run.py` | [skills/use-codex/references/dispatch-contract.md:61](../../../../../claude-autopilot/skills/use-codex/references/dispatch-contract.md#L61) | R21: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-022 | `compute_mech_facts.py` | [skills/fast-track/SKILL.md:265](../../../../../claude-autopilot/skills/fast-track/SKILL.md#L265) | R10: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-023 | `consolidate_findings.py` | [skills/fast-track/SKILL.md:415](../../../../../claude-autopilot/skills/fast-track/SKILL.md#L415) | R10: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-024 | `detect_tautological_tests.py` | [skills/review-work-completion/SKILL.md:170](../../../../../claude-autopilot/skills/review-work-completion/SKILL.md#L170) | R07: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-025 | `detect_usage_limit.py` | [skills/use-sonnet/SKILL.md:16](../../../../../claude-autopilot/skills/use-sonnet/SKILL.md#L16) | R21: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-026 | `diagnose_task.py` | [skills/work/references/gate-failure.md:35](../../../../../claude-autopilot/skills/work/references/gate-failure.md#L35) | R06: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-027 | `discovery.py` | [skills/run-autopilot/scripts/README.md:149](../../../../../claude-autopilot/skills/run-autopilot/scripts/README.md#L149) | R02: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-028 | `eligibility.py` | [skills/run-autopilot/references/phase-build.md:240](../../../../../claude-autopilot/skills/run-autopilot/references/phase-build.md#L240) | R02: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-029 | `enforce_prd_location.py` | [README.md:44](../../../../../claude-autopilot/README.md#L44) | R01: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-030 | `enforce_write_scope.py` | [skills/run-autopilot/SKILL.md:66](../../../../../claude-autopilot/skills/run-autopilot/SKILL.md#L66) | R26: Declare and test the external integration or its existing fallback. |
| UTIL-031 | `enter.py` | [skills/run-autopilot/references/phase-build.md:35](../../../../../claude-autopilot/skills/run-autopilot/references/phase-build.md#L35) | R02: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-032 | `fable-run.sh` | [skills/review-work-completion/references/agent-invocation.md:116](../../../../../claude-autopilot/skills/review-work-completion/references/agent-invocation.md#L116) | R26: Declare and test the external integration or its existing fallback. |
| UTIL-033 | `fablectl.py` | [skills/run-autopilot/references/model-ladder.md:91](../../../../../claude-autopilot/skills/run-autopilot/references/model-ladder.md#L91) | R02: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-034 | `fast_track_plan.py` | [skills/fast-track/SKILL.md:109](../../../../../claude-autopilot/skills/fast-track/SKILL.md#L109) | R10: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-035 | `frontmatter.py` | [skills/run-autopilot/references/phase-build.md:220](../../../../../claude-autopilot/skills/run-autopilot/references/phase-build.md#L220) | R02: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-036 | `gate.py` | [skills/review-work-completion/SKILL.md:403](../../../../../claude-autopilot/skills/review-work-completion/SKILL.md#L403) | R07: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-037 | `gateguard-fact-force.py` | [skills/run-autopilot/references/model-ladder.md:169](../../../../../claude-autopilot/skills/run-autopilot/references/model-ladder.md#L169) | R26: Declare and test the external integration or its existing fallback. |
| UTIL-038 | `gather-context.sh` | [skills/review-work-completion/SKILL.md:140](../../../../../claude-autopilot/skills/review-work-completion/SKILL.md#L140) | R07: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-039 | `gemini-run.sh` | [README.md:60](../../../../../claude-autopilot/README.md#L60) | R01: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-040 | `github-state.sh` | [skills/run-autopilot/references/phase-build.md:299](../../../../../claude-autopilot/skills/run-autopilot/references/phase-build.md#L299) | R26: Declare and test the external integration or its existing fallback. |
| UTIL-041 | `guard_phase_delegation.py` | [README.md:35](../../../../../claude-autopilot/README.md#L35) | R01: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-042 | `guard_push_on_critical.py` | [README.md:49](../../../../../claude-autopilot/README.md#L49) | R01: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-043 | `guard_skill_after_leave.py` | [README.md:36](../../../../../claude-autopilot/README.md#L36) | R01: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-044 | `guard_stop_on_live_lanes.py` | [README.md:38](../../../../../claude-autopilot/README.md#L38) | R01: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-045 | `lane.py` | [skills/run-autopilot/references/phase-build.md:253](../../../../../claude-autopilot/skills/run-autopilot/references/phase-build.md#L253) | R02: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-046 | `list-prds.sh` | [skills/plan-tasks/SKILL.md:22](../../../../../claude-autopilot/skills/plan-tasks/SKILL.md#L22) | R04: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-047 | `loop.py` | [skills/run-autopilot/SKILL.md:41](../../../../../claude-autopilot/skills/run-autopilot/SKILL.md#L41) | R02: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-048 | `loop_decision.py` | [skills/run-autopilot/references/state-schema.md:169](../../../../../claude-autopilot/skills/run-autopilot/references/state-schema.md#L169) | R02: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-049 | `model.py` | [skills/run-autopilot/references/dashboard-format.md:49](../../../../../claude-autopilot/skills/run-autopilot/references/dashboard-format.md#L49) | R02: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-050 | `note_session_leave.py` | [README.md:37](../../../../../claude-autopilot/README.md#L37) | R01: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-051 | `notify.py` | [README.md:110](../../../../../claude-autopilot/README.md#L110) | R26: Declare and test the external integration or its existing fallback. |
| UTIL-052 | `panels.py` | [skills/run-autopilot/scripts/README.md:152](../../../../../claude-autopilot/skills/run-autopilot/scripts/README.md#L152) | R02: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-053 | `parse_review.py` | [skills/work/SKILL.md:436](../../../../../claude-autopilot/skills/work/SKILL.md#L436) | R06: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-054 | `policy.py` | [skills/plan-tasks/SKILL.md:391](../../../../../claude-autopilot/skills/plan-tasks/SKILL.md#L391) | R04: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-055 | `prefer_tools.py` | [skills/run-autopilot/references/model-ladder.md:171](../../../../../claude-autopilot/skills/run-autopilot/references/model-ladder.md#L171) | R26: Declare and test the external integration or its existing fallback. |
| UTIL-056 | `qwen-run.sh` | [skills/run-autopilot/references/state-schema.md:214](../../../../../claude-autopilot/skills/run-autopilot/references/state-schema.md#L214) | R26: Declare and test the external integration or its existing fallback. |
| UTIL-057 | `record_dispatch.py` | [skills/fast-track/SKILL.md:142](../../../../../claude-autopilot/skills/fast-track/SKILL.md#L142) | R10: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-058 | `record_item.py` | [skills/fast-track/SKILL.md:646](../../../../../claude-autopilot/skills/fast-track/SKILL.md#L646) | R10: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-059 | `records.py` | [skills/review-work-completion/SKILL.md:298](../../../../../claude-autopilot/skills/review-work-completion/SKILL.md#L298) | R07: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-060 | `reinject_contract_card.py` | [skills/run-autopilot/SKILL.md:228](../../../../../claude-autopilot/skills/run-autopilot/SKILL.md#L228) | R26: Declare and test the external integration or its existing fallback. |
| UTIL-061 | `render_audit.py` | [skills/run-autopilot/references/audit-log-format.md:9](../../../../../claude-autopilot/skills/run-autopilot/references/audit-log-format.md#L9) | R02: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-062 | `render_prompt.py` | [skills/fast-track/SKILL.md:125](../../../../../claude-autopilot/skills/fast-track/SKILL.md#L125) | R10: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-063 | `render_report.py` | [skills/run-autopilot/references/batch-report-format.md:14](../../../../../claude-autopilot/skills/run-autopilot/references/batch-report-format.md#L14) | R02: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-064 | `render_stream.py` | [skills/run-autopilot/SKILL.md:47](../../../../../claude-autopilot/skills/run-autopilot/SKILL.md#L47) | R02: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-065 | `replay_tests_against_base.py` | [skills/review-work-completion/SKILL.md:170](../../../../../claude-autopilot/skills/review-work-completion/SKILL.md#L170) | R07: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-066 | `resume.py` | [skills/run-autopilot/SKILL.md:105](../../../../../claude-autopilot/skills/run-autopilot/SKILL.md#L105) | R02: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-067 | `resume_target.py` | [skills/run-autopilot/SKILL.md:105](../../../../../claude-autopilot/skills/run-autopilot/SKILL.md#L105) | R02: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-068 | `review_close.py` | [skills/review-work-completion/references/output-formats.md:271](../../../../../claude-autopilot/skills/review-work-completion/references/output-formats.md#L271) | R07: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-069 | `review_coverage_hook.py` | [README.md:40](../../../../../claude-autopilot/README.md#L40) | R01: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-070 | `review_stage.py` | [skills/review-work-completion/SKILL.md:165](../../../../../claude-autopilot/skills/review-work-completion/SKILL.md#L165) | R07: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-071 | `routing.py` | [skills/plan-tasks/SKILL.md:242](../../../../../claude-autopilot/skills/plan-tasks/SKILL.md#L242) | R04: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-072 | `runner.py` | [skills/run-autopilot/SKILL.md:171](../../../../../claude-autopilot/skills/run-autopilot/SKILL.md#L171) | R02: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-073 | `schema.py` | [skills/run-autopilot/references/state-schema.md:199](../../../../../claude-autopilot/skills/run-autopilot/references/state-schema.md#L199) | R02: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-074 | `screens.py` | [skills/run-autopilot/scripts/README.md:153](../../../../../claude-autopilot/skills/run-autopilot/scripts/README.md#L153) | R02: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-075 | `selection.py` | [skills/run-autopilot/references/phase-build.md:174](../../../../../claude-autopilot/skills/run-autopilot/references/phase-build.md#L174) | R02: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-076 | `sonnet-run.sh` | [README.md:147](../../../../../claude-autopilot/README.md#L147) | R01: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-077 | `statectl.py` | [skills/plan-tasks/SKILL.md:72](../../../../../claude-autopilot/skills/plan-tasks/SKILL.md#L72) | R04: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-078 | `status.py` | [skills/run-autopilot/references/dashboard-format.md:4](../../../../../claude-autopilot/skills/run-autopilot/references/dashboard-format.md#L4) | R02: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-079 | `store_tree.py` | [skills/run-autopilot/SKILL.md:263](../../../../../claude-autopilot/skills/run-autopilot/SKILL.md#L263) | R02: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-080 | `stream.py` | [skills/run-autopilot/scripts/README.md:150](../../../../../claude-autopilot/skills/run-autopilot/scripts/README.md#L150) | R02: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-081 | `tracon.py` | [skills/run-autopilot/references/dashboard-format.md:21](../../../../../claude-autopilot/skills/run-autopilot/references/dashboard-format.md#L21) | R02: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-082 | `tracon_wrapper_alive.py` | [skills/run-autopilot/SKILL.md:140](../../../../../claude-autopilot/skills/run-autopilot/SKILL.md#L140) | R02: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-083 | `transitions.py` | [skills/run-autopilot/SKILL.md:200](../../../../../claude-autopilot/skills/run-autopilot/SKILL.md#L200) | R02: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-084 | `tune_routing.py` | [skills/run-autopilot/references/model-ladder.md:278](../../../../../claude-autopilot/skills/run-autopilot/references/model-ladder.md#L278) | R02: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-085 | `validate_commit_msg.py` | [skills/work/SKILL.md:367](../../../../../claude-autopilot/skills/work/SKILL.md#L367) | R26: Declare and test the external integration or its existing fallback. |
| UTIL-086 | `validate_state_json_hook.py` | [README.md:41](../../../../../claude-autopilot/README.md#L41) | R01: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-087 | `wave.py` | [skills/run-autopilot/references/waves.md:5](../../../../../claude-autopilot/skills/run-autopilot/references/waves.md#L5) | R02: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-088 | `wave_assemble.py` | [skills/run-autopilot/references/state-schema.md:258](../../../../../claude-autopilot/skills/run-autopilot/references/state-schema.md#L258) | R02: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-089 | `wave_launch.py` | [skills/run-autopilot/references/state-schema.md:258](../../../../../claude-autopilot/skills/run-autopilot/references/state-schema.md#L258) | R02: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-090 | `wave_review.py` | [skills/run-autopilot/references/state-schema.md:258](../../../../../claude-autopilot/skills/run-autopilot/references/state-schema.md#L258) | R02: Retain its documented contract; relocate or rebind to the appropriate owner. |
| UTIL-091 | `work_routing.py` | [skills/work/SKILL.md:389](../../../../../claude-autopilot/skills/work/SKILL.md#L389) | R06: Retain its documented contract; relocate or rebind to the appropriate owner. |

## Configuration and state contract

Every field row of `skills/run-autopilot/references/state-schema.md` remains within R12’s schema-mapping obligation. Provider-specific fields retired by OVCAQ require a capability/event mapping or an explicit unresolved parity item; absence is not permission to lose behavior. Environment switches and PRD frontmatter are governed by the linked source procedures, including defaults and invalid-value behavior.

## Unresolved questions

- Which documented options or helpers have no semantic equivalent after the OVCAQ contract mapping? Keep them as parity blockers until resolved.

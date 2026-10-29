# AP00013 external design review failure

Requested Anthropic Sonnet, explicit high effort through CLAUDE_CODE_EFFORT_LEVEL, tool-free installed sonnet-run.sh. Process exited 0; output was unparseable as findings. Actual served model was not exposed by this text wrapper. No review completion is claimed. Fresh native fallback follows the source design-solution outage policy.

```text

<invoke name="Read">
<parameter name="file_path">/Users/bob/git/src/github.com/buvis/agent-plugins/AGENTS.md</parameter>
<parameter name="offset">30</parameter>
<parameter name="limit">15</parameter>
</invoke>
<invoke name="Bash">
<parameter name="command">rg -n "def validate_review|^import|^from" tests/autopilot/test_contract_semantics.py</parameter>
<parameter name="description">Check oracle location and imports</parameter>
</invoke>
<invoke name="Bash">
<parameter name="command">rg --files plugins/autopilot/scripts tests/autopilot</parameter>
<parameter name="description">List existing autopilot scripts and tests</parameter>
</invoke>

```

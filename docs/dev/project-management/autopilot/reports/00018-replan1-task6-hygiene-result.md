No edit: `CONTRACT` is a required public export at `tests/autopilot/controller_cli_support.py:17`. Both bootstrap test modules import it (lines 15 and 13). Deletion would break those imports. The file-local unused finding is unsupported; deletion-only scope permits no fix.

Tests not run; no changes made.

ASSUMPTIONS: none
FILES_TOUCHED: none
"""specflow helper: hashes, state, validation, and status from repository files alone."""

WORKFLOW_VERSION = "0.1.0"

# Registers the checks of 00005 and 00006 in CHECKS, whichever module is imported first.
from . import phase_checks as phase_checks
from . import structural as structural

"""specflow helper: hashes, state, validation, and status from repository files alone."""

WORKFLOW_VERSION = "0.1.0"

# Registers the structural checks of 00005 in CHECKS, whichever module is imported first.
from . import structural as structural

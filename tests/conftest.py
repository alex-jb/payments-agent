"""Test isolation guard.

Sets SFOS_TEST_MODE=1 so any code path calling solo_founder_os.log_outcome
/ record_example / log_edit during pytest does NOT write to the
developer's real ~/.<agent>/ dirs.

SFOS-side primitive shipped in solo-founder-os v0.20.3.
"""
import os

os.environ.setdefault("SFOS_TEST_MODE", "1")

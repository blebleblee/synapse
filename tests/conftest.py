"""
Pytest configuration for Synapse
Ensures root workspace is in sys.path and isolates test environment.
"""

import sys
import os
import pytest
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

@pytest.fixture(autouse=True)
def isolate_test_auth(monkeypatch):
    """
    By default, tests run in open single-user mode (auth disabled)
    so standard endpoint functional tests pass without needing tokens.
    Authentication-specific tests in test_auth.py explicitly set SYNAPSE_PASSWORD.
    """
    monkeypatch.delenv("SYNAPSE_PASSWORD", raising=False)
    monkeypatch.delenv("SYNAPSE_AUTH_PASSWORD", raising=False)

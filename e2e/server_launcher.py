"""
Isolated Server Launcher for End-to-End Browser Tests.
Runs Uvicorn on 127.0.0.1 on the specified test port with:
- Pre-import path overrides pointing strictly to temporary test directories.
- Prevention of external .env or user-level config loading.
- In-process Ollama socket probe suppression matching expected return types.
- Unaltered application authentication and routing logic in single-user mode.
"""

import sys
import os
import pathlib
from pathlib import Path

# Verify that mandatory isolation environment variables are present before any imports
for var in ("SYNAPSE_WORKSPACE", "SYNAPSE_TOPICS_DIR", "SYNAPSE_DB_PATH"):
    if not os.environ.get(var):
        sys.stderr.write(f"FATAL: Missing required isolation variable: {var}\n")
        sys.exit(1)

# Ensure root repository is in sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Prevent loading external ~/.config/synapse/env or local .env files into this test server
_orig_exists = pathlib.Path.exists

def _safe_exists(self):
    s = str(self)
    if ".config/synapse/env" in s or s.endswith("/.env"):
        return False
    return _orig_exists(self)

pathlib.Path.exists = _safe_exists

# Purge any inherited secrets/credentials from environment
for key in list(os.environ.keys()):
    if any(term in key for term in ("KEY", "PASS", "TOKEN", "SECRET")):
        os.environ.pop(key, None)
os.environ.pop("SYNAPSE_PASSWORD", None)
os.environ.pop("SYNAPSE_AUTH_PASSWORD", None)

# Confine Ollama probe suppression to this child process with matching return types
import learning_engine.models as le_models
le_models.OllamaProvider.check_connectivity = lambda host, model=None: False
le_models.OllamaProvider.is_available = lambda host="", timeout=1.5: False
le_models.OllamaCluster.get_cluster_status = lambda self: {
    "http://127.0.0.1:0": {"online": False, "models": []}
}

import uvicorn
from app.backend.main import app

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.stderr.write("Usage: python server_launcher.py <port>\n")
        sys.exit(1)

    port = int(sys.argv[1])
    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=port,
        log_level="info",
        access_log=False
    )
    server = uvicorn.Server(config)
    server.run()

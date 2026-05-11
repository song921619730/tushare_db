"""Strategy/param audit must pass with no BUGs (warns ok during transition)."""
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def test_no_strategy_param_bugs():
    result = subprocess.run(
        [sys.executable, "scripts/audit_strategy_param_mismatch.py"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"Strategy/param audit failed:\n{result.stdout}\n{result.stderr}"
    )

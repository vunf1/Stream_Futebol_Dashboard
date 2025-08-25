import os
import subprocess
from pathlib import Path

import pytest


def _run_mypy(args: list[str]) -> tuple[str, str, int]:
    """Run mypy via API if available, else fall back to CLI."""
    try:
        from mypy import api as mypy_api  # type: ignore
        stdout, stderr, exit_status = mypy_api.run(args)
        return stdout, stderr, exit_status
    except Exception:
        # Fallback to CLI invocation
        cmd = [
            os.fspath(Path(os.sys.executable)),
            "-m",
            "mypy",
            *args,
        ]
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=Path(__file__).resolve().parents[1],
        )
        return proc.stdout, proc.stderr, proc.returncode


def test_mypy_clean():
    project_root = Path(__file__).resolve().parents[1]
    config_path = project_root / "mypy.ini"

    args = [
        "--config-file",
        str(config_path),
        "--no-error-summary",
        "--show-error-codes",
        "--no-color-output",
        # Limit scope to core/config/utils to avoid GUI/lib stub noise
        "src/core",
        "src/config",
        "src/utils",
    ]

    stdout, stderr, exit_status = _run_mypy(args)

    combined = (stdout or "") + (stderr or "")
    if "No module named mypy" in combined or (
        exit_status == 2 and ("No module named" in combined)
    ):
        pytest.fail(
            "mypy is not installed in this environment. Install it to run type checks:\n"
            "  pip install mypy\n"
            "Or install all dev deps:\n"
            "  pip install -r requirements.txt"
        )

    if exit_status != 0:
        out = (stdout or "").strip()
        err = (stderr or "").strip()
        snippet = (out + ("\n\n" + err if err else "")).strip()
        if len(snippet) > 4000:
            snippet = snippet[:4000] + "\n... (truncated)"
        pytest.fail(f"mypy reported issues (exit {exit_status}):\n\n{snippet}")



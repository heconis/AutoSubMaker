from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Sequence


def run_command(
    command: Sequence[str],
    cwd: str | Path | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        check=True,
        capture_output=True,
        text=True,
    )


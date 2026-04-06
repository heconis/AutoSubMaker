from __future__ import annotations

import locale
import subprocess
from pathlib import Path
from typing import Sequence


def decode_process_output(payload: bytes | str | None) -> str:
    if payload is None:
        return ""
    if isinstance(payload, str):
        return payload

    preferred_encoding = locale.getpreferredencoding(False)
    tried: set[str] = set()
    for encoding in ("utf-8", preferred_encoding, "cp932"):
        normalized = encoding.lower()
        if normalized in tried:
            continue
        tried.add(normalized)
        try:
            return payload.decode(encoding)
        except UnicodeDecodeError:
            continue

    return payload.decode("utf-8", errors="replace")


def run_command(
    command: Sequence[str],
    cwd: str | Path | None = None,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=False,
    )
    stdout = decode_process_output(result.stdout)
    stderr = decode_process_output(result.stderr)

    if result.returncode != 0:
        raise subprocess.CalledProcessError(
            result.returncode,
            result.args,
            output=stdout,
            stderr=stderr,
        )

    return subprocess.CompletedProcess(
        args=result.args,
        returncode=result.returncode,
        stdout=stdout,
        stderr=stderr,
    )

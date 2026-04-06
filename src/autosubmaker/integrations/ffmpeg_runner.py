from __future__ import annotations

from pathlib import Path

from autosubmaker.utils.process_runner import run_command


class FFmpegRunner:
    def __init__(self, ffmpeg_path: str | Path) -> None:
        self.ffmpeg_path = str(ffmpeg_path)

    def get_version(self) -> str:
        result = run_command([self.ffmpeg_path, "-version"])
        return result.stdout.splitlines()[0] if result.stdout else "unknown"


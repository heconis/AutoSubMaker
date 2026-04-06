from __future__ import annotations

import shutil
from pathlib import Path

from autosubmaker.utils.process_runner import run_command


class FFmpegRunner:
    def __init__(self, ffmpeg_path: str | Path) -> None:
        self.ffmpeg_path = str(ffmpeg_path)

    def get_version(self) -> str:
        result = run_command([self.ffmpeg_path, "-version"])
        return result.stdout.splitlines()[0] if result.stdout else "unknown"


def resolve_ffprobe_path(ffmpeg_path: str | Path) -> Path | None:
    ffmpeg_candidate = Path(ffmpeg_path)
    sibling_name = "ffprobe.exe" if ffmpeg_candidate.suffix.lower() == ".exe" else "ffprobe"
    sibling_path = ffmpeg_candidate.with_name(sibling_name)
    if sibling_path.exists():
        return sibling_path.resolve()

    discovered_path = shutil.which("ffprobe")
    if discovered_path:
        return Path(discovered_path).resolve()

    return None

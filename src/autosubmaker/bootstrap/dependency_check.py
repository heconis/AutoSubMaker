from __future__ import annotations

import shutil
from pathlib import Path


def resolve_ffmpeg_path(
    configured_path: str | None,
    managed_executable: Path,
) -> Path | None:
    candidates: list[Path] = []

    if configured_path:
        candidates.append(Path(configured_path).expanduser())

    candidates.append(managed_executable)

    discovered_path = shutil.which("ffmpeg")
    if discovered_path:
        candidates.append(Path(discovered_path))

    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate.resolve()

    return None


def resolve_whisper_model_dir(models_root: Path, model_size: str) -> Path:
    return models_root / model_size


def is_model_available(model_dir: Path) -> bool:
    return model_dir.exists() and any(model_dir.iterdir())


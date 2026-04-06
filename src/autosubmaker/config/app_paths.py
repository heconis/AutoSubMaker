from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


APP_NAME = "AutoSubMaker"


def get_default_root_dir() -> Path:
    local_appdata = os.environ.get("LOCALAPPDATA")
    if local_appdata:
        return Path(local_appdata) / APP_NAME

    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / APP_NAME

    return Path.home() / f".{APP_NAME.lower()}"


@dataclass(slots=True)
class AppPaths:
    root: Path
    config_dir: Path
    bin_dir: Path
    ffmpeg_dir: Path
    ffmpeg_executable: Path
    models_dir: Path
    whisper_models_dir: Path
    logs_dir: Path
    temp_dir: Path
    outputs_dir: Path
    settings_file: Path
    log_file: Path

    @classmethod
    def default(cls) -> "AppPaths":
        root = get_default_root_dir()
        config_dir = root / "config"
        bin_dir = root / "bin"
        ffmpeg_dir = bin_dir / "ffmpeg"
        ffmpeg_executable = ffmpeg_dir / "ffmpeg.exe"
        models_dir = root / "models"
        whisper_models_dir = models_dir / "whisper"
        logs_dir = root / "logs"
        temp_dir = root / "temp"
        outputs_dir = root / "outputs"
        settings_file = config_dir / "settings.json"
        log_file = logs_dir / "autosubmaker.log"

        return cls(
            root=root,
            config_dir=config_dir,
            bin_dir=bin_dir,
            ffmpeg_dir=ffmpeg_dir,
            ffmpeg_executable=ffmpeg_executable,
            models_dir=models_dir,
            whisper_models_dir=whisper_models_dir,
            logs_dir=logs_dir,
            temp_dir=temp_dir,
            outputs_dir=outputs_dir,
            settings_file=settings_file,
            log_file=log_file,
        )

    def ensure_directories(self) -> None:
        for directory in (
            self.root,
            self.config_dir,
            self.bin_dir,
            self.ffmpeg_dir,
            self.models_dir,
            self.whisper_models_dir,
            self.logs_dir,
            self.temp_dir,
            self.outputs_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)


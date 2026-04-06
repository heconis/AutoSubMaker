from __future__ import annotations

from pathlib import Path

from autosubmaker.config.app_paths import AppPaths
from autosubmaker.services.temp_file_service import TempFileService
from autosubmaker.utils.logger import LogStore


def build_paths(root: Path) -> AppPaths:
    return AppPaths(
        root=root,
        config_dir=root / "config",
        bin_dir=root / "bin",
        ffmpeg_dir=root / "bin" / "ffmpeg",
        ffmpeg_executable=root / "bin" / "ffmpeg" / "ffmpeg.exe",
        models_dir=root / "models",
        whisper_models_dir=root / "models" / "whisper",
        logs_dir=root / "logs",
        temp_dir=root / "temp",
        outputs_dir=root / "outputs",
        settings_file=root / "config" / "settings.json",
        log_file=root / "logs" / "autosubmaker.log",
    )


def test_cleanup_job_temp_dir_removes_directory(tmp_path: Path) -> None:
    paths = build_paths(tmp_path)
    paths.ensure_directories()
    temp_dir = paths.temp_dir / "job123"
    temp_dir.mkdir(parents=True, exist_ok=True)
    (temp_dir / "sample.txt").write_text("temp", encoding="utf-8")
    service = TempFileService(paths=paths, log_store=LogStore(paths.log_file))

    removed = service.cleanup_job_temp_dir("job123")

    assert removed is True
    assert not temp_dir.exists()


def test_cleanup_job_temp_dir_returns_false_when_missing(tmp_path: Path) -> None:
    paths = build_paths(tmp_path)
    paths.ensure_directories()
    service = TempFileService(paths=paths, log_store=LogStore(paths.log_file))

    assert service.cleanup_job_temp_dir("missing") is False

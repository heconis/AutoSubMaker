from __future__ import annotations

from pathlib import Path

from autosubmaker.config.app_paths import AppPaths
from autosubmaker.config.app_settings import AppSettings
from autosubmaker.models.job import Job
from autosubmaker.services.burnin_service import BurnInService
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


def test_burnin_service_builds_output_and_filter_input(tmp_path: Path) -> None:
    paths = build_paths(tmp_path)
    paths.ensure_directories()
    output_dir = tmp_path / "out"
    output_dir.mkdir(parents=True, exist_ok=True)
    input_path = tmp_path / "sample.mp4"
    input_path.write_text("video", encoding="utf-8")
    ass_path = output_dir / "sample.ass"
    ass_path.write_text("[Script Info]\n", encoding="utf-8")

    captured: list[list[str]] = []

    def fake_runner(command: list[str]):
        captured.append(command)
        Path(command[-1]).write_text("rendered", encoding="utf-8")
        return None

    service = BurnInService(
        paths=paths,
        log_store=LogStore(paths.log_file),
        command_runner=fake_runner,
    )
    settings = AppSettings()
    job = Job(
        input_path=str(input_path),
        output_dir=str(output_dir),
        burn_in_video=True,
        subtitle_only=True,
    )
    job.ass_path = str(ass_path)

    output_path = service.burn_in(job, ffmpeg_path="ffmpeg.exe", settings=settings)

    assert output_path.name == "sample_subtitled.mp4"
    assert output_path.exists()
    assert captured
    command = captured[0]
    assert command[:4] == ["ffmpeg.exe", "-y", "-i", str(input_path)]
    assert "-vf" in command
    filter_arg = command[command.index("-vf") + 1]
    assert "ass='" in filter_arg
    copied_ass = paths.temp_dir / job.id / "burnin_input.ass"
    assert copied_ass.exists()


def test_burnin_service_uses_unique_name_when_target_exists(tmp_path: Path) -> None:
    paths = build_paths(tmp_path)
    paths.ensure_directories()
    output_dir = tmp_path / "out"
    output_dir.mkdir(parents=True, exist_ok=True)
    input_path = tmp_path / "sample.mp4"
    input_path.write_text("video", encoding="utf-8")
    ass_path = output_dir / "sample.ass"
    ass_path.write_text("[Script Info]\n", encoding="utf-8")
    existing_output = output_dir / "sample_subtitled.mp4"
    existing_output.write_text("already", encoding="utf-8")

    def fake_runner(command: list[str]):
        Path(command[-1]).write_text("rendered", encoding="utf-8")
        return None

    service = BurnInService(
        paths=paths,
        log_store=LogStore(paths.log_file),
        command_runner=fake_runner,
    )
    job = Job(
        input_path=str(input_path),
        output_dir=str(output_dir),
        burn_in_video=True,
        subtitle_only=True,
    )
    job.ass_path = str(ass_path)

    output_path = service.burn_in(job, ffmpeg_path="ffmpeg.exe", settings=AppSettings())

    assert output_path.name == "sample_subtitled_1.mp4"


def test_burnin_service_raises_without_ass_path(tmp_path: Path) -> None:
    paths = build_paths(tmp_path)
    paths.ensure_directories()
    service = BurnInService(paths=paths, log_store=LogStore(paths.log_file))
    job = Job(
        input_path=str(tmp_path / "sample.mp4"),
        output_dir=str(tmp_path / "out"),
        burn_in_video=True,
        subtitle_only=True,
    )

    try:
        service.burn_in(job, ffmpeg_path="ffmpeg.exe", settings=AppSettings())
        assert False, "expected RuntimeError"
    except RuntimeError as exc:
        assert "ASS 字幕" in str(exc)

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Callable

from autosubmaker.config.app_paths import AppPaths
from autosubmaker.config.app_settings import AppSettings
from autosubmaker.models.job import Job
from autosubmaker.utils.logger import LogStore
from autosubmaker.utils.process_runner import run_command


class BurnInService:
    def __init__(
        self,
        paths: AppPaths,
        log_store: LogStore,
        command_runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
    ) -> None:
        self.paths = paths
        self.log_store = log_store
        self.command_runner = command_runner or run_command

    def burn_in(
        self,
        job: Job,
        ffmpeg_path: str | Path,
        settings: AppSettings,
    ) -> Path:
        if not job.ass_path:
            raise RuntimeError("焼きこみ用の ASS 字幕が見つかりません。")

        source_video_path = Path(job.input_path)
        source_ass_path = Path(job.ass_path)
        if not source_ass_path.exists():
            raise RuntimeError(f"焼きこみ用 ASS が見つかりません: {source_ass_path}")

        output_path = self._build_output_path(job, settings)
        filter_ass_path = self._prepare_filter_ass_path(source_ass_path, job.id)
        filter_arg = f"ass='{self._escape_filter_path(filter_ass_path)}'"

        command = [
            str(ffmpeg_path),
            "-y",
            "-i",
            str(source_video_path),
            "-map",
            "0:v:0",
            "-map",
            "0:a?",
            "-vf",
            filter_arg,
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "copy",
        ]
        if output_path.suffix.lower() in {".mp4", ".m4v", ".mov"}:
            command.extend(["-movflags", "+faststart"])
        command.append(str(output_path))

        try:
            self.command_runner(command)
        except subprocess.CalledProcessError as exc:
            detail = (exc.stderr or exc.stdout or str(exc)).strip()
            raise RuntimeError(f"字幕焼きこみに失敗しました: {detail}") from exc

        self.log_store.add(f"字幕焼きこみが完了しました: {output_path}")
        return output_path

    def _build_output_path(self, job: Job, settings: AppSettings) -> Path:
        source_path = Path(job.input_path)
        output_dir = Path(job.output_dir).expanduser()
        output_dir.mkdir(parents=True, exist_ok=True)

        suffix = settings.subtitles.output_suffix.strip() or "_subtitled"
        stem = source_path.stem
        extension = source_path.suffix or ".mp4"
        candidate = output_dir / f"{stem}{suffix}{extension}"
        if candidate.resolve() != source_path.resolve() and not candidate.exists():
            return candidate

        index = 1
        while True:
            candidate = output_dir / f"{stem}{suffix}_{index}{extension}"
            if candidate.resolve() != source_path.resolve() and not candidate.exists():
                return candidate
            index += 1

    def _prepare_filter_ass_path(self, source_ass_path: Path, job_id: str) -> Path:
        job_temp_dir = self.paths.temp_dir / job_id
        job_temp_dir.mkdir(parents=True, exist_ok=True)
        filter_ass_path = job_temp_dir / "burnin_input.ass"
        shutil.copyfile(source_ass_path, filter_ass_path)
        return filter_ass_path

    def _escape_filter_path(self, path: Path) -> str:
        normalized = path.resolve().as_posix()
        return (
            normalized
            .replace("\\", "/")
            .replace(":", r"\:")
            .replace("'", r"\'")
        )

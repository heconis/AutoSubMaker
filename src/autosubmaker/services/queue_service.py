from __future__ import annotations

from pathlib import Path

from autosubmaker.config.app_settings import AppSettings
from autosubmaker.models.job import Job, JobStatus


SUPPORTED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".m4v"}


class QueueService:
    def __init__(self) -> None:
        self._jobs: list[Job] = []

    @property
    def jobs(self) -> list[Job]:
        return list(self._jobs)

    def add_paths(self, raw_paths: list[str], settings: AppSettings) -> tuple[list[Job], list[str]]:
        added_jobs: list[Job] = []
        errors: list[str] = []
        known_paths = {Path(job.input_path).resolve() for job in self._jobs}

        for raw_path in raw_paths:
            normalized = raw_path.strip().strip('"')
            if not normalized:
                continue

            candidate = Path(normalized).expanduser()
            if not candidate.exists():
                errors.append(f"見つかりません: {candidate}")
                continue

            if not candidate.is_file():
                errors.append(f"ファイルではありません: {candidate}")
                continue

            if candidate.suffix.lower() not in SUPPORTED_VIDEO_EXTENSIONS:
                errors.append(f"未対応拡張子です: {candidate.name}")
                continue

            resolved = candidate.resolve()
            if resolved in known_paths:
                errors.append(f"すでに追加済みです: {candidate.name}")
                continue

            job = Job(
                input_path=str(resolved),
                output_dir=settings.output_dir or str(candidate.parent),
                burn_in_video=settings.subtitles.burn_in_video,
                subtitle_only=settings.subtitles.emit_srt or settings.subtitles.emit_ass,
            )
            self._jobs.append(job)
            known_paths.add(resolved)
            added_jobs.append(job)

        return added_jobs, errors

    def clear_completed(self) -> int:
        before_count = len(self._jobs)
        self._jobs = [job for job in self._jobs if job.status is not JobStatus.COMPLETED]
        return before_count - len(self._jobs)

    def retry_failed(self) -> int:
        retried = 0
        for job in self._jobs:
            if job.status is JobStatus.FAILED:
                job.status = JobStatus.QUEUED
                job.progress = 0
                job.error_message = None
                retried += 1
        return retried

    def as_rows(self) -> list[dict[str, str | int]]:
        return [job.to_row() for job in self._jobs]


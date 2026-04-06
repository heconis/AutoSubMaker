from __future__ import annotations

from autosubmaker.bootstrap.dependency_check import (
    resolve_ffmpeg_path,
)
from autosubmaker.config.app_paths import AppPaths
from autosubmaker.config.app_settings import AppSettings
from autosubmaker.models.app_status import DependencyState, DependencyStatus, StartupState
from autosubmaker.services.whisper_model_service import WhisperModelService


class EnvironmentService:
    def __init__(
        self,
        paths: AppPaths,
        whisper_model_service: WhisperModelService,
    ) -> None:
        self.paths = paths
        self.whisper_model_service = whisper_model_service

    def inspect(self, settings: AppSettings) -> StartupState:
        ffmpeg_path = resolve_ffmpeg_path(settings.ffmpeg_path, self.paths.ffmpeg_executable)
        if ffmpeg_path:
            ffmpeg_status = DependencyStatus(
                name="FFmpeg",
                state=DependencyState.READY,
                message=f"利用可能: {ffmpeg_path}",
                path=str(ffmpeg_path),
            )
        else:
            ffmpeg_status = DependencyStatus(
                name="FFmpeg",
                state=DependencyState.MISSING,
                message="未検出です。手動指定または自動ダウンロードが必要です。",
            )

        whisper_status = self.whisper_model_service.build_dependency_status(
            settings.transcription.model_size
        )

        return StartupState(
            app_root=self.paths.root,
            ffmpeg=ffmpeg_status,
            whisper_model=whisper_status,
            notes=[
                f"FFmpeg 管理先: {self.paths.ffmpeg_dir}",
                f"Whisper モデル管理先: {self.paths.whisper_models_dir}",
            ],
        )

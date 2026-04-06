from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from pathlib import Path
from threading import Lock, Thread
import warnings

from autosubmaker.bootstrap.dependency_check import is_model_available, resolve_whisper_model_dir
from autosubmaker.config.app_paths import AppPaths
from autosubmaker.models.app_status import DependencyState, DependencyStatus
from autosubmaker.utils.logger import LogStore


class ModelDownloadPhase(str, Enum):
    IDLE = "idle"
    DOWNLOADING = "downloading"
    READY = "ready"
    ERROR = "error"
    MISSING_DEPENDENCY = "missing_dependency"


@dataclass(slots=True)
class ModelDownloadState:
    phase: ModelDownloadPhase = ModelDownloadPhase.IDLE
    model_size: str = ""
    target_dir: str | None = None
    message: str = "未確認です。"
    error_message: str | None = None


class WhisperModelService:
    def __init__(self, paths: AppPaths, log_store: LogStore) -> None:
        self.paths = paths
        self.log_store = log_store
        self._lock = Lock()
        self._thread: Thread | None = None
        self._state = ModelDownloadState()

    def snapshot(self) -> ModelDownloadState:
        with self._lock:
            return replace(self._state)

    def get_model_dir(self, model_size: str) -> Path:
        return resolve_whisper_model_dir(self.paths.whisper_models_dir, model_size)

    def build_dependency_status(self, model_size: str) -> DependencyStatus:
        model_dir = self.get_model_dir(model_size)
        snapshot = self.snapshot()

        if snapshot.model_size == model_size:
            if snapshot.phase is ModelDownloadPhase.DOWNLOADING:
                return DependencyStatus(
                    name="Whisper Model",
                    state=DependencyState.WARNING,
                    message=snapshot.message,
                    path=snapshot.target_dir,
                )
            if snapshot.phase is ModelDownloadPhase.ERROR:
                return DependencyStatus(
                    name="Whisper Model",
                    state=DependencyState.MISSING,
                    message=snapshot.message,
                    path=snapshot.target_dir,
                )
            if snapshot.phase is ModelDownloadPhase.MISSING_DEPENDENCY:
                return DependencyStatus(
                    name="Whisper Model",
                    state=DependencyState.MISSING,
                    message=snapshot.message,
                    path=snapshot.target_dir,
                )

        available, error_message = self.check_library_available()
        if not available:
            return DependencyStatus(
                name="Whisper Model",
                state=DependencyState.MISSING,
                message=f"faster-whisper が利用できません: {error_message}",
                path=str(model_dir),
            )

        if is_model_available(model_dir):
            return DependencyStatus(
                name="Whisper Model",
                state=DependencyState.READY,
                message=f"利用可能: {model_dir}",
                path=str(model_dir),
            )

        return DependencyStatus(
            name="Whisper Model",
            state=DependencyState.MISSING,
            message=f"未取得です。{model_size} モデルをダウンロードしてください。",
            path=str(model_dir),
        )

    def check_library_available(self) -> tuple[bool, str | None]:
        try:
            import faster_whisper  # noqa: F401
        except Exception as exc:
            return False, str(exc)
        return True, None

    def ensure_model(self, model_size: str, auto_download: bool = False) -> bool:
        model_dir = self.get_model_dir(model_size)

        if is_model_available(model_dir):
            self._set_state(
                ModelDownloadPhase.READY,
                model_size=model_size,
                target_dir=str(model_dir),
                message=f"利用可能: {model_dir}",
            )
            return False

        if not auto_download:
            return False

        return self.start_download(model_size)

    def start_download(self, model_size: str) -> bool:
        model_dir = self.get_model_dir(model_size)

        if is_model_available(model_dir):
            self._set_state(
                ModelDownloadPhase.READY,
                model_size=model_size,
                target_dir=str(model_dir),
                message=f"利用可能: {model_dir}",
            )
            return False

        available, error_message = self.check_library_available()
        if not available:
            self._set_state(
                ModelDownloadPhase.MISSING_DEPENDENCY,
                model_size=model_size,
                target_dir=str(model_dir),
                message=f"faster-whisper が利用できません: {error_message}",
                error_message=error_message,
            )
            return False

        with self._lock:
            if self._thread and self._thread.is_alive():
                return False

            self._state = ModelDownloadState(
                phase=ModelDownloadPhase.DOWNLOADING,
                model_size=model_size,
                target_dir=str(model_dir),
                message=f"{model_size} モデルをダウンロード中です。しばらくお待ちください。",
            )
            self._thread = Thread(
                target=self._download_worker,
                args=(model_size,),
                daemon=True,
            )
            self._thread.start()

        self.log_store.add(f"Whisper モデルのダウンロードを開始しました: {model_size}")
        return True

    def _download_worker(self, model_size: str) -> None:
        target_dir = self.get_model_dir(model_size)
        cache_dir = self.paths.whisper_models_dir / ".cache"
        target_dir.mkdir(parents=True, exist_ok=True)
        cache_dir.mkdir(parents=True, exist_ok=True)

        try:
            from faster_whisper import download_model

            with warnings.catch_warnings():
                warnings.filterwarnings(
                    "ignore",
                    message=r"The `local_dir_use_symlinks` argument is deprecated.*",
                    category=UserWarning,
                )
                warnings.filterwarnings(
                    "ignore",
                    message=r"You are sending unauthenticated requests to the HF Hub.*",
                    category=UserWarning,
                )
                downloaded_path = Path(
                    download_model(
                        model_size,
                        output_dir=str(target_dir),
                        cache_dir=str(cache_dir),
                        local_files_only=False,
                    )
                )
        except Exception as exc:
            error_message = str(exc)
            self._set_state(
                ModelDownloadPhase.ERROR,
                model_size=model_size,
                target_dir=str(target_dir),
                message=f"Whisper モデルのダウンロードに失敗しました: {error_message}",
                error_message=error_message,
            )
            self.log_store.add(f"Whisper モデルのダウンロード失敗: {error_message}")
            return

        self._set_state(
            ModelDownloadPhase.READY,
            model_size=model_size,
            target_dir=str(downloaded_path),
            message=f"ダウンロード完了: {downloaded_path}",
        )
        self.log_store.add(f"Whisper モデルのダウンロードが完了しました: {downloaded_path}")

    def _set_state(
        self,
        phase: ModelDownloadPhase,
        model_size: str,
        target_dir: str | None,
        message: str,
        error_message: str | None = None,
    ) -> None:
        with self._lock:
            self._state = ModelDownloadState(
                phase=phase,
                model_size=model_size,
                target_dir=target_dir,
                message=message,
                error_message=error_message,
            )

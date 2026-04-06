from __future__ import annotations

from dataclasses import dataclass

from autosubmaker.config.app_paths import AppPaths
from autosubmaker.config.app_settings import AppSettings
from autosubmaker.config.settings_store import SettingsStore
from autosubmaker.models.app_status import StartupState
from autosubmaker.services.audio_extract_service import AudioExtractService
from autosubmaker.services.burnin_service import BurnInService
from autosubmaker.services.environment_service import EnvironmentService
from autosubmaker.services.media_probe_service import MediaProbeService
from autosubmaker.services.subtitle_service import SubtitleService
from autosubmaker.services.transcription_service import TranscriptionService
from autosubmaker.services.whisper_model_service import WhisperModelService
from autosubmaker.utils.logger import LogStore


@dataclass(slots=True)
class BootstrapContext:
    paths: AppPaths
    settings_store: SettingsStore
    settings: AppSettings
    environment_service: EnvironmentService
    media_probe_service: MediaProbeService
    audio_extract_service: AudioExtractService
    transcription_service: TranscriptionService
    subtitle_service: SubtitleService
    burnin_service: BurnInService
    whisper_model_service: WhisperModelService
    startup_state: StartupState
    log_store: LogStore


def bootstrap_application() -> BootstrapContext:
    paths = AppPaths.default()
    paths.ensure_directories()

    log_store = LogStore(paths.log_file)
    settings_store = SettingsStore(paths)
    settings = settings_store.load()
    media_probe_service = MediaProbeService()
    audio_extract_service = AudioExtractService(paths, log_store)
    whisper_model_service = WhisperModelService(paths, log_store)
    transcription_service = TranscriptionService(
        paths=paths,
        whisper_model_service=whisper_model_service,
        log_store=log_store,
    )
    subtitle_service = SubtitleService(log_store=log_store)
    burnin_service = BurnInService(paths=paths, log_store=log_store)

    if not settings.output_dir:
        settings.output_dir = str(paths.outputs_dir)
        settings_store.save(settings)

    environment_service = EnvironmentService(paths, whisper_model_service)
    startup_state = environment_service.inspect(settings)

    log_store.add(f"アプリ管理ディレクトリを初期化しました: {paths.root}")
    log_store.add(f"出力先: {settings.output_dir}")
    log_store.add(f"FFmpeg: {startup_state.ffmpeg.message}")
    log_store.add(f"Whisper model: {startup_state.whisper_model.message}")

    return BootstrapContext(
        paths=paths,
        settings_store=settings_store,
        settings=settings,
        environment_service=environment_service,
        media_probe_service=media_probe_service,
        audio_extract_service=audio_extract_service,
        transcription_service=transcription_service,
        subtitle_service=subtitle_service,
        burnin_service=burnin_service,
        whisper_model_service=whisper_model_service,
        startup_state=startup_state,
        log_store=log_store,
    )

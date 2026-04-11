from __future__ import annotations

from pathlib import Path

import pytest

from autosubmaker.config.app_paths import AppPaths
from autosubmaker.config.app_settings import AppSettings
from autosubmaker.models.transcription_result import (
    TranscriptionResult,
    TranscriptionSegment,
)
from autosubmaker.services.transcription_service import TranscriptionService
from autosubmaker.utils.logger import LogStore


class FakeWhisperModelService:
    def __init__(self, model_dir: Path) -> None:
        self.model_dir = model_dir

    def get_model_dir(self, _model_size: str) -> Path:
        return self.model_dir


class FakeSegment:
    def __init__(self, start: float, end: float, text: str, words: list[object] | None = None) -> None:
        self.start = start
        self.end = end
        self.text = text
        self.words = words or []


class FakeWord:
    def __init__(self, start: float, end: float, word: str, probability: float = 0.9) -> None:
        self.start = start
        self.end = end
        self.word = word
        self.probability = probability


class FakeInfo:
    def __init__(self, language: str, duration: float) -> None:
        self.language = language
        self.duration = duration


class FakeRunner:
    def __init__(self) -> None:
        self.calls: list[dict[str, str | None]] = []

    def transcribe(
        self,
        audio_path: str | Path,
        model_size_or_path: str | Path,
        *,
        language: str | None,
        device: str,
        vad_filter: bool = True,
        word_timestamps: bool = True,
    ) -> tuple[list[FakeSegment], FakeInfo]:
        self.calls.append(
            {
                "audio_path": str(audio_path),
                "model_path": str(model_size_or_path),
                "language": language,
                "device": device,
                "vad_filter": str(vad_filter),
                "word_timestamps": str(word_timestamps),
            }
        )
        return (
            [
                FakeSegment(
                    0.0,
                    1.2,
                    "  こんにちは   ",
                    words=[FakeWord(0.0, 0.6, "こんにちは")],
                ),
                FakeSegment(1.2, 2.4, ""),
                FakeSegment(
                    2.5,
                    4.0,
                    "世界です。",
                    words=[FakeWord(2.5, 3.4, "世界です。")],
                ),
            ],
            FakeInfo(language="ja", duration=4.0),
        )


class FallbackRunner(FakeRunner):
    def transcribe(
        self,
        audio_path: str | Path,
        model_size_or_path: str | Path,
        *,
        language: str | None,
        device: str,
        vad_filter: bool = True,
        word_timestamps: bool = True,
    ) -> tuple[list[FakeSegment], FakeInfo]:
        if device == "cuda":
            self.calls.append(
                {
                    "audio_path": str(audio_path),
                    "model_path": str(model_size_or_path),
                    "language": language,
                    "device": device,
                    "vad_filter": str(vad_filter),
                    "word_timestamps": str(word_timestamps),
                }
            )
            raise RuntimeError("CUDA unavailable")
        return super().transcribe(
            audio_path,
            model_size_or_path,
            language=language,
            device=device,
            vad_filter=vad_filter,
            word_timestamps=word_timestamps,
        )


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


def test_transcription_service_writes_text_and_json_outputs(tmp_path: Path) -> None:
    paths = build_paths(tmp_path)
    paths.ensure_directories()
    model_dir = paths.whisper_models_dir / "small"
    model_dir.mkdir(parents=True, exist_ok=True)
    (model_dir / "config.json").write_text("{}", encoding="utf-8")

    runner = FakeRunner()
    service = TranscriptionService(
        paths=paths,
        whisper_model_service=FakeWhisperModelService(model_dir),
        log_store=LogStore(paths.log_file),
        whisper_runner=runner,
    )
    settings = AppSettings()
    settings.transcription.language_mode = "fixed"
    settings.transcription.language = "ja"

    result = service.transcribe(
        audio_path=tmp_path / "sample_audio.wav",
        settings=settings,
        job_id="job001",
    )

    assert result.language == "ja"
    assert [segment.text for segment in result.segments] == ["こんにちは", "世界です。"]
    assert result.segments[0].words[0].text == "こんにちは"
    assert result.segments[1].words[0].start_seconds == 2.5
    assert result.text_path is not None
    assert result.json_path is not None
    assert Path(result.text_path).read_text(encoding="utf-8") == "こんにちは\n世界です。"
    assert '"words": [' in Path(result.json_path).read_text(encoding="utf-8")
    assert '"language": "ja"' in Path(result.json_path).read_text(encoding="utf-8")
    assert runner.calls == [
        {
            "audio_path": str(tmp_path / "sample_audio.wav"),
            "model_path": str(model_dir),
            "language": "ja",
            "device": "auto",
            "vad_filter": "True",
            "word_timestamps": "True",
        }
    ]


def test_transcription_service_falls_back_to_cpu_when_gpu_fails(tmp_path: Path) -> None:
    paths = build_paths(tmp_path)
    paths.ensure_directories()
    model_dir = paths.whisper_models_dir / "small"
    model_dir.mkdir(parents=True, exist_ok=True)
    (model_dir / "model.bin").write_text("ok", encoding="utf-8")

    runner = FallbackRunner()
    log_store = LogStore(paths.log_file)
    service = TranscriptionService(
        paths=paths,
        whisper_model_service=FakeWhisperModelService(model_dir),
        log_store=log_store,
        whisper_runner=runner,
    )
    settings = AppSettings()
    settings.transcription.device_mode = "gpu"

    result = service.transcribe(
        audio_path=tmp_path / "fallback_audio.wav",
        settings=settings,
        job_id="job002",
    )

    assert result.language == "ja"
    assert [call["device"] for call in runner.calls] == ["cuda", "cpu"]
    assert "cpu へ切り替えます" in log_store.as_text()


def test_transcription_result_full_text_joins_segments() -> None:
    result = TranscriptionResult(
        language="ja",
        duration_seconds=2.0,
        segments=[
            TranscriptionSegment(1, 0.0, 1.0, "一行目"),
            TranscriptionSegment(2, 1.0, 2.0, "二行目"),
        ],
    )

    assert result.full_text == "一行目\n二行目"


def test_transcription_service_requires_available_model(tmp_path: Path) -> None:
    paths = build_paths(tmp_path)
    paths.ensure_directories()
    model_dir = paths.whisper_models_dir / "small"
    model_dir.mkdir(parents=True, exist_ok=True)

    service = TranscriptionService(
        paths=paths,
        whisper_model_service=FakeWhisperModelService(model_dir),
        log_store=LogStore(paths.log_file),
        whisper_runner=FakeRunner(),
    )

    with pytest.raises(RuntimeError, match="Whisper モデルが見つかりません"):
        service.transcribe(
            audio_path=tmp_path / "missing_audio.wav",
            settings=AppSettings(),
            job_id="job003",
        )

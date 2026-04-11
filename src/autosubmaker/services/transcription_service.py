from __future__ import annotations

import json
import re
from pathlib import Path

from autosubmaker.bootstrap.dependency_check import is_model_available
from autosubmaker.config.app_paths import AppPaths
from autosubmaker.config.app_settings import AppSettings
from autosubmaker.integrations.whisper_runner import WhisperRunner
from autosubmaker.models.transcription_result import (
    TranscriptionResult,
    TranscriptionSegment,
    TranscriptionWord,
)
from autosubmaker.services.whisper_model_service import WhisperModelService
from autosubmaker.utils.logger import LogStore
from autosubmaker.utils.text_splitter import normalize_text


class TranscriptionService:
    def __init__(
        self,
        paths: AppPaths,
        whisper_model_service: WhisperModelService,
        log_store: LogStore,
        whisper_runner: WhisperRunner | None = None,
    ) -> None:
        self.paths = paths
        self.whisper_model_service = whisper_model_service
        self.log_store = log_store
        self.whisper_runner = whisper_runner or WhisperRunner()

    def transcribe(
        self,
        audio_path: str | Path,
        settings: AppSettings,
        job_id: str,
    ) -> TranscriptionResult:
        source_audio_path = Path(audio_path)
        model_size = settings.transcription.model_size
        model_dir = self.whisper_model_service.get_model_dir(model_size)

        if not is_model_available(model_dir):
            raise RuntimeError(f"Whisper モデルが見つかりません: {model_dir}")

        language = self._resolve_language(settings)
        raw_segments, info = self._run_transcription(
            audio_path=source_audio_path,
            model_dir=model_dir,
            language=language,
            settings=settings,
        )

        result = self._build_result(raw_segments, info)
        text_path, json_path = self._build_output_paths(source_audio_path, job_id)
        result.text_path = str(text_path)
        result.json_path = str(json_path)
        self._write_outputs(result, text_path, json_path)

        self.log_store.add(
            "文字起こしが完了しました: "
            f"{source_audio_path.name} -> {len(result.segments)} セグメント / "
            f"言語 {result.language} / 保存先 {text_path}"
        )
        return result

    def _run_transcription(
        self,
        *,
        audio_path: Path,
        model_dir: Path,
        language: str | None,
        settings: AppSettings,
    ) -> tuple[object, object]:
        device_candidates = self._resolve_device_candidates(
            settings.transcription.device_mode
        )
        last_error: Exception | None = None

        for index, device in enumerate(device_candidates):
            try:
                return self.whisper_runner.transcribe(
                    audio_path,
                    model_dir,
                    language=language,
                    device=device,
                    vad_filter=True,
                    word_timestamps=True,
                )
            except Exception as exc:
                last_error = exc
                if index + 1 < len(device_candidates):
                    next_device = device_candidates[index + 1]
                    self.log_store.add(
                        f"Whisper を {device} で開始できなかったため {next_device} へ切り替えます: {exc}"
                    )
                    continue

        detail = str(last_error).strip() if last_error else "不明なエラー"
        raise RuntimeError(f"文字起こしに失敗しました: {detail}") from last_error

    def _build_result(
        self,
        raw_segments: object,
        info: object,
    ) -> TranscriptionResult:
        segments: list[TranscriptionSegment] = []

        for segment in raw_segments:
            text = normalize_text(str(getattr(segment, "text", "")).strip())
            if not text:
                continue

            start_seconds = max(0.0, float(getattr(segment, "start", 0.0) or 0.0))
            end_seconds = max(
                start_seconds,
                float(getattr(segment, "end", start_seconds) or start_seconds),
            )
            words = self._extract_words(segment)
            segments.append(
                TranscriptionSegment(
                    index=len(segments) + 1,
                    start_seconds=start_seconds,
                    end_seconds=end_seconds,
                    text=text,
                    words=words,
                )
            )

        duration_seconds = float(getattr(info, "duration", 0.0) or 0.0)
        if not duration_seconds and segments:
            duration_seconds = segments[-1].end_seconds

        detected_language = normalize_text(str(getattr(info, "language", "") or ""))
        if not detected_language:
            detected_language = "unknown"

        return TranscriptionResult(
            language=detected_language,
            duration_seconds=duration_seconds,
            segments=segments,
        )

    def _extract_words(self, segment: object) -> list[TranscriptionWord]:
        raw_words = getattr(segment, "words", None) or []
        words: list[TranscriptionWord] = []
        for raw_word in raw_words:
            raw_text = str(getattr(raw_word, "word", "") or "")
            if not normalize_text(raw_text):
                continue

            start_seconds = max(0.0, float(getattr(raw_word, "start", 0.0) or 0.0))
            end_seconds = max(
                start_seconds,
                float(getattr(raw_word, "end", start_seconds) or start_seconds),
            )
            probability = getattr(raw_word, "probability", None)
            words.append(
                TranscriptionWord(
                    start_seconds=start_seconds,
                    end_seconds=end_seconds,
                    text=raw_text,
                    probability=float(probability) if probability is not None else None,
                )
            )
        return words

    def _build_output_paths(
        self,
        audio_path: Path,
        job_id: str,
    ) -> tuple[Path, Path]:
        safe_stem = re.sub(r"[^A-Za-z0-9._-]+", "_", audio_path.stem).strip("._")
        if safe_stem.endswith("_audio"):
            safe_stem = safe_stem[:-6].strip("._")
        if not safe_stem:
            safe_stem = "transcription"

        job_temp_dir = self.paths.temp_dir / job_id
        job_temp_dir.mkdir(parents=True, exist_ok=True)
        text_path = job_temp_dir / f"{safe_stem}_transcription.txt"
        json_path = job_temp_dir / f"{safe_stem}_transcription.json"
        return text_path, json_path

    def _write_outputs(
        self,
        result: TranscriptionResult,
        text_path: Path,
        json_path: Path,
    ) -> None:
        text_path.write_text(result.full_text, encoding="utf-8", newline="\n")
        json_path.write_text(
            json.dumps(result.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
            newline="\n",
        )

    @staticmethod
    def _resolve_language(settings: AppSettings) -> str | None:
        if settings.transcription.language_mode == "fixed":
            language = normalize_text(settings.transcription.language)
            return language or "ja"
        return None

    @staticmethod
    def _resolve_device_candidates(device_mode: str) -> list[str]:
        if device_mode == "gpu":
            return ["cuda", "cpu"]
        if device_mode == "cpu":
            return ["cpu"]
        return ["auto"]

from __future__ import annotations

from pathlib import Path
from typing import Any

class WhisperRunner:
    def __init__(self) -> None:
        self._cache_key: tuple[str, str] | None = None
        self._model: Any = None

    def transcribe(
        self,
        audio_path: str | Path,
        model_size_or_path: str | Path,
        *,
        language: str | None,
        device: str,
        vad_filter: bool = True,
    ) -> tuple[Any, Any]:
        model = self._get_model(model_size_or_path, device)
        return model.transcribe(
            str(audio_path),
            language=language,
            task="transcribe",
            vad_filter=vad_filter,
        )

    def _get_model(self, model_size_or_path: str | Path, device: str) -> Any:
        model_path = str(model_size_or_path)
        cache_key = (model_path, device)
        if self._cache_key == cache_key and self._model is not None:
            return self._model

        from faster_whisper import WhisperModel

        self._model = WhisperModel(
            model_path,
            device=device,
            compute_type=self._resolve_compute_type(device),
            local_files_only=True,
        )
        self._cache_key = cache_key
        return self._model

    @staticmethod
    def _resolve_compute_type(device: str) -> str:
        if device == "cpu":
            return "int8"
        return "default"

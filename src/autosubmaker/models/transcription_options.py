from __future__ import annotations

from dataclasses import asdict, dataclass


AVAILABLE_MODEL_SIZES = (
    "tiny",
    "base",
    "small",
    "medium",
    "large-v1",
    "large-v2",
    "large-v3",
    "turbo",
)


def normalize_model_size(model_size: str | None) -> str:
    normalized = (model_size or "").strip()
    if normalized == "large":
        return "large-v3"
    if normalized in AVAILABLE_MODEL_SIZES:
        return normalized
    return "small"


@dataclass(slots=True)
class TranscriptionOptions:
    language_mode: str = "auto"
    language: str = "ja"
    model_size: str = "small"
    device_mode: str = "auto"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict | None) -> "TranscriptionOptions":
        if not data:
            return cls()
        return cls(
            language_mode=data.get("language_mode", "auto"),
            language=data.get("language", "ja"),
            model_size=normalize_model_size(data.get("model_size", "small")),
            device_mode=data.get("device_mode", "auto"),
        )

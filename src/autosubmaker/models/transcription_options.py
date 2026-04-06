from __future__ import annotations

from dataclasses import asdict, dataclass


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
            model_size=data.get("model_size", "small"),
            device_mode=data.get("device_mode", "auto"),
        )


from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class TranscriptionSegment:
    index: int
    start_seconds: float
    end_seconds: float
    text: str

    def to_dict(self) -> dict[str, float | int | str]:
        return {
            "index": self.index,
            "start_seconds": self.start_seconds,
            "end_seconds": self.end_seconds,
            "text": self.text,
        }


@dataclass(slots=True)
class TranscriptionResult:
    language: str
    duration_seconds: float
    segments: list[TranscriptionSegment] = field(default_factory=list)
    text_path: str | None = None
    json_path: str | None = None

    @property
    def full_text(self) -> str:
        return "\n".join(segment.text for segment in self.segments)

    def to_dict(self) -> dict[str, object]:
        return {
            "language": self.language,
            "duration_seconds": self.duration_seconds,
            "text": self.full_text,
            "segments": [segment.to_dict() for segment in self.segments],
            "text_path": self.text_path,
            "json_path": self.json_path,
        }

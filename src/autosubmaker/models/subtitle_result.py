from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class SubtitleCue:
    index: int
    start_seconds: float
    end_seconds: float
    text: str


@dataclass(slots=True)
class SubtitleResult:
    cues: list[SubtitleCue] = field(default_factory=list)
    srt_path: str | None = None
    ass_path: str | None = None

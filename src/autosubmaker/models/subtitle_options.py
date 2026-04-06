from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(slots=True)
class SubtitleOptions:
    emit_srt: bool = True
    emit_ass: bool = True
    burn_in_video: bool = True
    output_suffix: str = "_subtitled"
    keep_temp_files: bool = False
    landscape_chars_per_line: int = 18
    portrait_chars_per_line: int = 13
    max_lines: int = 2
    min_duration_seconds: float = 0.8
    max_duration_seconds: float = 4.0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict | None) -> "SubtitleOptions":
        if not data:
            return cls()
        return cls(
            emit_srt=data.get("emit_srt", True),
            emit_ass=data.get("emit_ass", True),
            burn_in_video=data.get("burn_in_video", True),
            output_suffix=data.get("output_suffix", "_subtitled"),
            keep_temp_files=data.get("keep_temp_files", False),
            landscape_chars_per_line=data.get("landscape_chars_per_line", 18),
            portrait_chars_per_line=data.get("portrait_chars_per_line", 13),
            max_lines=data.get("max_lines", 2),
            min_duration_seconds=data.get("min_duration_seconds", 0.8),
            max_duration_seconds=data.get("max_duration_seconds", 4.0),
        )


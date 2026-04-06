from __future__ import annotations

from dataclasses import asdict, dataclass, field

from autosubmaker.models.subtitle_options import SubtitleOptions
from autosubmaker.models.subtitle_style import SubtitleStyle
from autosubmaker.models.transcription_options import TranscriptionOptions


@dataclass(slots=True)
class AppSettings:
    ffmpeg_path: str | None = None
    output_dir: str | None = None
    window_mode: str = "native"
    transcription: TranscriptionOptions = field(default_factory=TranscriptionOptions)
    subtitles: SubtitleOptions = field(default_factory=SubtitleOptions)
    style: SubtitleStyle = field(default_factory=SubtitleStyle)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict | None) -> "AppSettings":
        if not data:
            return cls()

        transcription_data = data.get("transcription") or {}
        subtitles_data = data.get("subtitles") or {}
        style_data = data.get("style") or {}

        return cls(
            ffmpeg_path=data.get("ffmpeg_path"),
            output_dir=data.get("output_dir"),
            window_mode=data.get("window_mode", "native"),
            transcription=TranscriptionOptions.from_dict(transcription_data),
            subtitles=SubtitleOptions.from_dict(subtitles_data),
            style=SubtitleStyle.from_dict(style_data),
        )


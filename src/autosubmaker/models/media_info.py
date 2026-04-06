from __future__ import annotations

from dataclasses import dataclass

from autosubmaker.models.job import VideoOrientation


@dataclass(slots=True)
class MediaInfo:
    width: int = 0
    height: int = 0
    duration_seconds: float = 0.0

    @property
    def orientation(self) -> VideoOrientation:
        if self.width <= 0 or self.height <= 0:
            return VideoOrientation.UNKNOWN
        if self.width > self.height:
            return VideoOrientation.LANDSCAPE
        if self.width < self.height:
            return VideoOrientation.PORTRAIT
        return VideoOrientation.SQUARE

    @property
    def resolution_label(self) -> str:
        if self.width <= 0 or self.height <= 0:
            return "-"
        return f"{self.width}x{self.height}"

    @property
    def duration_label(self) -> str:
        total_seconds = max(0, round(self.duration_seconds))
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"

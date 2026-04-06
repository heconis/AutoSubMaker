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


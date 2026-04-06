from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from uuid import uuid4


class JobStatus(str, Enum):
    QUEUED = "待機中"
    RUNNING = "実行中"
    COMPLETED = "完了"
    FAILED = "失敗"


class VideoOrientation(str, Enum):
    LANDSCAPE = "横長"
    PORTRAIT = "縦長"
    SQUARE = "正方形"
    UNKNOWN = "未判定"


@dataclass(slots=True)
class Job:
    input_path: str
    output_dir: str
    burn_in_video: bool
    subtitle_only: bool
    id: str = field(default_factory=lambda: uuid4().hex[:8])
    status: JobStatus = JobStatus.QUEUED
    progress: int = 0
    resolution: str = "-"
    duration_label: str = "-"
    orientation: VideoOrientation = VideoOrientation.UNKNOWN
    error_message: str | None = None

    @property
    def file_name(self) -> str:
        return Path(self.input_path).name

    @property
    def output_mode(self) -> str:
        if self.subtitle_only and not self.burn_in_video:
            return "字幕のみ"
        if self.subtitle_only and self.burn_in_video:
            return "字幕 + 焼きこみ"
        return "焼きこみ"

    def to_row(self) -> dict[str, str | int]:
        return {
            "status": self.status.value,
            "file_name": self.file_name,
            "resolution": self.resolution,
            "orientation": self.orientation.value,
            "duration": self.duration_label,
            "mode": self.output_mode,
            "progress": f"{self.progress}%",
            "output_dir": self.output_dir,
        }


from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class DependencyState(str, Enum):
    READY = "ready"
    MISSING = "missing"
    WARNING = "warning"


@dataclass(slots=True)
class DependencyStatus:
    name: str
    state: DependencyState
    message: str
    path: str | None = None

    @property
    def badge_label(self) -> str:
        return f"{self.name}: {self.state.value.title()}"

    @property
    def color(self) -> str:
        if self.state is DependencyState.READY:
            return "bg-green-100 text-green-800"
        if self.state is DependencyState.WARNING:
            return "bg-amber-100 text-amber-800"
        return "bg-rose-100 text-rose-800"


@dataclass(slots=True)
class StartupState:
    app_root: Path
    ffmpeg: DependencyStatus
    whisper_model: DependencyStatus
    notes: list[str] = field(default_factory=list)

    @property
    def has_blockers(self) -> bool:
        return any(
            status.state is not DependencyState.READY
            for status in (self.ffmpeg, self.whisper_model)
        )


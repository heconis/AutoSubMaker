from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ProcessResult:
    success: bool
    output_files: list[str] = field(default_factory=list)
    message: str = ""


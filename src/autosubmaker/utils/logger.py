from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass(slots=True)
class LogStore:
    log_file: Path
    lines: list[str] = field(default_factory=list)
    max_lines: int = 200

    def add(self, message: str) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{timestamp}] {message}"
        self.lines.append(line)
        self.lines = self.lines[-self.max_lines :]

        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        with self.log_file.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(line + "\n")

    def as_text(self) -> str:
        return "\n".join(self.lines)


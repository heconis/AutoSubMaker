from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(slots=True)
class SubtitleStyle:
    font_name: str = "Yu Gothic UI"
    font_size: int = 54
    text_color: str = "#FFFFFF"
    outline_color: str = "#000000"
    outline_width: int = 3
    bottom_margin: int = 72
    alignment: str = "center"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict | None) -> "SubtitleStyle":
        if not data:
            return cls()
        return cls(
            font_name=data.get("font_name", "Yu Gothic UI"),
            font_size=data.get("font_size", 54),
            text_color=data.get("text_color", "#FFFFFF"),
            outline_color=data.get("outline_color", "#000000"),
            outline_width=data.get("outline_width", 3),
            bottom_margin=data.get("bottom_margin", 72),
            alignment=data.get("alignment", "center"),
        )


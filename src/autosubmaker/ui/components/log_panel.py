from __future__ import annotations

from typing import Callable

from nicegui import ui


class LogPanel:
    def __init__(self, text_getter: Callable[[], str]) -> None:
        self.text_getter = text_getter

    @ui.refreshable
    def render(self) -> None:
        with ui.card().classes("w-full rounded-2xl shadow-sm"):
            ui.label("ログ").classes("text-lg font-semibold")
            log_text = self.text_getter() or "(ログはまだありません)"
            ui.textarea(value=log_text).props("readonly autogrow").classes("w-full")


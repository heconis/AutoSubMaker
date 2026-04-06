from __future__ import annotations

from nicegui import ui


class ErrorDialog:
    def __init__(self) -> None:
        self.dialog = ui.dialog()
        with self.dialog, ui.card().classes("w-[520px] max-w-full rounded-2xl"):
            ui.label("エラー詳細").classes("text-lg font-semibold")
            self._message = ui.label("詳細はありません。").classes("whitespace-pre-wrap text-sm")
            ui.button("閉じる", on_click=self.dialog.close)

    def open(self, message: str) -> None:
        self._message.text = message
        self.dialog.open()


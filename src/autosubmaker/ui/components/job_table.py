from __future__ import annotations

from typing import Callable

from nicegui import ui


class JobTable:
    def __init__(self, rows_getter: Callable[[], list[dict[str, str | int]]]) -> None:
        self.rows_getter = rows_getter

    @ui.refreshable
    def render(self) -> None:
        rows = self.rows_getter()
        with ui.card().classes("w-full rounded-2xl shadow-sm"):
            ui.label("処理キュー").classes("text-lg font-semibold")

            if not rows:
                ui.label("まだ動画は追加されていません。").classes("text-sm text-slate-500")
                return

            columns = [
                {"name": "status", "label": "状態", "field": "status", "align": "left"},
                {"name": "file_name", "label": "ファイル名", "field": "file_name", "align": "left"},
                {"name": "resolution", "label": "解像度", "field": "resolution", "align": "left"},
                {"name": "orientation", "label": "向き", "field": "orientation", "align": "left"},
                {"name": "duration", "label": "長さ", "field": "duration", "align": "left"},
                {"name": "mode", "label": "出力モード", "field": "mode", "align": "left"},
                {"name": "progress", "label": "進捗", "field": "progress", "align": "left"},
                {"name": "output_dir", "label": "出力先", "field": "output_dir", "align": "left"},
            ]
            ui.table(columns=columns, rows=rows, row_key="file_name").classes("w-full")


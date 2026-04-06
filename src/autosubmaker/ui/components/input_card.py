from __future__ import annotations

from typing import Callable

from nicegui import ui


class InputCard:
    def __init__(self, on_add_paths: Callable[[list[str]], None]) -> None:
        self.on_add_paths = on_add_paths

    def build(self) -> None:
        with ui.card().classes("w-full rounded-2xl shadow-sm"):
            ui.label("動画の追加").classes("text-lg font-semibold")
            ui.label(
                "MVP の土台として、まずはファイルパスの手入力でキュー追加できる状態にしています。"
            ).classes("text-sm text-slate-600")

            single_input = ui.input("動画パス").classes("w-full")
            multi_input = ui.textarea("複数動画パス").classes("w-full")
            multi_input.props("autogrow")

            with ui.row().classes("gap-2"):
                ui.button(
                    "1件追加",
                    on_click=lambda: self.on_add_paths([single_input.value or ""]),
                )
                ui.button(
                    "複数追加",
                    on_click=lambda: self.on_add_paths(
                        [line for line in (multi_input.value or "").splitlines()]
                    ),
                ).props("outline")

            ui.label(
                "ドラッグアンドドロップとファイル選択ダイアログは次段階で実装します。"
            ).classes("text-xs text-slate-500")


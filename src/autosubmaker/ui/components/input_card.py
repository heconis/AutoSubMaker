from __future__ import annotations

from collections.abc import Awaitable, Callable

from nicegui import ui


PREFERRED_VIDEO_EXTENSIONS = (".mp4", ".mov", ".mkv", ".avi", ".m4v")
VIDEO_FILE_DIALOG_FILTERS = (
    f"動画ファイル ({';'.join(f'*{extension}' for extension in PREFERRED_VIDEO_EXTENSIONS)})",
    "すべてのファイル (*.*)",
)


def supported_extension_label() -> str:
    return " / ".join(extension.lstrip(".") for extension in PREFERRED_VIDEO_EXTENSIONS)


class InputCard:
    def __init__(
        self,
        on_add_paths: Callable[[list[str]], None],
        on_pick_files: Callable[[], Awaitable[None] | None],
    ) -> None:
        self.on_add_paths = on_add_paths
        self.on_pick_files = on_pick_files

    def build(self) -> None:
        with ui.card().classes("w-full rounded-2xl shadow-sm"):
            ui.label("動画の追加").classes("text-lg font-semibold")
            ui.label(
                "ファイル選択、ドラッグアンドドロップ、またはパス入力で動画をキューへ追加できます。"
            ).classes("text-sm text-slate-600")

            with ui.row().classes("w-full items-center gap-2"):
                ui.button("動画ファイルを選択", on_click=self.on_pick_files)
                ui.label("手入力は下のフォームから追加できます。").classes(
                    "text-xs text-slate-500"
                )

            with ui.card().classes(
                "w-full border-2 border-dashed border-slate-300 bg-slate-50 shadow-none"
            ):
                ui.label("ここに動画ファイルをドラッグアンドドロップ").classes(
                    "text-base font-medium text-slate-700"
                )
                ui.label(
                    "ネイティブウィンドウ上へドロップすると、そのままキューへ追加されます。"
                ).classes("text-sm text-slate-600")
                ui.label(f"対応形式: {supported_extension_label()}").classes(
                    "text-xs text-slate-500"
                )

            ui.separator()
            ui.label("パスを直接入力して追加する場合").classes(
                "text-sm font-medium text-slate-700"
            )

            single_input = ui.input("動画パス").classes("w-full")
            multi_input = ui.textarea("複数動画パス").classes("w-full")
            multi_input.props("autogrow")

            def add_single() -> None:
                self.on_add_paths([single_input.value or ""])
                single_input.set_value("")

            def add_multiple() -> None:
                self.on_add_paths([line for line in (multi_input.value or "").splitlines()])
                multi_input.set_value("")

            with ui.row().classes("gap-2"):
                ui.button("1件追加", on_click=add_single)
                ui.button("複数追加", on_click=add_multiple).props("outline")

            ui.label(
                "ネットワークドライブや別アプリで開いているファイルでも、フルパスが分かれば追加できます。"
            ).classes("text-xs text-slate-500")

from __future__ import annotations

from typing import Callable

from nicegui import ui

from autosubmaker.config.app_settings import AppSettings
from autosubmaker.models.app_status import StartupState


class HeaderBar:
    def __init__(
        self,
        startup_state_getter: Callable[[], StartupState],
        settings: AppSettings,
        on_open_setup: Callable[[], None],
    ) -> None:
        self.startup_state_getter = startup_state_getter
        self.settings = settings
        self.on_open_setup = on_open_setup

    @ui.refreshable
    def render(self) -> None:
        state = self.startup_state_getter()
        with ui.card().classes("w-full rounded-2xl shadow-sm"):
            with ui.row().classes("w-full items-center justify-between gap-4"):
                with ui.column().classes("gap-1"):
                    ui.label("AutoSubMaker").classes("text-2xl font-bold")
                    ui.label("動画投入から字幕生成までをまとめて扱う作業画面です。").classes(
                        "text-sm text-slate-600"
                    )
                with ui.row().classes("items-center gap-2"):
                    ui.label(state.ffmpeg.badge_label).classes(
                        f"rounded-full px-3 py-1 text-xs font-medium {state.ffmpeg.color}"
                    )
                    ui.label(state.whisper_model.badge_label).classes(
                        f"rounded-full px-3 py-1 text-xs font-medium {state.whisper_model.color}"
                    )
                    ui.button("環境確認", on_click=self.on_open_setup).props("outline")
            ui.separator()
            with ui.row().classes("w-full items-center justify-between text-sm text-slate-600"):
                ui.label(f"出力先: {self.settings.output_dir or '-'}")
                ui.label(f"モデルサイズ: {self.settings.transcription.model_size}")


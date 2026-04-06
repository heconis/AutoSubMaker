from __future__ import annotations

from typing import Callable

from nicegui import ui

from autosubmaker.config.app_settings import AppSettings
from autosubmaker.models.app_status import StartupState


class SetupDialog:
    def __init__(
        self,
        startup_state_getter: Callable[[], StartupState],
        settings: AppSettings,
        on_save_ffmpeg_path: Callable[[str], None],
        on_download_whisper_model: Callable[[], None],
        on_refresh_environment: Callable[[], None],
    ) -> None:
        self.startup_state_getter = startup_state_getter
        self.settings = settings
        self.on_save_ffmpeg_path = on_save_ffmpeg_path
        self.on_download_whisper_model = on_download_whisper_model
        self.on_refresh_environment = on_refresh_environment

        self.dialog = ui.dialog()
        with self.dialog, ui.card().classes("w-[720px] max-w-full rounded-2xl"):
            ui.label("初回セットアップ").classes("text-xl font-semibold")
            self.render_body()

    @ui.refreshable
    def render_body(self) -> None:
        state = self.startup_state_getter()
        ui.label(
            "FFmpeg と Whisper モデルの利用状態を確認できます。Whisper モデルはここから取得できます。"
        ).classes("text-sm text-slate-600")

        with ui.card().classes("w-full bg-slate-50 shadow-none"):
            ui.label("FFmpeg").classes("font-semibold")
            ui.label(state.ffmpeg.message).classes("text-sm")
            ffmpeg_input = ui.input(
                "FFmpeg 実行ファイルのパス",
                value=self.settings.ffmpeg_path or "",
            ).classes("w-full")
            with ui.row().classes("gap-2"):
                ui.button(
                    "パスを保存して再確認",
                    on_click=lambda: self.on_save_ffmpeg_path(ffmpeg_input.value or ""),
                )
                ui.button(
                    "自動ダウンロード（次段階）",
                    on_click=lambda: ui.notify(
                        "FFmpeg 自動ダウンロードは次の実装ステップで追加します。",
                        type="warning",
                    ),
                ).props("outline")

        with ui.card().classes("w-full bg-slate-50 shadow-none"):
            ui.label("Whisper モデル").classes("font-semibold")
            ui.label(state.whisper_model.message).classes("text-sm")
            ui.label(f"保存先: {state.whisper_model.path or '-'}").classes("text-xs text-slate-500")
            with ui.row().classes("gap-2"):
                ui.button(
                    "モデルをダウンロード",
                    on_click=self.on_download_whisper_model,
                )
                ui.button("状態を再確認", on_click=self.on_refresh_environment).props("outline")

        with ui.row().classes("w-full justify-end"):
            ui.button("閉じる", on_click=self.dialog.close)

    def open(self) -> None:
        self.render_body.refresh()
        self.dialog.open()

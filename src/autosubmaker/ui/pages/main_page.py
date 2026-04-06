from __future__ import annotations

from typing import TYPE_CHECKING

from nicegui import ui

from autosubmaker.ui.components.header_bar import HeaderBar
from autosubmaker.ui.components.input_card import InputCard
from autosubmaker.ui.components.job_table import JobTable
from autosubmaker.ui.components.log_panel import LogPanel
from autosubmaker.ui.components.settings_panel import SettingsPanel
from autosubmaker.ui.dialogs.error_dialog import ErrorDialog
from autosubmaker.ui.dialogs.setup_dialog import SetupDialog

if TYPE_CHECKING:
    from autosubmaker.ui.app_shell import AppContext


class MainPage:
    def __init__(self, context: "AppContext") -> None:
        self.context = context
        self.startup_state = context.bootstrap.startup_state
        self._last_model_snapshot = context.bootstrap.whisper_model_service.snapshot()
        self.error_dialog = ErrorDialog()
        self.header_bar = HeaderBar(
            startup_state_getter=self.get_startup_state,
            settings=self.context.bootstrap.settings,
            on_open_setup=self.open_setup_dialog,
        )
        self.job_table = JobTable(self.context.queue_service.as_rows)
        self.log_panel = LogPanel(self.context.bootstrap.log_store.as_text)
        self.settings_panel = SettingsPanel(
            settings=self.context.bootstrap.settings,
            on_settings_changed=self.on_settings_changed,
        )
        self.setup_dialog = SetupDialog(
            startup_state_getter=self.get_startup_state,
            settings=self.context.bootstrap.settings,
            on_save_ffmpeg_path=self.save_ffmpeg_path,
            on_download_whisper_model=self.download_whisper_model,
            on_refresh_environment=self.refresh_environment,
        )

    def build(self) -> None:
        with ui.column().classes("w-full gap-4 p-4"):
            self.header_bar.render()

            with ui.row().classes("w-full items-start gap-4 max-[1200px]:flex-col"):
                with ui.column().classes("min-w-0 flex-1 gap-4"):
                    InputCard(self.add_paths).build()
                    self.render_action_bar()
                    self.job_table.render()
                self.settings_panel.build()

            self.log_panel.render()

        ui.timer(0.5, self.poll_background_state)

        if self.startup_state.has_blockers:
            ui.timer(0.1, self.open_setup_dialog, once=True)

        if self.startup_state.whisper_model.state.value != "ready":
            ui.timer(0.2, self.auto_start_whisper_download, once=True)

    def get_startup_state(self):
        return self.startup_state

    def open_setup_dialog(self) -> None:
        self.setup_dialog.open()

    def refresh_environment(self, add_log: bool = True) -> None:
        self.startup_state = self.context.bootstrap.environment_service.inspect(
            self.context.bootstrap.settings
        )
        self.header_bar.render.refresh()
        self.setup_dialog.render_body.refresh()
        self.log_panel.render.refresh()
        if add_log:
            self.context.bootstrap.log_store.add("依存状態を再確認しました。")

    def save_ffmpeg_path(self, raw_path: str) -> None:
        normalized = raw_path.strip() or None
        self.context.bootstrap.settings.ffmpeg_path = normalized
        self.context.bootstrap.settings_store.save(self.context.bootstrap.settings)
        self.context.bootstrap.log_store.add(
            f"FFmpeg パスを更新しました: {normalized or '(未設定)'}"
        )
        self.refresh_environment()
        ui.notify("FFmpeg パスを保存しました。", type="positive")

    def download_whisper_model(self) -> None:
        model_size = self.context.bootstrap.settings.transcription.model_size
        started = self.context.bootstrap.whisper_model_service.start_download(model_size)
        self.refresh_environment(add_log=False)

        if started:
            ui.notify(f"{model_size} モデルのダウンロードを開始しました。", type="positive")
            return

        snapshot = self.context.bootstrap.whisper_model_service.snapshot()
        if snapshot.phase.value == "downloading":
            ui.notify("モデルはすでにダウンロード中です。", type="warning")
        elif snapshot.phase.value == "ready":
            ui.notify("モデルはすでに利用可能です。", type="positive")
        else:
            ui.notify(snapshot.message, type="warning")

    def auto_start_whisper_download(self) -> None:
        self.context.bootstrap.whisper_model_service.ensure_model(
            self.context.bootstrap.settings.transcription.model_size,
            auto_download=True,
        )
        self.refresh_environment(add_log=False)

    def poll_background_state(self) -> None:
        snapshot = self.context.bootstrap.whisper_model_service.snapshot()
        if snapshot == self._last_model_snapshot:
            return

        self._last_model_snapshot = snapshot
        self.refresh_environment(add_log=False)

    def add_paths(self, paths: list[str]) -> None:
        added_jobs, errors = self.context.queue_service.add_paths(
            paths,
            self.context.bootstrap.settings,
        )

        for job in added_jobs:
            self.context.bootstrap.log_store.add(f"キューへ追加: {job.file_name}")
        for error in errors:
            self.context.bootstrap.log_store.add(f"追加失敗: {error}")

        if not added_jobs and not errors:
            ui.notify("追加対象がありません。", type="warning")
        elif errors and not added_jobs:
            self.error_dialog.open("\n".join(errors))
        elif errors:
            ui.notify("一部の動画だけ追加しました。", type="warning")
        else:
            ui.notify(f"{len(added_jobs)} 件の動画を追加しました。", type="positive")

        self.render_action_bar.refresh()
        self.job_table.render.refresh()
        self.log_panel.render.refresh()

    def on_settings_changed(self, message: str) -> None:
        self.context.bootstrap.settings_store.save(self.context.bootstrap.settings)
        self.context.bootstrap.log_store.add(message)
        self.header_bar.render.refresh()
        self.log_panel.render.refresh()

        self.context.bootstrap.whisper_model_service.ensure_model(
            self.context.bootstrap.settings.transcription.model_size,
            auto_download=False,
        )
        self.refresh_environment(add_log=False)

    @ui.refreshable
    def render_action_bar(self) -> None:
        with ui.card().classes("w-full rounded-2xl shadow-sm"):
            with ui.row().classes("w-full items-center justify-between gap-2"):
                with ui.row().classes("gap-2"):
                    ui.button("処理開始", on_click=self.start_processing)
                    ui.button("完了済みをクリア", on_click=self.clear_completed).props("outline")
                    ui.button("失敗分を再試行", on_click=self.retry_failed).props("outline")
                ui.label(
                    f"ジョブ数: {len(self.context.queue_service.jobs)}"
                ).classes("text-sm text-slate-600")

    def start_processing(self) -> None:
        if self.startup_state.has_blockers:
            self.context.bootstrap.log_store.add("依存不足のため処理開始を保留しました。")
            self.log_panel.render.refresh()
            self.open_setup_dialog()
            ui.notify("先に依存関係を確認してください。", type="warning")
            return

        self.context.bootstrap.log_store.add(
            "処理パイプラインの接続は次段階です。今回は起動土台まで実装しています。"
        )
        self.log_panel.render.refresh()
        ui.notify("処理本体は次の実装ステップで接続します。", type="warning")

    def clear_completed(self) -> None:
        cleared = self.context.queue_service.clear_completed()
        self.context.bootstrap.log_store.add(f"完了済みジョブを {cleared} 件クリアしました。")
        self.render_action_bar.refresh()
        self.job_table.render.refresh()
        self.log_panel.render.refresh()
        ui.notify(f"{cleared} 件クリアしました。", type="positive")

    def retry_failed(self) -> None:
        retried = self.context.queue_service.retry_failed()
        self.context.bootstrap.log_store.add(f"失敗ジョブを {retried} 件再試行待ちに戻しました。")
        self.render_action_bar.refresh()
        self.job_table.render.refresh()
        self.log_panel.render.refresh()
        ui.notify(f"{retried} 件再試行待ちに戻しました。", type="positive")

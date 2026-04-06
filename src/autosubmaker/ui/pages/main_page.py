from __future__ import annotations

import asyncio
from pathlib import Path
from time import monotonic
from typing import TYPE_CHECKING

from nicegui import app, ui
from nicegui.events import NativeEventArguments

from autosubmaker.models.job import Job, JobStatus
from autosubmaker.ui.components.header_bar import HeaderBar
from autosubmaker.ui.components.input_card import (
    InputCard,
    VIDEO_FILE_DIALOG_FILTERS,
)
from autosubmaker.ui.components.job_table import JobTable
from autosubmaker.ui.components.log_panel import LogPanel
from autosubmaker.ui.components.settings_panel import SettingsPanel
from autosubmaker.ui.dialogs.error_dialog import ErrorDialog
from autosubmaker.ui.dialogs.setup_dialog import SetupDialog

if TYPE_CHECKING:
    from nicegui.client import Client

    from autosubmaker.ui.app_shell import AppContext


_LAST_NATIVE_DROP_SIGNATURE: tuple[str, ...] | None = None
_LAST_NATIVE_DROP_AT = 0.0


class MainPage:
    def __init__(
        self,
        context: "AppContext",
        ui_client: "Client",
    ) -> None:
        self.context = context
        self.startup_state = context.bootstrap.startup_state
        self._last_model_snapshot = context.bootstrap.whisper_model_service.snapshot()
        self._is_processing = False
        self._ui_client = ui_client
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
                    InputCard(self.add_paths, self.pick_files).build()
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
        if add_log:
            self.context.bootstrap.log_store.add("依存状態を再確認しました。")
        self.startup_state = self.context.bootstrap.environment_service.inspect(
            self.context.bootstrap.settings
        )
        self.header_bar.render.refresh()
        self.setup_dialog.render_body.refresh()
        self.log_panel.render.refresh()

    def _notify(self, message: str, *, type: str = "positive", group: bool = True) -> None:
        self._ui_client.safe_invoke(
            lambda: ui.notify(
                message,
                type=type,
                group=group,
            )
        )

    def save_ffmpeg_path(self, raw_path: str) -> None:
        normalized = raw_path.strip() or None
        self.context.bootstrap.settings.ffmpeg_path = normalized
        self.context.bootstrap.settings_store.save(self.context.bootstrap.settings)
        self.context.bootstrap.log_store.add(
            f"FFmpeg パスを更新しました: {normalized or '(未設定)'}"
        )
        self.refresh_environment()
        self._notify("FFmpeg パスを保存しました。", type="positive")

    def download_whisper_model(self) -> None:
        model_size = self.context.bootstrap.settings.transcription.model_size
        started = self.context.bootstrap.whisper_model_service.start_download(model_size)
        self.refresh_environment(add_log=False)

        if started:
            self._notify(f"{model_size} モデルのダウンロードを開始しました。", type="positive")
            return

        snapshot = self.context.bootstrap.whisper_model_service.snapshot()
        if snapshot.phase.value == "downloading":
            self._notify("モデルはすでにダウンロード中です。", type="warning")
        elif snapshot.phase.value == "ready":
            self._notify("モデルはすでに利用可能です。", type="positive")
        else:
            self._notify(snapshot.message, type="warning")

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
            self._populate_job_metadata(job)
            self.context.bootstrap.log_store.add(f"キューへ追加: {job.file_name}")
        for error in errors:
            self.context.bootstrap.log_store.add(f"追加失敗: {error}")

        if not added_jobs and not errors:
            self._notify("追加対象がありません。", type="warning", group=False)
        elif errors and not added_jobs:
            self.error_dialog.open("\n".join(errors))
        elif errors:
            self._notify("一部の動画だけ追加しました。", type="warning", group=False)
        else:
            self._notify(
                f"{len(added_jobs)} 件の動画を追加しました。",
                type="positive",
                group=False,
            )

        self.render_action_bar.refresh()
        self.job_table.render.refresh()
        self.log_panel.render.refresh()

    async def pick_files(self) -> None:
        window = app.native.main_window
        if window is None:
            self._notify(
                "ファイル選択ダイアログを開けません。パス入力をご利用ください。",
                type="warning",
            )
            return

        paths = await window.create_file_dialog(
            directory=self._initial_file_dialog_directory(),
            allow_multiple=True,
            file_types=VIDEO_FILE_DIALOG_FILTERS,
        )
        if not paths:
            return

        self.add_paths(list(paths))

    def handle_native_drop(self, event: NativeEventArguments) -> None:
        global _LAST_NATIVE_DROP_AT
        global _LAST_NATIVE_DROP_SIGNATURE

        paths = [
            str(path).strip()
            for path in event.args.get("files", [])
            if str(path).strip()
        ]
        if not paths:
            return

        signature = tuple(
            str(Path(path).expanduser().resolve(strict=False))
            for path in paths
        )
        now = monotonic()
        if (
            _LAST_NATIVE_DROP_SIGNATURE == signature
            and now - _LAST_NATIVE_DROP_AT < 2.0
        ):
            return

        _LAST_NATIVE_DROP_SIGNATURE = signature
        _LAST_NATIVE_DROP_AT = now

        self.context.bootstrap.log_store.add(
            f"ドラッグアンドドロップで {len(paths)} 件の入力を受け取りました。"
        )
        self._ui_client.safe_invoke(lambda: self.add_paths(paths))

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

    async def start_processing(self) -> None:
        if self.startup_state.has_blockers:
            self.context.bootstrap.log_store.add("依存不足のため処理開始を保留しました。")
            self.log_panel.render.refresh()
            self.open_setup_dialog()
            self._notify("先に依存関係を確認してください。", type="warning")
            return

        if self._is_processing:
            self._notify("現在処理中です。完了までお待ちください。", type="warning")
            return

        queued_jobs = [job for job in self.context.queue_service.jobs if job.status is JobStatus.QUEUED]
        if not queued_jobs:
            self._notify("処理対象の待機中ジョブがありません。", type="warning")
            return

        ffmpeg_path = self.startup_state.ffmpeg.path
        if not ffmpeg_path:
            self._notify("FFmpeg のパスが解決できません。", type="warning")
            return

        self._is_processing = True
        self.render_action_bar.refresh()
        success_count = 0
        failure_count = 0

        try:
            for job in queued_jobs:
                job.status = JobStatus.RUNNING
                job.progress = 5
                job.error_message = None
                self.job_table.render.refresh()
                self.log_panel.render.refresh()
                self.context.bootstrap.log_store.add(f"処理開始: {job.file_name}")

                try:
                    await self._ensure_job_metadata(job, ffmpeg_path)
                    job.progress = 30
                    self.job_table.render.refresh()

                    audio_path = await asyncio.to_thread(
                        self.context.bootstrap.audio_extract_service.extract_audio,
                        job.input_path,
                        ffmpeg_path,
                        job.id,
                    )
                    job.audio_path = str(audio_path)
                    job.progress = 55
                    self.job_table.render.refresh()

                    transcription_result = await asyncio.to_thread(
                        self.context.bootstrap.transcription_service.transcribe,
                        audio_path,
                        self.context.bootstrap.settings,
                        job.id,
                    )
                    job.transcription_text_path = transcription_result.text_path
                    job.transcription_json_path = transcription_result.json_path
                    job.transcription_language = transcription_result.language
                    job.progress = 80
                    self.job_table.render.refresh()

                    subtitle_result = await asyncio.to_thread(
                        self.context.bootstrap.subtitle_service.generate,
                        job,
                        transcription_result,
                        self.context.bootstrap.settings,
                    )
                    job.srt_path = subtitle_result.srt_path
                    job.ass_path = subtitle_result.ass_path
                    job.progress = 85
                    self.job_table.render.refresh()

                    if job.burn_in_video:
                        output_video_path = await asyncio.to_thread(
                            self.context.bootstrap.burnin_service.burn_in,
                            job,
                            ffmpeg_path,
                            self.context.bootstrap.settings,
                        )
                        job.output_video_path = str(output_video_path)
                        job.progress = 100
                        self.context.bootstrap.log_store.add(
                            f"焼きこみまで完了: {job.file_name} -> {output_video_path}"
                        )
                    else:
                        job.progress = 100
                        self.context.bootstrap.log_store.add(
                            "字幕生成まで完了: "
                            f"{job.file_name} -> {subtitle_result.srt_path or subtitle_result.ass_path}"
                        )
                    job.status = JobStatus.COMPLETED
                    success_count += 1
                except Exception as exc:
                    job.status = JobStatus.FAILED
                    job.error_message = str(exc)
                    failure_count += 1
                    self.context.bootstrap.log_store.add(
                        f"処理失敗: {job.file_name} -> {job.error_message}"
                    )

                self.render_action_bar.refresh()
                self.job_table.render.refresh()
                self.log_panel.render.refresh()
                await asyncio.sleep(0)
        finally:
            self._is_processing = False
            self.render_action_bar.refresh()

        if failure_count:
            self._notify(
                f"処理が完了しました。成功 {success_count} 件 / 失敗 {failure_count} 件",
                type="warning",
            )
        else:
            self._notify(f"処理が完了しました。成功 {success_count} 件", type="positive")

    def clear_completed(self) -> None:
        cleared = self.context.queue_service.clear_completed()
        self.context.bootstrap.log_store.add(f"完了済みジョブを {cleared} 件クリアしました。")
        self.render_action_bar.refresh()
        self.job_table.render.refresh()
        self.log_panel.render.refresh()
        self._notify(f"{cleared} 件クリアしました。", type="positive")

    def retry_failed(self) -> None:
        retried = self.context.queue_service.retry_failed()
        self.context.bootstrap.log_store.add(f"失敗ジョブを {retried} 件再試行待ちに戻しました。")
        self.render_action_bar.refresh()
        self.job_table.render.refresh()
        self.log_panel.render.refresh()
        self._notify(f"{retried} 件再試行待ちに戻しました。", type="positive")

    def _populate_job_metadata(self, job: Job) -> None:
        ffmpeg_path = self.startup_state.ffmpeg.path
        if not ffmpeg_path:
            return

        try:
            media_info = self.context.bootstrap.media_probe_service.probe(job.input_path, ffmpeg_path)
        except Exception as exc:
            self.context.bootstrap.log_store.add(
                f"メタ情報取得に失敗しました: {job.file_name} -> {exc}"
            )
            return

        job.apply_media_info(media_info)

    async def _ensure_job_metadata(self, job: Job, ffmpeg_path: str) -> None:
        if job.resolution != "-" and job.duration_label != "-":
            return

        media_info = await asyncio.to_thread(
            self.context.bootstrap.media_probe_service.probe,
            job.input_path,
            ffmpeg_path,
        )
        job.apply_media_info(media_info)

    def _initial_file_dialog_directory(self) -> str:
        output_dir = self.context.bootstrap.settings.output_dir
        if output_dir:
            candidate = Path(output_dir).expanduser()
            if candidate.exists():
                return str(candidate)
        return str(Path.home())

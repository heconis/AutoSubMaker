from __future__ import annotations

from typing import Callable

from nicegui import ui

from autosubmaker.config.app_settings import AppSettings
from autosubmaker.models.transcription_options import AVAILABLE_MODEL_SIZES


class SettingsPanel:
    def __init__(
        self,
        settings: AppSettings,
        on_settings_changed: Callable[[str], None],
        available_fonts: list[str] | tuple[str, ...],
    ) -> None:
        self.settings = settings
        self.on_settings_changed = on_settings_changed
        self.available_fonts = self._build_font_options(available_fonts)

    def build(self) -> None:
        with ui.column().classes("w-[360px] max-w-full gap-4"):
            self._build_output_card()
            self._build_transcription_card()
            self._build_subtitle_card()
            self._build_style_card()

    def _build_output_card(self) -> None:
        with ui.card().classes("w-full rounded-2xl shadow-sm"):
            ui.label("出力設定").classes("text-lg font-semibold")
            output_dir = ui.input("出力先フォルダ", value=self.settings.output_dir or "").classes("w-full")
            output_dir.on(
                "change",
                lambda _e: self._apply(
                    lambda: setattr(self.settings, "output_dir", output_dir.value or None),
                    "出力先を保存しました。",
                ),
            )

            emit_srt = ui.checkbox("SRT を出力", value=self.settings.subtitles.emit_srt)
            emit_srt.on(
                "update:model-value",
                lambda _e: self._apply(
                    lambda: setattr(self.settings.subtitles, "emit_srt", bool(emit_srt.value)),
                    "SRT 出力設定を保存しました。",
                ),
            )

            emit_ass = ui.checkbox("ASS を出力", value=self.settings.subtitles.emit_ass)
            emit_ass.on(
                "update:model-value",
                lambda _e: self._apply(
                    lambda: setattr(self.settings.subtitles, "emit_ass", bool(emit_ass.value)),
                    "ASS 出力設定を保存しました。",
                ),
            )

            burn_in = ui.checkbox("字幕を焼きこむ", value=self.settings.subtitles.burn_in_video)
            burn_in.on(
                "update:model-value",
                lambda _e: self._apply(
                    lambda: setattr(
                        self.settings.subtitles,
                        "burn_in_video",
                        bool(burn_in.value),
                    ),
                    "焼きこみ設定を保存しました。",
                ),
            )

            keep_temp = ui.checkbox(
                "一時ファイルを保持",
                value=self.settings.subtitles.keep_temp_files,
            )
            keep_temp.on(
                "update:model-value",
                lambda _e: self._apply(
                    lambda: setattr(
                        self.settings.subtitles,
                        "keep_temp_files",
                        bool(keep_temp.value),
                    ),
                    "一時ファイル設定を保存しました。",
                ),
            )

    def _build_transcription_card(self) -> None:
        with ui.card().classes("w-full rounded-2xl shadow-sm"):
            ui.label("文字起こし設定").classes("text-lg font-semibold")

            language_mode = ui.select(
                {"auto": "自動判定", "fixed": "固定指定"},
                value=self.settings.transcription.language_mode,
                label="言語モード",
            ).classes("w-full")
            language_mode.on(
                "update:model-value",
                lambda _e: self._apply(
                    lambda: setattr(
                        self.settings.transcription,
                        "language_mode",
                        language_mode.value,
                    ),
                    "言語モードを保存しました。",
                ),
            )

            language = ui.input("言語コード", value=self.settings.transcription.language).classes("w-full")
            language.on(
                "change",
                lambda _e: self._apply(
                    lambda: setattr(
                        self.settings.transcription,
                        "language",
                        language.value or "ja",
                    ),
                    "言語コードを保存しました。",
                ),
            )

            model_size = ui.select(
                list(AVAILABLE_MODEL_SIZES),
                value=self.settings.transcription.model_size,
                label="モデルサイズ",
            ).classes("w-full")
            model_size.on(
                "update:model-value",
                lambda _e: self._apply(
                    lambda: setattr(
                        self.settings.transcription,
                        "model_size",
                        model_size.value,
                    ),
                    "モデルサイズを保存しました。",
                ),
            )

            device_mode = ui.select(
                {"auto": "Auto", "gpu": "GPU 優先", "cpu": "CPU 固定"},
                value=self.settings.transcription.device_mode,
                label="実行デバイス",
            ).classes("w-full")
            device_mode.on(
                "update:model-value",
                lambda _e: self._apply(
                    lambda: setattr(
                        self.settings.transcription,
                        "device_mode",
                        device_mode.value,
                    ),
                    "実行デバイスを保存しました。",
                ),
            )

    def _build_subtitle_card(self) -> None:
        with ui.card().classes("w-full rounded-2xl shadow-sm"):
            ui.label("字幕整形").classes("text-lg font-semibold")

            landscape = ui.number(
                "横長動画の最大文字数",
                value=self.settings.subtitles.landscape_chars_per_line,
                min=8,
                max=30,
                step=1,
            ).classes("w-full")
            landscape.on(
                "change",
                lambda _e: self._apply(
                    lambda: setattr(
                        self.settings.subtitles,
                        "landscape_chars_per_line",
                        int(landscape.value or 18),
                    ),
                    "横長字幕の最大文字数を保存しました。",
                ),
            )

            portrait = ui.number(
                "縦長動画の最大文字数",
                value=self.settings.subtitles.portrait_chars_per_line,
                min=8,
                max=24,
                step=1,
            ).classes("w-full")
            portrait.on(
                "change",
                lambda _e: self._apply(
                    lambda: setattr(
                        self.settings.subtitles,
                        "portrait_chars_per_line",
                        int(portrait.value or 13),
                    ),
                    "縦長字幕の最大文字数を保存しました。",
                ),
            )

            max_lines = ui.number(
                "最大行数",
                value=self.settings.subtitles.max_lines,
                min=1,
                max=3,
                step=1,
            ).classes("w-full")
            max_lines.on(
                "change",
                lambda _e: self._apply(
                    lambda: setattr(
                        self.settings.subtitles,
                        "max_lines",
                        int(max_lines.value or 2),
                    ),
                    "最大行数を保存しました。",
                ),
            )

            min_duration = ui.number(
                "最小表示時間（秒）",
                value=self.settings.subtitles.min_duration_seconds,
                min=0.1,
                max=5.0,
                step=0.1,
            ).classes("w-full")
            min_duration.on(
                "change",
                lambda _e: self._apply(
                    lambda: setattr(
                        self.settings.subtitles,
                        "min_duration_seconds",
                        float(min_duration.value or 0.8),
                    ),
                    "最小表示時間を保存しました。",
                ),
            )

            max_duration = ui.number(
                "最大表示時間（秒）",
                value=self.settings.subtitles.max_duration_seconds,
                min=0.5,
                max=10.0,
                step=0.1,
            ).classes("w-full")
            max_duration.on(
                "change",
                lambda _e: self._apply(
                    lambda: setattr(
                        self.settings.subtitles,
                        "max_duration_seconds",
                        float(max_duration.value or 4.0),
                    ),
                    "最大表示時間を保存しました。",
                ),
            )

    def _build_style_card(self) -> None:
        with ui.card().classes("w-full rounded-2xl shadow-sm"):
            ui.label("字幕スタイル").classes("text-lg font-semibold")

            font_name = ui.select(
                self.available_fonts,
                value=self.settings.style.font_name,
                label="フォント名",
            ).classes("w-full")
            font_name.props("use-input input-debounce=0")
            font_name.on(
                "update:model-value",
                lambda _e: self._apply(
                    lambda: setattr(self.settings.style, "font_name", font_name.value or "Yu Gothic UI"),
                    "フォント名を保存しました。",
                ),
            )

            font_size = ui.number(
                "フォントサイズ",
                value=self.settings.style.font_size,
                min=10,
                max=120,
                step=1,
            ).classes("w-full")
            font_size.on(
                "change",
                lambda _e: self._apply(
                    lambda: setattr(self.settings.style, "font_size", int(font_size.value or 54)),
                    "フォントサイズを保存しました。",
                ),
            )

            text_color = ui.input("文字色", value=self.settings.style.text_color).classes("w-full")
            text_color.on(
                "change",
                lambda _e: self._apply(
                    lambda: setattr(self.settings.style, "text_color", text_color.value or "#FFFFFF"),
                    "文字色を保存しました。",
                ),
            )

            outline_color = ui.input("縁取り色", value=self.settings.style.outline_color).classes("w-full")
            outline_color.on(
                "change",
                lambda _e: self._apply(
                    lambda: setattr(
                        self.settings.style,
                        "outline_color",
                        outline_color.value or "#000000",
                    ),
                    "縁取り色を保存しました。",
                ),
            )

            outline_width = ui.number(
                "縁取り太さ",
                value=self.settings.style.outline_width,
                min=0,
                max=12,
                step=1,
            ).classes("w-full")
            outline_width.on(
                "change",
                lambda _e: self._apply(
                    lambda: setattr(
                        self.settings.style,
                        "outline_width",
                        int(outline_width.value or 3),
                    ),
                    "縁取り太さを保存しました。",
                ),
            )

            bottom_margin = ui.number(
                "画面下からの余白",
                value=self.settings.style.bottom_margin,
                min=0,
                max=600,
                step=1,
            ).classes("w-full")
            bottom_margin.on(
                "change",
                lambda _e: self._apply(
                    lambda: setattr(
                        self.settings.style,
                        "bottom_margin",
                        int(bottom_margin.value or 72),
                    ),
                    "画面下からの余白を保存しました。",
                ),
            )

    def _apply(self, mutation: Callable[[], None], message: str) -> None:
        mutation()
        self.on_settings_changed(message)

    def _build_font_options(self, available_fonts: list[str] | tuple[str, ...]) -> list[str]:
        fonts = [font for font in available_fonts if font]
        if self.settings.style.font_name and self.settings.style.font_name not in fonts:
            fonts.insert(0, self.settings.style.font_name)
        if not fonts:
            fonts.append("Yu Gothic UI")
        return list(dict.fromkeys(fonts))

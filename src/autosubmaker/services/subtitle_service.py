from __future__ import annotations

import re
from pathlib import Path

from autosubmaker.config.app_settings import AppSettings
from autosubmaker.models.job import Job, VideoOrientation
from autosubmaker.models.subtitle_result import SubtitleCue, SubtitleResult
from autosubmaker.models.transcription_result import (
    TranscriptionResult,
    TranscriptionSegment,
    TranscriptionWord,
)
from autosubmaker.utils.logger import LogStore
from autosubmaker.utils.text_splitter import normalize_text
from autosubmaker.utils.text_splitter import split_into_subtitle_blocks
from autosubmaker.utils.timecode import format_ass_timecode, format_srt_timecode


class SubtitleService:
    SILENCE_GAP_SECONDS = 0.35

    def __init__(self, log_store: LogStore) -> None:
        self.log_store = log_store

    def generate(
        self,
        job: Job,
        transcription_result: TranscriptionResult,
        settings: AppSettings,
    ) -> SubtitleResult:
        cues = self._build_cues(job, transcription_result, settings)
        if not cues:
            raise RuntimeError("字幕に変換できる文字起こし結果がありません。")

        need_srt = settings.subtitles.emit_srt
        need_ass = settings.subtitles.emit_ass or job.burn_in_video
        if not need_srt and not need_ass:
            raise RuntimeError("字幕ファイル出力が無効です。SRT または ASS を有効にしてください。")

        output_dir = Path(job.output_dir).expanduser()
        output_dir.mkdir(parents=True, exist_ok=True)
        safe_stem = self._build_safe_stem(job)

        srt_path = output_dir / f"{safe_stem}.srt" if need_srt else None
        ass_path = output_dir / f"{safe_stem}.ass" if need_ass else None

        if srt_path:
            srt_path.write_text(self._render_srt(cues), encoding="utf-8", newline="\n")
        if ass_path:
            ass_path.write_text(
                self._render_ass(job, cues, settings),
                encoding="utf-8",
                newline="\n",
            )

        output_labels = [str(path) for path in (srt_path, ass_path) if path is not None]
        self.log_store.add(f"字幕ファイルを生成しました: {', '.join(output_labels)}")
        return SubtitleResult(
            cues=cues,
            srt_path=str(srt_path) if srt_path else None,
            ass_path=str(ass_path) if ass_path else None,
        )

    def _build_cues(
        self,
        job: Job,
        transcription_result: TranscriptionResult,
        settings: AppSettings,
    ) -> list[SubtitleCue]:
        max_chars = self._resolve_chars_per_line(job, settings)
        max_lines = max(1, int(settings.subtitles.max_lines))
        min_duration = max(0.1, float(settings.subtitles.min_duration_seconds))
        max_duration = max(min_duration, float(settings.subtitles.max_duration_seconds))

        cues: list[SubtitleCue] = []
        for segment in transcription_result.segments:
            if segment.words:
                cues.extend(
                    self._build_cues_from_words(
                        segment=segment,
                        start_index=len(cues) + 1,
                        max_chars=max_chars,
                        max_lines=max_lines,
                        min_duration=min_duration,
                        max_duration=max_duration,
                    )
                )
                continue

            blocks = split_into_subtitle_blocks(
                segment.text,
                max_chars=max_chars,
                max_lines=max_lines,
            )
            if not blocks:
                continue

            durations = self._distribute_durations(
                blocks=blocks,
                total_duration=max(0.0, segment.end_seconds - segment.start_seconds),
                min_duration=min_duration,
                max_duration=max_duration,
            )
            current_start = segment.start_seconds
            for block, duration in zip(blocks, durations):
                cue = SubtitleCue(
                    index=len(cues) + 1,
                    start_seconds=max(0.0, current_start),
                    end_seconds=max(current_start + duration, current_start + 0.1),
                    text=block,
                )
                current_start = cue.end_seconds
                cues.append(cue)

        return cues

    def _build_cues_from_words(
        self,
        *,
        segment: TranscriptionSegment,
        start_index: int,
        max_chars: int,
        max_lines: int,
        min_duration: float,
        max_duration: float,
    ) -> list[SubtitleCue]:
        cues: list[SubtitleCue] = []
        current_words: list[TranscriptionWord] = []

        for word in segment.words:
            if not current_words:
                current_words = [word]
                continue

            gap = max(0.0, word.start_seconds - current_words[-1].end_seconds)
            candidate_words = [*current_words, word]
            candidate_blocks = split_into_subtitle_blocks(
                self._compose_words_text(candidate_words),
                max_chars=max_chars,
                max_lines=max_lines,
            )

            if gap >= self.SILENCE_GAP_SECONDS or len(candidate_blocks) > 1:
                cues.extend(
                    self._finalize_word_group(
                        words=current_words,
                        start_index=start_index + len(cues),
                        max_chars=max_chars,
                        max_lines=max_lines,
                        min_duration=min_duration,
                        max_duration=max_duration,
                    )
                )
                current_words = [word]
                continue

            current_words.append(word)

        if current_words:
            cues.extend(
                self._finalize_word_group(
                    words=current_words,
                    start_index=start_index + len(cues),
                    max_chars=max_chars,
                    max_lines=max_lines,
                    min_duration=min_duration,
                    max_duration=max_duration,
                )
            )

        return cues

    def _finalize_word_group(
        self,
        *,
        words: list[TranscriptionWord],
        start_index: int,
        max_chars: int,
        max_lines: int,
        min_duration: float,
        max_duration: float,
    ) -> list[SubtitleCue]:
        if not words:
            return []

        text = self._compose_words_text(words)
        blocks = split_into_subtitle_blocks(
            text,
            max_chars=max_chars,
            max_lines=max_lines,
        )
        if len(blocks) <= 1:
            cue_text = blocks[0] if blocks else text
            return [
                SubtitleCue(
                    index=start_index,
                    start_seconds=words[0].start_seconds,
                    end_seconds=self._resolve_word_group_end(
                        words,
                        min_duration=min_duration,
                        max_duration=max_duration,
                    ),
                    text=cue_text,
                )
            ]

        return self._build_text_only_cues(
            text=text,
            start_seconds=words[0].start_seconds,
            end_seconds=words[-1].end_seconds,
            start_index=start_index,
            max_chars=max_chars,
            max_lines=max_lines,
            min_duration=min_duration,
            max_duration=max_duration,
        )

    def _build_text_only_cues(
        self,
        *,
        text: str,
        start_seconds: float,
        end_seconds: float,
        start_index: int,
        max_chars: int,
        max_lines: int,
        min_duration: float,
        max_duration: float,
    ) -> list[SubtitleCue]:
        blocks = split_into_subtitle_blocks(
            text,
            max_chars=max_chars,
            max_lines=max_lines,
        )
        durations = self._distribute_durations(
            blocks=blocks,
            total_duration=max(0.0, end_seconds - start_seconds),
            min_duration=min_duration,
            max_duration=max_duration,
        )
        cues: list[SubtitleCue] = []
        current_start = start_seconds
        for offset, (block, duration) in enumerate(zip(blocks, durations)):
            cue = SubtitleCue(
                index=start_index + offset,
                start_seconds=max(0.0, current_start),
                end_seconds=max(current_start + duration, current_start + 0.1),
                text=block,
            )
            current_start = cue.end_seconds
            cues.append(cue)
        return cues

    def _compose_words_text(self, words: list[TranscriptionWord]) -> str:
        return normalize_text("".join(word.text for word in words))

    def _resolve_word_group_end(
        self,
        words: list[TranscriptionWord],
        *,
        min_duration: float,
        max_duration: float,
    ) -> float:
        start_seconds = words[0].start_seconds
        end_seconds = words[-1].end_seconds
        duration = max(0.0, end_seconds - start_seconds)
        if duration <= 0:
            return start_seconds + min_duration
        return start_seconds + min(duration, max_duration)

    def _distribute_durations(
        self,
        *,
        blocks: list[str],
        total_duration: float,
        min_duration: float,
        max_duration: float,
    ) -> list[float]:
        count = len(blocks)
        if count == 0:
            return []

        total = total_duration
        if total <= 0:
            return [min_duration for _ in blocks]

        weights = [max(len(block.replace("\n", "")), 1) for block in blocks]
        lower_bound = min_duration if total >= min_duration * count else 0.0
        upper_bound = max_duration if total <= max_duration * count else float("inf")

        remaining = total
        durations: list[float | None] = [None] * count
        active = set(range(count))

        while active:
            weight_sum = sum(weights[index] for index in active)
            if weight_sum <= 0:
                even_duration = remaining / len(active)
                for index in active:
                    durations[index] = even_duration
                break

            changed = False
            for index in list(active):
                proposed = remaining * weights[index] / weight_sum
                if proposed < lower_bound:
                    durations[index] = lower_bound
                    remaining -= lower_bound
                    active.remove(index)
                    changed = True
                elif proposed > upper_bound:
                    durations[index] = upper_bound
                    remaining -= upper_bound
                    active.remove(index)
                    changed = True

            if changed:
                continue

            for index in active:
                durations[index] = remaining * weights[index] / weight_sum
            break

        resolved = [max(float(duration or 0.0), 0.1) for duration in durations]
        scale = total / sum(resolved)
        return [duration * scale for duration in resolved]

    def _render_srt(self, cues: list[SubtitleCue]) -> str:
        lines: list[str] = []
        for cue in cues:
            lines.append(str(cue.index))
            lines.append(
                f"{format_srt_timecode(cue.start_seconds)} --> {format_srt_timecode(cue.end_seconds)}"
            )
            lines.append(cue.text)
            lines.append("")
        return "\n".join(lines).strip() + "\n"

    def _render_ass(
        self,
        job: Job,
        cues: list[SubtitleCue],
        settings: AppSettings,
    ) -> str:
        play_res_x, play_res_y = self._resolve_play_resolution(job)
        style = settings.style
        alignment = self._resolve_alignment(style.alignment)
        primary_color = self._to_ass_color(style.text_color)
        outline_color = self._to_ass_color(style.outline_color)

        header_lines = [
            "[Script Info]",
            "ScriptType: v4.00+",
            "WrapStyle: 0",
            "ScaledBorderAndShadow: yes",
            f"PlayResX: {play_res_x}",
            f"PlayResY: {play_res_y}",
            "",
            "[V4+ Styles]",
            "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,"
            "Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,"
            "Alignment,MarginL,MarginR,MarginV,Encoding",
            "Style: Default,"
            f"{style.font_name},{style.font_size},{primary_color},{primary_color},{outline_color},&H00000000,"
            "0,0,0,0,100,100,0,0,1,"
            f"{style.outline_width},0,{alignment},48,48,{style.bottom_margin},1",
            "",
            "[Events]",
            "Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text",
        ]

        for cue in cues:
            ass_text = self._escape_ass_text(cue.text)
            header_lines.append(
                "Dialogue: 0,"
                f"{format_ass_timecode(cue.start_seconds)},{format_ass_timecode(cue.end_seconds)},"
                f"Default,,0,0,0,,{ass_text}"
            )

        return "\n".join(header_lines) + "\n"

    def _resolve_chars_per_line(self, job: Job, settings: AppSettings) -> int:
        if job.orientation is VideoOrientation.PORTRAIT:
            return max(1, int(settings.subtitles.portrait_chars_per_line))
        if job.orientation is VideoOrientation.SQUARE:
            return max(
                1,
                min(
                    int(settings.subtitles.landscape_chars_per_line),
                    int(settings.subtitles.portrait_chars_per_line),
                ),
            )
        return max(1, int(settings.subtitles.landscape_chars_per_line))

    def _resolve_play_resolution(self, job: Job) -> tuple[int, int]:
        if "x" in job.resolution:
            width_text, height_text = job.resolution.lower().split("x", maxsplit=1)
            try:
                width = max(1, int(width_text))
                height = max(1, int(height_text))
                return width, height
            except ValueError:
                pass

        if job.orientation is VideoOrientation.PORTRAIT:
            return 1080, 1920
        if job.orientation is VideoOrientation.SQUARE:
            return 1080, 1080
        return 1920, 1080

    def _build_safe_stem(self, job: Job) -> str:
        stem = Path(job.input_path).stem
        safe_stem = re.sub(r"[^A-Za-z0-9._-]+", "_", stem).strip("._")
        return safe_stem or "subtitle"

    def _escape_ass_text(self, text: str) -> str:
        return (
            text.replace("\\", "＼")
            .replace("{", "（")
            .replace("}", "）")
            .replace("\n", r"\N")
        )

    def _resolve_alignment(self, alignment: str) -> int:
        mapping = {
            "left": 1,
            "center": 2,
            "right": 3,
        }
        return mapping.get(alignment, 2)

    def _to_ass_color(self, color: str) -> str:
        normalized = color.strip().lstrip("#")
        if len(normalized) != 6:
            normalized = "FFFFFF"
        red = normalized[0:2]
        green = normalized[2:4]
        blue = normalized[4:6]
        return f"&H00{blue}{green}{red}"

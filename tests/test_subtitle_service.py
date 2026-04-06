from __future__ import annotations

from pathlib import Path

from autosubmaker.config.app_settings import AppSettings
from autosubmaker.models.job import Job, VideoOrientation
from autosubmaker.models.subtitle_result import SubtitleCue
from autosubmaker.models.transcription_result import TranscriptionResult, TranscriptionSegment
from autosubmaker.services.subtitle_service import SubtitleService
from autosubmaker.utils.logger import LogStore


def build_service(tmp_path: Path) -> SubtitleService:
    return SubtitleService(log_store=LogStore(tmp_path / "autosubmaker.log"))


def test_subtitle_service_generates_srt_and_ass_files(tmp_path: Path) -> None:
    service = build_service(tmp_path)
    settings = AppSettings()
    settings.subtitles.landscape_chars_per_line = 6
    settings.subtitles.max_lines = 2
    settings.style.font_name = "Yu Gothic UI"
    job = Job(
        input_path=str(tmp_path / "sample.mp4"),
        output_dir=str(tmp_path / "outputs"),
        burn_in_video=True,
        subtitle_only=True,
    )
    job.orientation = VideoOrientation.LANDSCAPE
    job.resolution = "1920x1080"
    transcription_result = TranscriptionResult(
        language="ja",
        duration_seconds=5.0,
        segments=[
            TranscriptionSegment(
                index=1,
                start_seconds=0.0,
                end_seconds=4.0,
                text="今日はいい天気ですね。明日も晴れるでしょう。",
            )
        ],
    )

    result = service.generate(job, transcription_result, settings)

    assert result.srt_path is not None
    assert result.ass_path is not None
    srt_text = Path(result.srt_path).read_text(encoding="utf-8")
    ass_text = Path(result.ass_path).read_text(encoding="utf-8")

    assert "1\n00:00:00,000 -->" in srt_text
    assert "今日は" in srt_text
    assert "[Script Info]" in ass_text
    assert "PlayResX: 1920" in ass_text
    assert "Dialogue: 0,0:00:00.00," in ass_text


def test_subtitle_service_uses_portrait_line_limit(tmp_path: Path) -> None:
    service = build_service(tmp_path)
    settings = AppSettings()
    settings.subtitles.landscape_chars_per_line = 18
    settings.subtitles.portrait_chars_per_line = 4
    job = Job(
        input_path=str(tmp_path / "portrait.mp4"),
        output_dir=str(tmp_path / "outputs"),
        burn_in_video=False,
        subtitle_only=True,
    )
    job.orientation = VideoOrientation.PORTRAIT
    transcription_result = TranscriptionResult(
        language="ja",
        duration_seconds=3.0,
        segments=[
            TranscriptionSegment(
                index=1,
                start_seconds=0.0,
                end_seconds=3.0,
                text="あいうえおかきくけこ",
            )
        ],
    )

    cues = service.generate(job, transcription_result, settings).cues

    assert len(cues) >= 2
    assert all(len(line) <= 4 for cue in cues for line in cue.text.split("\n"))


def test_subtitle_service_uses_default_resolution_when_missing(tmp_path: Path) -> None:
    service = build_service(tmp_path)
    settings = AppSettings()
    settings.subtitles.emit_srt = False
    settings.subtitles.emit_ass = True
    job = Job(
        input_path=str(tmp_path / "unknown.mp4"),
        output_dir=str(tmp_path / "outputs"),
        burn_in_video=False,
        subtitle_only=True,
    )
    job.orientation = VideoOrientation.PORTRAIT
    transcription_result = TranscriptionResult(
        language="ja",
        duration_seconds=2.0,
        segments=[
            TranscriptionSegment(
                index=1,
                start_seconds=0.0,
                end_seconds=2.0,
                text="テスト字幕",
            )
        ],
    )

    result = service.generate(job, transcription_result, settings)
    ass_text = Path(result.ass_path or "").read_text(encoding="utf-8")

    assert "PlayResX: 1080" in ass_text
    assert "PlayResY: 1920" in ass_text


def test_subtitle_service_distributes_durations_across_cues(tmp_path: Path) -> None:
    service = build_service(tmp_path)
    durations = service._distribute_durations(
        blocks=["短い", "少し長めの字幕です"],
        total_duration=4.0,
        min_duration=0.8,
        max_duration=4.0,
    )

    assert len(durations) == 2
    assert round(sum(durations), 3) == 4.0
    assert durations[1] > durations[0]


def test_subtitle_service_render_srt_uses_timecodes() -> None:
    service = build_service(Path.cwd())
    text = service._render_srt(
        [
            SubtitleCue(index=1, start_seconds=0.0, end_seconds=1.25, text="一行目"),
            SubtitleCue(index=2, start_seconds=1.25, end_seconds=2.5, text="二行目"),
        ]
    )

    assert "00:00:01,250" in text
    assert "二行目" in text

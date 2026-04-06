from autosubmaker.utils.timecode import format_ass_timecode, format_srt_timecode


def test_format_srt_timecode() -> None:
    assert format_srt_timecode(65.432) == "00:01:05,432"


def test_format_srt_timecode_clamps_negative_values() -> None:
    assert format_srt_timecode(-1.0) == "00:00:00,000"


def test_format_ass_timecode() -> None:
    assert format_ass_timecode(65.432) == "0:01:05.43"

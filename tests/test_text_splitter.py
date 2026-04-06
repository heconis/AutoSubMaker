from autosubmaker.utils.text_splitter import normalize_text, split_into_subtitle_blocks, wrap_text


def test_normalize_text_collapses_spaces() -> None:
    assert normalize_text("  今日は   いい天気　ですね  ") == "今日は いい天気 ですね"


def test_wrap_text_prefers_punctuation_breaks() -> None:
    lines = wrap_text("今日はいい天気ですね。明日も晴れるでしょう。", 12)
    assert lines[0].endswith("。")


def test_split_into_subtitle_blocks_honors_max_lines() -> None:
    blocks = split_into_subtitle_blocks(
        "これは長めの字幕テキストで、二行ごとに区切って返したいです。",
        max_chars=8,
        max_lines=2,
    )
    assert all(block.count("\n") <= 1 for block in blocks)
    assert len(blocks) >= 2


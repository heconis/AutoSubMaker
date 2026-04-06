from __future__ import annotations

import re


PREFERRED_BREAK_CHARS = ("。", "、", "！", "？", "!", "?", " ", "　")
LINE_HEAD_AVOID_CHARS = ("、", "。", "」", "』", "）", ")", "】", "》", "〉", "’", "”")


def normalize_text(text: str) -> str:
    replaced = text.replace("\u3000", " ")
    replaced = re.sub(r"\s+", " ", replaced)
    return replaced.strip()


def find_split_index(text: str, max_chars: int) -> int:
    if len(text) <= max_chars:
        return len(text)

    candidates = [
        index
        for index in range(1, max_chars + 1)
        if text[index - 1] in PREFERRED_BREAK_CHARS
    ]
    if candidates:
        return candidates[-1]

    return max_chars


def wrap_text(text: str, max_chars: int) -> list[str]:
    remaining = normalize_text(text)
    if not remaining:
        return []

    lines: list[str] = []
    while remaining:
        split_index = find_split_index(remaining, max_chars)
        line = remaining[:split_index].strip()
        remaining = remaining[split_index:].strip()

        if remaining and remaining[0] in LINE_HEAD_AVOID_CHARS:
            line = (line + remaining[0]).strip()
            remaining = remaining[1:].strip()

        lines.append(line)

    return lines


def split_into_subtitle_blocks(text: str, max_chars: int, max_lines: int = 2) -> list[str]:
    wrapped_lines = wrap_text(text, max_chars)
    blocks: list[str] = []

    while wrapped_lines:
        block_lines = wrapped_lines[:max_lines]
        wrapped_lines = wrapped_lines[max_lines:]
        blocks.append("\n".join(block_lines))

    return blocks


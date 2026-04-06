from __future__ import annotations

import subprocess

import pytest

from autosubmaker.utils.process_runner import decode_process_output, run_command


def test_decode_process_output_prefers_utf8_when_available() -> None:
    payload = "日本語ログ".encode("utf-8")
    assert decode_process_output(payload) == "日本語ログ"


def test_decode_process_output_falls_back_to_cp932() -> None:
    payload = "エラー詳細".encode("cp932")
    assert decode_process_output(payload) == "エラー詳細"


def test_run_command_decodes_utf8_output() -> None:
    result = run_command(
        [
            "python",
            "-c",
            "import sys; sys.stdout.buffer.write('日本語'.encode('utf-8'))",
        ]
    )
    assert result.stdout == "日本語"


def test_run_command_raises_with_decoded_stderr() -> None:
    with pytest.raises(subprocess.CalledProcessError) as exc_info:
        run_command(
            [
                "python",
                "-c",
                "import sys; sys.stderr.buffer.write('失敗'.encode('utf-8')); raise SystemExit(2)",
            ]
        )

    assert exc_info.value.returncode == 2
    assert exc_info.value.stderr == "失敗"

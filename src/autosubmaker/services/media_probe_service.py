from __future__ import annotations

import json
import subprocess
from pathlib import Path

from autosubmaker.integrations.ffmpeg_runner import resolve_ffprobe_path
from autosubmaker.models.media_info import MediaInfo
from autosubmaker.utils.process_runner import run_command


class MediaProbeService:
    def probe(self, input_path: str | Path, ffmpeg_path: str | Path) -> MediaInfo:
        ffprobe_path = resolve_ffprobe_path(ffmpeg_path)
        if not ffprobe_path:
            raise RuntimeError("ffprobe が見つかりません。FFmpeg と同じ場所にあるか確認してください。")

        try:
            result = run_command(
                [
                    str(ffprobe_path),
                    "-v",
                    "error",
                    "-show_entries",
                    "stream=codec_type,width,height,duration:format=duration",
                    "-of",
                    "json",
                    str(input_path),
                ]
            )
        except subprocess.CalledProcessError as exc:
            detail = (exc.stderr or exc.stdout or str(exc)).strip()
            raise RuntimeError(f"動画メタ情報の取得に失敗しました: {detail}") from exc

        payload = json.loads(result.stdout or "{}")
        streams = payload.get("streams") or []
        video_stream = next(
            (stream for stream in streams if stream.get("codec_type") == "video"),
            {},
        )

        return MediaInfo(
            width=self._to_int(video_stream.get("width")),
            height=self._to_int(video_stream.get("height")),
            duration_seconds=self._resolve_duration(payload, video_stream),
        )

    def _resolve_duration(self, payload: dict, video_stream: dict) -> float:
        format_duration = (payload.get("format") or {}).get("duration")
        return self._to_float(format_duration) or self._to_float(video_stream.get("duration"))

    def _to_int(self, value: object) -> int:
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0

    def _to_float(self, value: object) -> float:
        try:
            return float(value or 0.0)
        except (TypeError, ValueError):
            return 0.0

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from autosubmaker.config.app_paths import AppPaths
from autosubmaker.utils.logger import LogStore
from autosubmaker.utils.process_runner import run_command


class AudioExtractService:
    def __init__(self, paths: AppPaths, log_store: LogStore) -> None:
        self.paths = paths
        self.log_store = log_store

    def build_output_path(self, input_path: str | Path, job_id: str) -> Path:
        source_path = Path(input_path)
        safe_stem = re.sub(r"[^A-Za-z0-9._-]+", "_", source_path.stem).strip("._")
        if not safe_stem:
            safe_stem = "audio"
        job_temp_dir = self.paths.temp_dir / job_id
        job_temp_dir.mkdir(parents=True, exist_ok=True)
        return job_temp_dir / f"{safe_stem}_audio.wav"

    def extract_audio(
        self,
        input_path: str | Path,
        ffmpeg_path: str | Path,
        job_id: str,
    ) -> Path:
        output_path = self.build_output_path(input_path, job_id)

        try:
            run_command(
                [
                    str(ffmpeg_path),
                    "-y",
                    "-i",
                    str(input_path),
                    "-vn",
                    "-ac",
                    "1",
                    "-ar",
                    "16000",
                    "-c:a",
                    "pcm_s16le",
                    str(output_path),
                ]
            )
        except subprocess.CalledProcessError as exc:
            detail = (exc.stderr or exc.stdout or str(exc)).strip()
            raise RuntimeError(f"音声抽出に失敗しました: {detail}") from exc

        self.log_store.add(f"音声抽出が完了しました: {output_path}")
        return output_path

from __future__ import annotations

import shutil
import time

from autosubmaker.config.app_paths import AppPaths
from autosubmaker.utils.logger import LogStore


class TempFileService:
    def __init__(self, paths: AppPaths, log_store: LogStore) -> None:
        self.paths = paths
        self.log_store = log_store

    def cleanup_job_temp_dir(self, job_id: str) -> bool:
        job_temp_dir = self.paths.temp_dir / job_id
        if not job_temp_dir.exists():
            return False

        last_error: Exception | None = None
        for attempt in range(3):
            try:
                shutil.rmtree(job_temp_dir)
                self.log_store.add(f"一時ファイルを削除しました: {job_temp_dir}")
                return True
            except OSError as exc:
                last_error = exc
                if attempt < 2:
                    time.sleep(0.2)

        self.log_store.add(
            f"一時ファイルの削除に失敗しました: {job_temp_dir} -> {last_error}"
        )
        return False

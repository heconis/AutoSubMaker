from __future__ import annotations

import json

from autosubmaker.config.app_paths import AppPaths
from autosubmaker.config.app_settings import AppSettings


class SettingsStore:
    def __init__(self, paths: AppPaths) -> None:
        self.paths = paths

    def load(self) -> AppSettings:
        if not self.paths.settings_file.exists():
            return AppSettings(output_dir=str(self.paths.outputs_dir))

        data = json.loads(self.paths.settings_file.read_text(encoding="utf-8"))
        settings = AppSettings.from_dict(data)
        if not settings.output_dir:
            settings.output_dir = str(self.paths.outputs_dir)
        return settings

    def save(self, settings: AppSettings) -> None:
        self.paths.config_dir.mkdir(parents=True, exist_ok=True)
        payload = settings.to_dict()
        self.paths.settings_file.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

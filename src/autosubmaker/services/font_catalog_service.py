from __future__ import annotations

import re
import sys


class FontCatalogService:
    _FONT_REGISTRY_PATHS = (
        r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts",
    )

    def list_fonts(self) -> list[str]:
        if not sys.platform.startswith("win"):
            return ["Yu Gothic UI", "Meiryo", "Arial"]

        font_names: list[str] = []
        try:
            import winreg

            for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
                for registry_path in self._FONT_REGISTRY_PATHS:
                    font_names.extend(self._read_registry_font_names(winreg, hive, registry_path))
        except Exception:
            return ["Yu Gothic UI", "Meiryo", "Arial"]

        return self._prepare_font_names(font_names) or ["Yu Gothic UI", "Meiryo", "Arial"]

    def _read_registry_font_names(self, winreg_module, hive, registry_path: str) -> list[str]:
        names: list[str] = []
        try:
            with winreg_module.OpenKey(hive, registry_path) as key:
                value_count = winreg_module.QueryInfoKey(key)[1]
                for index in range(value_count):
                    value_name = winreg_module.EnumValue(key, index)[0]
                    names.append(value_name)
        except OSError:
            return []
        return names

    def _prepare_font_names(self, raw_names: list[str]) -> list[str]:
        deduped: dict[str, str] = {}
        for raw_name in raw_names:
            normalized = self._normalize_font_name(raw_name)
            if not normalized:
                continue
            key = normalized.casefold()
            deduped.setdefault(key, normalized)
        return sorted(deduped.values(), key=str.casefold)

    def _normalize_font_name(self, raw_name: str) -> str:
        normalized = re.sub(r"\s+\([^)]*\)$", "", raw_name.strip())
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized.strip()

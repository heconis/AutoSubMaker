from __future__ import annotations

from autosubmaker.services.font_catalog_service import FontCatalogService


def test_normalize_font_name_removes_registry_suffix() -> None:
    service = FontCatalogService()
    assert service._normalize_font_name("Arial (TrueType)") == "Arial"
    assert service._normalize_font_name(" Yu Gothic UI  (OpenType) ") == "Yu Gothic UI"


def test_prepare_font_names_deduplicates_and_sorts() -> None:
    service = FontCatalogService()
    prepared = service._prepare_font_names(
        [
            "Arial (TrueType)",
            "Yu Gothic UI (TrueType)",
            "arial (OpenType)",
            "Meiryo (TrueType)",
        ]
    )

    assert prepared == ["Arial", "Meiryo", "Yu Gothic UI"]

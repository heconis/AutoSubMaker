from autosubmaker.models.transcription_options import (
    AVAILABLE_MODEL_SIZES,
    TranscriptionOptions,
    normalize_model_size,
)


def test_available_model_sizes_include_large_variants_and_turbo() -> None:
    assert AVAILABLE_MODEL_SIZES == (
        "tiny",
        "base",
        "small",
        "medium",
        "large-v1",
        "large-v2",
        "large-v3",
        "turbo",
    )


def test_normalize_model_size_maps_legacy_large_to_large_v3() -> None:
    assert normalize_model_size("large") == "large-v3"


def test_transcription_options_from_dict_uses_normalized_model_size() -> None:
    options = TranscriptionOptions.from_dict({"model_size": "large"})
    assert options.model_size == "large-v3"

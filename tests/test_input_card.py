from autosubmaker.ui.components.input_card import (
    VIDEO_FILE_DIALOG_FILTERS,
    supported_extension_label,
)


def test_supported_extension_label_lists_known_formats() -> None:
    assert supported_extension_label() == "mp4 / mov / mkv / avi / m4v"


def test_video_file_dialog_filters_include_supported_extensions() -> None:
    assert VIDEO_FILE_DIALOG_FILTERS[0].startswith("動画ファイル (")
    assert "*.mp4" in VIDEO_FILE_DIALOG_FILTERS[0]
    assert "*.mov" in VIDEO_FILE_DIALOG_FILTERS[0]
    assert VIDEO_FILE_DIALOG_FILTERS[1] == "すべてのファイル (*.*)"

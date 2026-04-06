from autosubmaker.models.job import VideoOrientation
from autosubmaker.models.media_info import MediaInfo


def test_media_info_resolution_label() -> None:
    info = MediaInfo(width=1920, height=1080, duration_seconds=12.3)
    assert info.resolution_label == "1920x1080"


def test_media_info_duration_label_without_hours() -> None:
    info = MediaInfo(width=1920, height=1080, duration_seconds=65.2)
    assert info.duration_label == "01:05"


def test_media_info_orientation() -> None:
    info = MediaInfo(width=1080, height=1920, duration_seconds=1.0)
    assert info.orientation is VideoOrientation.PORTRAIT

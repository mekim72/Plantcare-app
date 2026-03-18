import pytest

from youtube2blog.errors import URLValidationError
from youtube2blog.utils import extract_video_id, format_timestamp


def test_extract_video_id_watch_url() -> None:
    assert extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"


def test_extract_video_id_shorts_url() -> None:
    assert extract_video_id("https://www.youtube.com/shorts/dQw4w9WgXcQ") == "dQw4w9WgXcQ"


def test_extract_video_id_rejects_invalid() -> None:
    with pytest.raises(URLValidationError):
        extract_video_id("https://example.com/watch?v=abc")


def test_format_timestamp() -> None:
    assert format_timestamp(0) == "00:00"
    assert format_timestamp(71.9) == "01:11"


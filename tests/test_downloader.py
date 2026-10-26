import io
import os
import tempfile
import pytest
from downloader.clean import cleanup, create_temp_dir, register_temp_path
from downloader.core import download
from downloader.utils import (
    check_file_size,
    detect_platform,
    get_mimetype,
    prepare_media_result,
    select_best_yt_dlp_format,
)


def test_detect_platform():
    assert detect_platform("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "youtube"
    assert detect_platform("https://youtu.be/dQw4w9WgXcQ") == "youtube"
    assert detect_platform("https://www.tiktok.com/@user/video/1234567890") == "tiktok"
    assert detect_platform("https://vt.tiktok.com/ZS12345") == "tiktok"
    assert detect_platform("https://www.instagram.com/p/C123456") == "instagram"
    assert detect_platform("https://instagr.am/p/C123456") == "instagram"
    assert detect_platform("https://www.facebook.com/watch/?v=123456") == "facebook"
    assert detect_platform("https://fb.watch/123456") == "facebook"
    assert detect_platform("https://x.com/user/status/1234567890") == "x"
    assert detect_platform("https://twitter.com/user/status/1234567890") == "x"
    assert detect_platform("https://t.co/abcde") == "x"
    assert detect_platform("https://unknown-domain.com/video") is None


def test_select_best_yt_dlp_format():
    formats = [
        {"format_id": "137", "vcodec": "h264", "height": 1080},
        {"format_id": "22", "vcodec": "h264", "height": 720},
        {"format_id": "18", "vcodec": "h264", "height": 360},
    ]

    # audio
    assert select_best_yt_dlp_format(formats, media_type="audio") == "bestaudio/best"

    # best/worst/None
    assert select_best_yt_dlp_format(formats, target_resolution=None) == "bestvideo+bestaudio/best"
    assert select_best_yt_dlp_format(formats, target_resolution="best") == "bestvideo+bestaudio/best"
    assert select_best_yt_dlp_format(formats, target_resolution="worst") == "worstvideo+worstaudio/worst"

    # closest resolution: 480 -> closest is 360 (height 360 diff 120 vs 720 diff 240)
    fmt = select_best_yt_dlp_format(formats, target_resolution=480)
    assert "18+bestaudio/best" in fmt

    # closest resolution: 900 -> closest is 1080 (diff 180 vs 720 diff 180 - min picks first/closest)
    fmt = select_best_yt_dlp_format(formats, target_resolution=720)
    assert "22+bestaudio/best" in fmt


def test_mimetype():
    assert get_mimetype("file.mp4") == "video/mp4"
    assert get_mimetype("file.mp3") == "audio/mpeg"
    assert get_mimetype("file.jpg") == "image/jpeg"
    assert get_mimetype("file.png") == "image/png"


def test_max_filesize_check():
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"x" * 100)
        temp_path = f.name

    try:
        assert check_file_size(temp_path, max_filesize=50) is not None
        assert check_file_size(temp_path, max_filesize=500) is None
    finally:
        os.remove(temp_path)


def test_prepare_media_result_as_bytes():
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
        f.write(b"video content dummy")
        temp_path = f.name

    try:
        res = prepare_media_result(temp_path, media_type="video", as_bytes=True)
        assert res["type"] == "video"
        assert res["path"] == temp_path
        assert res["mimetype"] == "video/mp4"
        assert isinstance(res["bytes"], io.BytesIO)
        assert res["bytes"].getvalue() == b"video content dummy"
    finally:
        os.remove(temp_path)


def test_cleanup():
    temp_dir = create_temp_dir()
    temp_file = os.path.join(temp_dir, "test.txt")
    with open(temp_file, "w") as f:
        f.write("hello")
    register_temp_path(temp_file)

    assert os.path.exists(temp_file)
    assert os.path.exists(temp_dir)

    cleanup()

    assert not os.path.exists(temp_file)
    assert not os.path.exists(temp_dir)


def test_error_return_on_invalid_url():
    res = download("https://invalid-nonexistent-url-domain-12345.com/test")
    assert isinstance(res, dict)
    assert "error" in res


def test_platform_aliases():
    assert callable(download.youtube)
    assert callable(download.tiktok)
    assert callable(download.instagram)
    assert callable(download.facebook)
    assert callable(download.x)
    assert callable(download.twitter)

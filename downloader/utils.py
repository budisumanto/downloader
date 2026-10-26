import io
import mimetypes
import os
import re
from typing import Any, Dict, List, Optional, Tuple, Union
import requests

PLATFORM_PATTERNS = {
    "youtube": r"(https?://)?(www\.|m\.)?(youtube\.com|youtu\.be)/.+",
    "tiktok": r"(https?://)?(www\.|vm\.|vt\.)?tiktok\.com/.+",
    "instagram": r"(https?://)?(www\.)?(instagram\.com|instagr\.am)/.+",
    "facebook": r"(https?://)?(www\.|m\.|web\.|fb\.)?(facebook\.com|fb\.watch|fb\.com)/.+",
    "x": r"(https?://)?(www\.|mobile\.)?(twitter\.com|x\.com|t\.co)/.+",
}


def detect_platform(url: str) -> Optional[str]:
    """Detect platform from URL using regex."""
    if not url:
        return None

    for platform, pattern in PLATFORM_PATTERNS.items():
        if re.match(pattern, url, re.IGNORECASE):
            return platform
    return None


def resolve_url(url: str, timeout: int = 10) -> str:
    """Follow redirects to resolve short links if necessary."""
    try:
        response = requests.head(url, allow_redirects=True, timeout=timeout)
        return response.url
    except Exception:
        try:
            response = requests.get(url, allow_redirects=True, timeout=timeout, stream=True)
            return response.url
        except Exception:
            return url


def get_mimetype(filepath_or_url: str, default: str = "application/octet-stream") -> str:
    """Guess mimetype from file path or URL."""
    mime, _ = mimetypes.guess_type(filepath_or_url)
    if mime:
        return mime

    ext = os.path.splitext(filepath_or_url)[1].lower()
    ext_map = {
        ".mp4": "video/mp4",
        ".webm": "video/webm",
        ".mkv": "video/x-matroska",
        ".mov": "video/quicktime",
        ".avi": "video/x-msvideo",
        ".mp3": "audio/mpeg",
        ".m4a": "audio/mp4",
        ".ogg": "audio/ogg",
        ".wav": "audio/wav",
        ".flac": "audio/flac",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }
    return ext_map.get(ext, default)


def select_best_yt_dlp_format(
    formats: List[Dict[str, Any]],
    target_resolution: Optional[Union[int, str]] = None,
    media_type: str = "video",
) -> Optional[str]:
    """Select yt-dlp format selector string or format_id based on requested resolution."""
    if media_type == "audio":
        return "bestaudio/best"

    if target_resolution is None or target_resolution == "best":
        return "bestvideo+bestaudio/best"
    if target_resolution == "worst":
        return "worstvideo+worstaudio/worst"

    try:
        target_h = int(target_resolution)
    except (ValueError, TypeError):
        return "bestvideo+bestaudio/best"

    # If we have a format list from extract_info, pick closest height
    video_formats = [
        f for f in formats if f.get("vcodec") != "none" and f.get("height") is not None
    ]
    if not video_formats:
        return f"bestvideo[height<={target_h}]+bestaudio/best[height<={target_h}]/best"

    closest_format = min(
        video_formats, key=lambda f: abs(f["height"] - target_h)
    )
    format_id = closest_format.get("format_id")
    if format_id:
        return f"{format_id}+bestaudio/best"

    return f"bestvideo[height<={target_h}]+bestaudio/best[height<={target_h}]/best"


def check_file_size(filepath: str, max_filesize: Optional[Union[int, float]] = None) -> Optional[Dict[str, Any]]:
    """Check if file exceeds max_filesize limit (in bytes)."""
    if not max_filesize:
        return None

    try:
        size = os.path.getsize(filepath)
        if size > max_filesize:
            return {
                "error": f"File size ({size} bytes) exceeds limit of {max_filesize} bytes",
                "exceeded_limit": True,
            }
    except Exception as e:
        return {"error": f"Failed to check file size: {str(e)}"}

    return None


def prepare_media_result(
    filepath: str,
    media_type: str,
    as_bytes: bool = False,
    max_filesize: Optional[Union[int, float]] = None,
) -> Dict[str, Any]:
    """Format single media result item."""
    size_error = check_file_size(filepath, max_filesize)
    if size_error:
        return size_error

    mimetype = get_mimetype(filepath)
    result = {
        "type": media_type,
        "path": filepath,
        "mimetype": mimetype,
    }

    if as_bytes:
        try:
            with open(filepath, "rb") as f:
                result["bytes"] = io.BytesIO(f.read())
        except Exception as e:
            return {"error": f"Failed to read file as bytes: {str(e)}"}

    return result

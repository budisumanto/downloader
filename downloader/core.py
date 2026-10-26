from typing import Any, Dict, List, Optional, Union
from .extractors import extract_media


def download(
    url: str,
    resolution: Optional[Union[int, str]] = None,
    media_type: str = "video",
    as_bytes: bool = False,
    output_dir: Optional[str] = None,
    timeout: int = 30,
    max_filesize: Optional[Union[int, float]] = None,
    cookies_path: Optional[str] = None,
) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """Download media from supported platforms with auto platform detection."""
    return extract_media(
        url=url,
        resolution=resolution,
        media_type=media_type,
        as_bytes=as_bytes,
        output_dir=output_dir,
        timeout=timeout,
        max_filesize=max_filesize,
        cookies_path=cookies_path,
    )


def youtube(
    url: str,
    resolution: Optional[Union[int, str]] = None,
    media_type: str = "video",
    as_bytes: bool = False,
    output_dir: Optional[str] = None,
    timeout: int = 30,
    max_filesize: Optional[Union[int, float]] = None,
    cookies_path: Optional[str] = None,
) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """Download media from YouTube."""
    return extract_media(
        url=url,
        resolution=resolution,
        media_type=media_type,
        as_bytes=as_bytes,
        output_dir=output_dir,
        timeout=timeout,
        max_filesize=max_filesize,
        cookies_path=cookies_path,
        platform="youtube",
    )


def tiktok(
    url: str,
    resolution: Optional[Union[int, str]] = None,
    media_type: str = "video",
    as_bytes: bool = False,
    output_dir: Optional[str] = None,
    timeout: int = 30,
    max_filesize: Optional[Union[int, float]] = None,
    cookies_path: Optional[str] = None,
) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """Download media from TikTok."""
    return extract_media(
        url=url,
        resolution=resolution,
        media_type=media_type,
        as_bytes=as_bytes,
        output_dir=output_dir,
        timeout=timeout,
        max_filesize=max_filesize,
        cookies_path=cookies_path,
        platform="tiktok",
    )


def instagram(
    url: str,
    resolution: Optional[Union[int, str]] = None,
    media_type: str = "video",
    as_bytes: bool = False,
    output_dir: Optional[str] = None,
    timeout: int = 30,
    max_filesize: Optional[Union[int, float]] = None,
    cookies_path: Optional[str] = None,
) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """Download media from Instagram."""
    return extract_media(
        url=url,
        resolution=resolution,
        media_type=media_type,
        as_bytes=as_bytes,
        output_dir=output_dir,
        timeout=timeout,
        max_filesize=max_filesize,
        cookies_path=cookies_path,
        platform="instagram",
    )


def facebook(
    url: str,
    resolution: Optional[Union[int, str]] = None,
    media_type: str = "video",
    as_bytes: bool = False,
    output_dir: Optional[str] = None,
    timeout: int = 30,
    max_filesize: Optional[Union[int, float]] = None,
    cookies_path: Optional[str] = None,
) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """Download media from Facebook."""
    return extract_media(
        url=url,
        resolution=resolution,
        media_type=media_type,
        as_bytes=as_bytes,
        output_dir=output_dir,
        timeout=timeout,
        max_filesize=max_filesize,
        cookies_path=cookies_path,
        platform="facebook",
    )


def x(
    url: str,
    resolution: Optional[Union[int, str]] = None,
    media_type: str = "video",
    as_bytes: bool = False,
    output_dir: Optional[str] = None,
    timeout: int = 30,
    max_filesize: Optional[Union[int, float]] = None,
    cookies_path: Optional[str] = None,
) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """Download media from X (Twitter)."""
    return extract_media(
        url=url,
        resolution=resolution,
        media_type=media_type,
        as_bytes=as_bytes,
        output_dir=output_dir,
        timeout=timeout,
        max_filesize=max_filesize,
        cookies_path=cookies_path,
        platform="x",
    )


# Attach platform specific aliases to download function object
download.youtube = youtube  # type: ignore
download.tiktok = tiktok  # type: ignore
download.instagram = instagram  # type: ignore
download.facebook = facebook  # type: ignore
download.x = x  # type: ignore
download.twitter = x  # type: ignore

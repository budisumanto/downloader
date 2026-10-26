import os
import re
import tempfile
from typing import Any, Dict, List, Optional, Union
import requests
import yt_dlp

from .clean import create_temp_dir, register_temp_path
from .utils import (
    check_file_size,
    detect_platform,
    prepare_media_result,
    resolve_url,
    select_best_yt_dlp_format,
)


def extract_media(
    url: str,
    resolution: Optional[Union[int, str]] = None,
    media_type: str = "video",
    as_bytes: bool = False,
    output_dir: Optional[str] = None,
    timeout: int = 30,
    max_filesize: Optional[Union[int, float]] = None,
    cookies_path: Optional[str] = None,
    platform: Optional[str] = None,
) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """Extract and download media from supported platforms."""
    if not url:
        return {"error": "Invalid or empty URL"}

    # Resolve short URL if necessary
    resolved_url = resolve_url(url, timeout=min(timeout, 10))
    detected = platform or detect_platform(resolved_url) or detect_platform(url)

    # Attempt yt-dlp first for video/audio or general extraction
    res = _download_via_ytdlp(
        url=resolved_url,
        resolution=resolution,
        media_type=media_type,
        as_bytes=as_bytes,
        output_dir=output_dir,
        timeout=timeout,
        max_filesize=max_filesize,
        cookies_path=cookies_path,
    )

    if not isinstance(res, dict) or "error" not in res:
        return res

    # If yt-dlp returned error, attempt custom extractors for specific image multi-media/carousels
    if detected in ("x", "twitter"):
        custom_res = _extract_x_images(
            url=resolved_url,
            as_bytes=as_bytes,
            output_dir=output_dir,
            timeout=timeout,
            max_filesize=max_filesize,
        )
        if custom_res and not (isinstance(custom_res, dict) and "error" in custom_res):
            return custom_res

    elif detected == "tiktok":
        custom_res = _extract_tiktok_slides(
            url=resolved_url,
            as_bytes=as_bytes,
            output_dir=output_dir,
            timeout=timeout,
            max_filesize=max_filesize,
        )
        if custom_res and not (isinstance(custom_res, dict) and "error" in custom_res):
            return custom_res

    elif detected == "instagram":
        custom_res = _extract_instagram_carousel(
            url=resolved_url,
            as_bytes=as_bytes,
            output_dir=output_dir,
            timeout=timeout,
            max_filesize=max_filesize,
            cookies_path=cookies_path,
        )
        if custom_res and not (isinstance(custom_res, dict) and "error" in custom_res):
            return custom_res

    return res


def _download_via_ytdlp(
    url: str,
    resolution: Optional[Union[int, str]] = None,
    media_type: str = "video",
    as_bytes: bool = False,
    output_dir: Optional[str] = None,
    timeout: int = 30,
    max_filesize: Optional[Union[int, float]] = None,
    cookies_path: Optional[str] = None,
) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """Download using yt-dlp engine."""
    out_folder = output_dir or create_temp_dir()
    os.makedirs(out_folder, exist_ok=True)
    out_tmpl = os.path.join(out_folder, "%(id)s.%(ext)s")

    ydl_opts: Dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "outtmpl": out_tmpl,
        "socket_timeout": timeout,
    }

    if cookies_path and os.path.isfile(cookies_path):
        ydl_opts["cookiefile"] = cookies_path

    if media_type == "audio":
        ydl_opts["format"] = "bestaudio/best"
        ydl_opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]
    else:
        # Check available formats first to pick closest resolution if needed
        format_selector = "bestvideo+bestaudio/best"
        if resolution is not None:
            try:
                info_opts = dict(ydl_opts)
                info_opts["skip_download"] = True
                with yt_dlp.YoutubeDL(info_opts) as ydl_info:
                    info_dict = ydl_info.extract_info(url, download=False)
                    if info_dict and "formats" in info_dict:
                        format_selector = select_best_yt_dlp_format(
                            info_dict["formats"], target_resolution=resolution, media_type=media_type
                        )
            except Exception:
                pass
        ydl_opts["format"] = format_selector

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if not info:
                return {"error": "Failed to extract media info with yt-dlp"}

            # Handle playlist / multi-item if yt-dlp returns multiple entries
            entries = info.get("entries")
            if entries:
                results = []
                for entry in entries:
                    if not entry:
                        continue
                    filepath = ydl.prepare_filename(entry)
                    if not os.path.exists(filepath):
                        # Try finding file with different ext
                        base, _ = os.path.splitext(filepath)
                        for f in os.listdir(out_folder):
                            if f.startswith(os.path.basename(base)):
                                filepath = os.path.join(out_folder, f)
                                break
                    if os.path.exists(filepath):
                        register_temp_path(filepath)
                        actual_type = "audio" if media_type == "audio" else ("image" if filepath.endswith(('.jpg', '.png', '.webp')) else "video")
                        res = prepare_media_result(filepath, actual_type, as_bytes, max_filesize)
                        if "error" in res:
                            return res
                        results.append(res)
                if results:
                    return results if len(results) > 1 else results[0]

            # Single item
            filepath = ydl.prepare_filename(info)
            if not os.path.exists(filepath):
                # Check if file has different ext after post-processing
                base, _ = os.path.splitext(filepath)
                found = None
                for f in os.listdir(out_folder):
                    if f.startswith(os.path.basename(base)):
                        found = os.path.join(out_folder, f)
                        break
                if found:
                    filepath = found

            if not os.path.exists(filepath):
                return {"error": "Downloaded file not found"}

            register_temp_path(filepath)
            actual_type = "audio" if media_type == "audio" else ("image" if filepath.endswith(('.jpg', '.jpeg', '.png', '.webp')) else "video")
            return prepare_media_result(filepath, actual_type, as_bytes, max_filesize)

    except yt_dlp.utils.DownloadError as e:
        msg = str(e)
        if "exceeds" in msg.lower() or "too large" in msg.lower():
            return {"error": msg, "exceeded_limit": True}
        return {"error": f"yt-dlp error: {msg}"}
    except Exception as e:
        return {"error": f"Download exception: {str(e)}"}


def _extract_x_images(
    url: str,
    as_bytes: bool = False,
    output_dir: Optional[str] = None,
    timeout: int = 30,
    max_filesize: Optional[Union[int, float]] = None,
) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """Custom extractor for X/Twitter multi-photo posts."""
    tweet_id_match = re.search(r"status/(\d+)", url)
    if not tweet_id_match:
        return {"error": "Could not parse Tweet ID"}

    tweet_id = tweet_id_match.group(1)
    # Attempt syndication API
    syndication_url = f"https://cdn.syndication.twimg.com/tweet-result?id={tweet_id}&token=x"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        resp = requests.get(syndication_url, headers=headers, timeout=timeout)
        if resp.status_code == 200:
            data = resp.json()
            media_details = data.get("mediaDetails", [])
            image_urls = []
            for media in media_details:
                if media.get("type") == "photo":
                    img_url = media.get("media_url_https")
                    if img_url:
                        # Request high res
                        image_urls.append(f"{img_url}?name=orig")

            if image_urls:
                return _download_image_urls(image_urls, output_dir, as_bytes, max_filesize, timeout)
    except Exception:
        pass

    # HTML meta tag fallback
    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        if resp.status_code == 200:
            og_images = re.findall(r'property="og:image"\s+content="([^"]+)"', resp.text)
            valid_images = [img for img in og_images if "default-og" not in img and "profile_images" not in img]
            if valid_images:
                return _download_image_urls(valid_images, output_dir, as_bytes, max_filesize, timeout)
    except Exception:
        pass

    return {"error": "No media found for X/Twitter tweet"}


def _extract_tiktok_slides(
    url: str,
    as_bytes: bool = False,
    output_dir: Optional[str] = None,
    timeout: int = 30,
    max_filesize: Optional[Union[int, float]] = None,
) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """Custom extractor for TikTok image slides."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        if resp.status_code == 200:
            # Extract image URLs from SIGI_STATE or __UNIVERSAL_DATA_FOR_REHYDRATION__
            image_urls = re.findall(r'"display_image":\s*\{\s*"url_list":\s*\["([^"]+)"', resp.text)
            if not image_urls:
                image_urls = re.findall(r'"imageUrl":\s*"([^"]+)"', resp.text)

            # Clean backslashes
            image_urls = [img.replace("\\u002F", "/").replace("\\/", "/") for img in image_urls]
            image_urls = list(dict.fromkeys(image_urls))  # deduplicate

            if image_urls:
                return _download_image_urls(image_urls, output_dir, as_bytes, max_filesize, timeout)
    except Exception:
        pass

    return {"error": "No slides found for TikTok link"}


def _extract_instagram_carousel(
    url: str,
    as_bytes: bool = False,
    output_dir: Optional[str] = None,
    timeout: int = 30,
    max_filesize: Optional[Union[int, float]] = None,
    cookies_path: Optional[str] = None,
) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """Custom extractor for Instagram photo carousel."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    cookies = {}
    if cookies_path and os.path.exists(cookies_path):
        try:
            with open(cookies_path, "r") as f:
                for line in f:
                    if not line.startswith("#") and line.strip():
                        parts = line.strip().split("\t")
                        if len(parts) >= 7:
                            cookies[parts[5]] = parts[6]
        except Exception:
            pass

    try:
        resp = requests.get(url, headers=headers, cookies=cookies, timeout=timeout)
        if resp.status_code == 200:
            og_images = re.findall(r'property="og:image"\s+content="([^"]+)"', resp.text)
            if og_images:
                clean_imgs = [img.replace("&amp;", "&") for img in og_images]
                return _download_image_urls(clean_imgs, output_dir, as_bytes, max_filesize, timeout)
    except Exception:
        pass

    return {"error": "No media found for Instagram post"}


def _download_image_urls(
    image_urls: List[str],
    output_dir: Optional[str],
    as_bytes: bool,
    max_filesize: Optional[Union[int, float]],
    timeout: int,
) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """Helper to download a list of image URLs."""
    out_folder = output_dir or create_temp_dir()
    os.makedirs(out_folder, exist_ok=True)

    results = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    for idx, img_url in enumerate(image_urls):
        try:
            r = requests.get(img_url, headers=headers, timeout=timeout)
            if r.status_code == 200:
                ext = ".jpg"
                if "image/png" in r.headers.get("content-type", ""):
                    ext = ".png"
                elif "image/webp" in r.headers.get("content-type", ""):
                    ext = ".webp"

                filepath = os.path.join(out_folder, f"image_{idx+1}{ext}")
                with open(filepath, "wb") as f:
                    f.write(r.content)

                register_temp_path(filepath)
                res = prepare_media_result(filepath, "image", as_bytes, max_filesize)
                if "error" in res:
                    return res
                results.append(res)
        except Exception as e:
            continue

    if not results:
        return {"error": "Failed to download image resources"}

    return results if len(results) > 1 else results[0]

"""Fetch a direct audio or video URL into an output directory."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Callable, Optional
from urllib.parse import urlparse, urlunparse
from urllib.request import Request, urlopen


MEDIA_EXTENSIONS = {
    ".aac",
    ".flac",
    ".m4a",
    ".m4v",
    ".mkv",
    ".mov",
    ".mp3",
    ".mp4",
    ".ogg",
    ".opus",
    ".wav",
    ".webm",
}
RESERVED_NAMES = {
    "raw-transcript.txt",
    "segments.json",
    "transcript.md",
    "transcript.srt",
    "transcript.vtt",
}


def is_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def display_url(url: str) -> str:
    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    netloc = f"{hostname}:{parsed.port}" if parsed.port else hostname
    return urlunparse((parsed.scheme, netloc, parsed.path, "", "", ""))


def media_filename(url: str, content_type: str) -> str:
    suffix = Path(urlparse(url).path).suffix.lower()
    if suffix not in MEDIA_EXTENSIONS:
        suffix = _suffix_for_type(content_type) or ""
    stem = Path(urlparse(url).path).stem
    stem = re.sub(r"[^A-Za-z0-9._-]", "_", stem).strip("._")
    if not stem:
        stem = "source-media"
    name = f"{stem[:80]}{suffix}"
    if name in RESERVED_NAMES or not suffix:
        name = f"source-media{suffix or '.bin'}"
    return name


def is_direct_media(url: str, content_type: str) -> bool:
    kind = content_type.split(";", 1)[0].strip().lower()
    if kind.startswith(("audio/", "video/")):
        return True
    if kind in {"application/octet-stream", "binary/octet-stream", ""}:
        return Path(urlparse(url).path).suffix.lower() in MEDIA_EXTENSIONS
    return False


def fetch_media(
    url: str,
    output_dir: Path,
    *,
    opener: Optional[Callable] = None,
) -> Path:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise RuntimeError("only a direct http(s) audio or video URL is accepted")
    if parsed.username or parsed.password:
        raise RuntimeError("refusing a URL with embedded credentials")
    request = Request(url, headers={"User-Agent": "podcast-transcript"})
    open_url = opener or urlopen
    try:
        response = open_url(request, timeout=60)
    except OSError as exc:
        raise RuntimeError(f"could not fetch media: {display_url(url)}") from exc
    with response:
        content_type = ""
        headers = getattr(response, "headers", {}) or {}
        if hasattr(headers, "get"):
            content_type = headers.get("Content-Type") or headers.get("content-type") or ""
        if not is_direct_media(url, str(content_type)):
            raise RuntimeError(
                f"URL is not a direct audio or video file: {display_url(url)}"
            )
        target = output_dir / media_filename(url, str(content_type))
        if target.exists():
            raise FileExistsError(f"refusing to overwrite: {target.name}")
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        handle = os.open(target, flags)
        try:
            with os.fdopen(handle, "wb") as stream:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    stream.write(chunk)
        except BaseException:
            target.unlink(missing_ok=True)
            raise
    return target


def _suffix_for_type(content_type: str) -> str:
    kind = content_type.split(";", 1)[0].strip().lower()
    return {
        "audio/mpeg": ".mp3",
        "audio/mp4": ".m4a",
        "audio/wav": ".wav",
        "audio/x-wav": ".wav",
        "audio/flac": ".flac",
        "audio/ogg": ".ogg",
        "video/mp4": ".mp4",
        "video/webm": ".webm",
    }.get(kind, "")

"""Render segments.json as Markdown, SRT, or WebVTT."""

from __future__ import annotations

import json
import os
from pathlib import Path


def load_segments(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError("segments file is not valid JSON") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("segments"), list):
        raise RuntimeError("segments file is missing a segment list")
    return payload


def render_markdown(payload: dict) -> str:
    lines = ["# Transcript", ""]
    for segment in payload["segments"]:
        text = _cue_text(segment)
        if not text:
            continue
        speaker = segment.get("speaker")
        if speaker:
            lines.append(f"**{speaker}**: {text}")
        else:
            lines.append(text)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_srt(payload: dict) -> str:
    return _render_cues(payload, decimal=",")


def render_vtt(payload: dict) -> str:
    body = _render_cues(payload, decimal=".")
    return "WEBVTT\n\n" + body


def write_exclusive(path: Path, text: str) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite: {path.name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    handle = os.open(path, flags)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            stream.write(text)
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def export_segments(source: Path, kind: str, destination: Path) -> None:
    payload = load_segments(source)
    if kind == "md":
        text = render_markdown(payload)
    elif kind == "srt":
        text = render_srt(payload)
    elif kind == "vtt":
        text = render_vtt(payload)
    else:
        raise RuntimeError(f"unsupported export format: {kind}")
    write_exclusive(destination, text)


def format_timestamp(seconds: float, decimal: str) -> str:
    if seconds < 0:
        seconds = 0.0
    millis = int(seconds * 1000 + 0.5)
    hours, rem = divmod(millis, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    secs, millis = divmod(rem, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}{decimal}{millis:03d}"


def _cue_text(segment: dict) -> str:
    text = str(segment.get("text", "")).replace("\n", " ").strip()
    return text.replace("-->", "->")


def _render_cues(payload: dict, decimal: str) -> str:
    blocks = []
    index = 1
    for segment in payload["segments"]:
        text = _cue_text(segment)
        if not text:
            continue
        start = float(segment.get("start", 0))
        end = float(segment.get("end", start))
        if end <= start:
            end = start + 0.001
        speaker = segment.get("speaker")
        if speaker:
            text = f"{speaker}: {text}"
        blocks.append(
            "\n".join(
                [
                    str(index),
                    f"{format_timestamp(start, decimal)} --> {format_timestamp(end, decimal)}",
                    text,
                ]
            )
        )
        index += 1
    if not blocks:
        return ""
    return "\n\n".join(blocks) + "\n"

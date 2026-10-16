from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Callable, Optional


logger = logging.getLogger(__name__)

from runtime_paths import (
    RuntimePaths,
    atomic_write_json,
    atomic_write_text,
    build_runtime_paths,
    runtime_python,
)


def transcribe_audio(
    audio_path: Path,
    raw_output: Path,
    segments_output: Path,
    state: dict,
    *,
    language: Optional[str] = None,
    mlx_runner: Optional[Callable] = None,
    faster_runner: Optional[Callable] = None,
) -> dict:
    if state.get("status") != "complete":
        raise RuntimeError("transcription requires a complete runtime")
    if not audio_path.is_file():
        raise FileNotFoundError(audio_path)
    if raw_output.exists() or segments_output.exists():
        raise FileExistsError("refusing to overwrite transcript output")
    model_path = Path(state["model_path"])
    if not model_path.is_dir():
        raise FileNotFoundError(model_path)

    backend = state["backend"]
    if backend == "mlx":
        runner = mlx_runner or run_mlx
        detected, segments = runner(audio_path, model_path, language)
    elif backend == "faster":
        runner = faster_runner or run_faster
        detected, segments = runner(
            audio_path,
            model_path,
            state.get("device", "cpu"),
            state.get("compute_type", "int8"),
            language,
        )
    else:
        raise RuntimeError(f"unsupported installed backend: {backend}")

    normalized = [
        {
            "start": float(item["start"]),
            "end": float(item["end"]),
            "text": str(item["text"]).strip(),
        }
        for item in segments
        if str(item.get("text", "")).strip()
    ]
    text = "".join(f"{item['text']}\n" for item in normalized)
    payload = {"language": detected, "segments": normalized}
    atomic_write_text(raw_output, text)
    try:
        atomic_write_json(segments_output, payload)
    except BaseException:
        raw_output.unlink(missing_ok=True)
        raise
    return payload


def run_mlx(audio: Path, model: Path, language: Optional[str]):
    import mlx_whisper

    kwargs = {"word_timestamps": True}
    if language:
        kwargs["language"] = language
    result = mlx_whisper.transcribe(
        str(audio), path_or_hf_repo=str(model), **kwargs
    )
    segments = [
        {
            "start": segment["start"],
            "end": segment["end"],
            "text": segment["text"],
        }
        for segment in result.get("segments", [])
    ]
    return result.get("language") or language or "unknown", segments


def run_faster(
    audio: Path,
    model: Path,
    device: str,
    compute_type: str,
    language: Optional[str],
):
    from faster_whisper import WhisperModel

    def execute(selected_device: str, selected_compute: str):
        instance = WhisperModel(
            str(model),
            device=selected_device,
            compute_type=selected_compute,
            local_files_only=True,
        )
        stream, info = instance.transcribe(
            str(audio),
            language=language,
            word_timestamps=True,
            vad_filter=True,
        )
        items = [
            {"start": item.start, "end": item.end, "text": item.text}
            for item in stream
        ]
        return info.language, items

    try:
        return execute(device, compute_type)
    except RuntimeError as exc:
        if device != "cuda":
            raise
        logger.warning(
            "faster-whisper CUDA inference failed (%s); falling back to CPU with int8",
            exc,
        )
        return execute("cpu", "int8")


def _load_state(paths: RuntimePaths) -> dict:
    if not paths.state.is_file():
        raise RuntimeError("local transcription runtime is not installed")
    state = json.loads(paths.state.read_text(encoding="utf-8"))
    if state.get("status") != "complete":
        raise RuntimeError("local transcription runtime is incomplete")
    return state


def _same_executable(left: Path, right: Path) -> bool:
    return os.path.normcase(os.path.abspath(left)) == os.path.normcase(
        os.path.abspath(right)
    )


def _inside(path: Path, root: Path) -> bool:
    return path == root or root in path.parents


def _validate_output_directory(output_dir: Path, paths: RuntimePaths) -> Path:
    selected = output_dir.expanduser().resolve()
    skill_root = Path(__file__).resolve().parents[1]
    cache_root = paths.root.expanduser().resolve()
    if _inside(selected, skill_root) or _inside(selected, cache_root):
        raise RuntimeError("output directory must be outside the skill and runtime cache")
    return selected


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Transcribe media with an installed local model."
    )
    parser.add_argument("input", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--language")
    parser.add_argument(
        "--inside-runtime", action="store_true", help=argparse.SUPPRESS
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = _parser().parse_args(argv)
    paths = build_runtime_paths()
    state = _load_state(paths)
    python = runtime_python(paths)
    if not args.inside_runtime:
        if not python.is_file():
            raise RuntimeError("installed runtime Python is missing")
        if not _same_executable(Path(sys.executable), python):
            forwarded = list(sys.argv[1:] if argv is None else argv)
            os.execv(
                str(python),
                [
                    str(python),
                    str(Path(__file__).resolve()),
                    *forwarded,
                    "--inside-runtime",
                ],
            )

    output_dir = _validate_output_directory(args.output_dir, paths)
    payload = transcribe_audio(
        args.input.expanduser().resolve(),
        output_dir / "raw-transcript.txt",
        output_dir / "segments.json",
        state,
        language=args.language,
    )
    print(
        json.dumps(
            {
                "language": payload["language"],
                "segment_count": len(payload["segments"]),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "podcast-trancript-public" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from transcribe import transcribe_audio


class TranscribeTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.audio = self.root / "episode.wav"
        self.audio.write_bytes(b"RIFF-test")
        self.model = self.root / "model"
        self.model.mkdir()

    def state(self, backend="faster", device="cpu"):
        return {
            "status": "complete",
            "backend": backend,
            "profile": "small",
            "model_path": str(self.model),
            "device": device,
            "compute_type": "int8" if backend == "faster" else "float16",
        }

    def test_faster_contract_writes_text_and_segments(self):
        def runner(audio, model, device, compute_type, language):
            self.assertEqual(self.audio, audio)
            self.assertEqual(self.model, model)
            return "zh", [
                {"start": 0.0, "end": 1.5, "text": "第一句。"},
                {"start": 1.5, "end": 3.0, "text": "第二句。"},
            ]

        raw = self.root / "raw-transcript.txt"
        segments = self.root / "segments.json"
        transcribe_audio(
            self.audio,
            raw,
            segments,
            self.state(),
            faster_runner=runner,
        )
        self.assertEqual("第一句。\n第二句。\n", raw.read_text(encoding="utf-8"))
        payload = json.loads(segments.read_text(encoding="utf-8"))
        self.assertEqual("zh", payload["language"])
        self.assertNotIn("speaker", json.dumps(payload).lower())

    def test_mlx_contract_uses_local_model(self):
        seen = {}

        def runner(audio, model, language):
            seen["model"] = model
            return "en", [{"start": 0.0, "end": 1.0, "text": "Hello."}]

        transcribe_audio(
            self.audio,
            self.root / "raw.txt",
            self.root / "segments.json",
            self.state("mlx"),
            mlx_runner=runner,
        )
        self.assertEqual(self.model, seen["model"])

    def test_existing_output_is_never_overwritten(self):
        raw = self.root / "raw.txt"
        raw.write_text("keep", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            transcribe_audio(
                self.audio,
                raw,
                self.root / "segments.json",
                self.state(),
                faster_runner=lambda *args: ("en", []),
            )
        self.assertEqual("keep", raw.read_text(encoding="utf-8"))

    def test_incomplete_state_is_rejected(self):
        bad = self.state()
        bad["status"] = "partial"
        with self.assertRaisesRegex(RuntimeError, "complete runtime"):
            transcribe_audio(
                self.audio,
                self.root / "raw.txt",
                self.root / "segments.json",
                bad,
            )

    def test_cuda_runtime_failure_reuses_local_model_on_cpu(self):
        calls = []

        class FakeInfo:
            language = "en"

        class FakeModel:
            def __init__(
                self, model_path, *, device, compute_type, local_files_only
            ):
                calls.append(
                    (Path(model_path), device, compute_type, local_files_only)
                )
                if device == "cuda":
                    raise RuntimeError("CUDA unavailable")

            def transcribe(self, *args, **kwargs):
                return iter(()), FakeInfo()

        fake_module = type("M", (), {"WhisperModel": FakeModel})
        with patch.dict(sys.modules, {"faster_whisper": fake_module}):
            from transcribe import run_faster

            with self.assertLogs("transcribe", level="WARNING") as captured:
                language, segments = run_faster(
                    self.audio, self.model, "cuda", "float16", None
                )
        self.assertEqual("en", language)
        self.assertEqual([], segments)
        self.assertEqual(
            [
                (self.model, "cuda", "float16", True),
                (self.model, "cpu", "int8", True),
            ],
            calls,
        )
        self.assertTrue(
            any("CPU" in line and "int8" in line for line in captured.output)
        )

    def test_faster_whisper_enables_vad_filter(self):
        seen = {}

        class FakeInfo:
            language = "en"

        class FakeSegment:
            start = 0.0
            end = 1.0
            text = "Hello."

        class FakeModel:
            def __init__(self, *args, **kwargs):
                pass

            def transcribe(self, *args, **kwargs):
                seen.update(kwargs)
                return iter([FakeSegment()]), FakeInfo()

        fake_module = type("M", (), {"WhisperModel": FakeModel})
        with patch.dict(sys.modules, {"faster_whisper": fake_module}):
            from transcribe import run_faster

            language, segments = run_faster(
                self.audio, self.model, "cpu", "int8", None
            )
        self.assertEqual("en", language)
        self.assertEqual("Hello.", segments[0]["text"])
        self.assertTrue(seen["vad_filter"])
        self.assertTrue(seen["word_timestamps"])


if __name__ == "__main__":
    unittest.main()

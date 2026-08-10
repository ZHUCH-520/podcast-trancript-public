import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "podcast-trancript-public" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from doctor import MachineFacts, build_report, recommend_profile
from model_catalog import MODEL_PROFILES, package_requirements
from runtime_paths import build_runtime_paths


class RuntimeDiscoveryTest(unittest.TestCase):
    def test_macos_cache_is_generic(self):
        paths = build_runtime_paths(
            system="Darwin",
            home=Path("/private/example-home"),
            environ={},
        )
        self.assertEqual(
            Path("/private/example-home/Library/Caches/podcast-trancript-public"),
            paths.root,
        )

    def test_windows_cache_uses_local_app_data(self):
        paths = build_runtime_paths(
            system="Windows",
            home=Path("C:/ignored"),
            environ={"LOCALAPPDATA": "C:/LocalData"},
        )
        self.assertEqual(
            Path("C:/LocalData/podcast-trancript-public"),
            paths.root,
        )

    def test_backend_selection_and_recommendations(self):
        apple = MachineFacts(
            "Darwin", "arm64", 16 * 1024**3, False, None, True, True
        )
        windows_cpu = MachineFacts(
            "Windows", "AMD64", 32 * 1024**3, False, None, False, True
        )
        windows_gpu = MachineFacts(
            "Windows", "AMD64", 32 * 1024**3, True, 10 * 1024**3, False, True
        )
        self.assertEqual(("mlx", "turbo"), recommend_profile(apple))
        self.assertEqual(("faster", "small"), recommend_profile(windows_cpu))
        self.assertEqual(("faster", "turbo"), recommend_profile(windows_gpu))

    def test_catalog_is_pinned_and_complete(self):
        self.assertEqual({"small", "turbo", "large-v3"}, set(MODEL_PROFILES))
        for profile in MODEL_PROFILES.values():
            for model in (profile.mlx, profile.faster):
                self.assertRegex(model.revision, r"^[0-9a-f]{40}$")
                self.assertGreater(model.download_bytes, 100_000_000)
                self.assertIn("config.json", model.required_files)
        self.assertIn("mlx-whisper==0.4.3", package_requirements("mlx"))
        self.assertIn("faster-whisper==1.2.1", package_requirements("faster"))

    def test_doctor_report_is_read_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "never-create"
            paths = build_runtime_paths(
                "Darwin", Path(tmp), {"PODCAST_TRANSCRIPT_CACHE": str(root)}
            )
            report = build_report(
                paths,
                MachineFacts(
                    "Darwin", "arm64", 8 * 1024**3, False, None, True, True
                ),
            )
            json.dumps(report)
            self.assertTrue(report["system_dependencies"]["ffmpeg"])
            self.assertFalse(root.exists())


if __name__ == "__main__":
    unittest.main()

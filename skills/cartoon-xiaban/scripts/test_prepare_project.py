"""Local, network-free regression tests for brand snapshot safety and consistency."""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).with_name("prepare_project.py")
ROOT = SCRIPT.parent.parent
spec = importlib.util.spec_from_file_location("prepare_brand", SCRIPT)
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)


class BrandSnapshotTests(unittest.TestCase):
    def test_actual_pack_valid_and_pending_voice_not_fabricated(self):
        profile, paths = prepare.validate(ROOT)
        self.assertEqual(profile["voice"]["status"], "audition_pending")
        self.assertIsNone(profile["voice"]["selected_voice_id"])
        self.assertGreaterEqual(len(paths), 6)

    def test_snapshot_copies_real_assets_and_cannot_overwrite(self):
        with tempfile.TemporaryDirectory(prefix="cartoon-brand-test-") as temp:
            output = Path(temp) / "episode"
            command = [sys.executable, str(SCRIPT), "--output", str(output), "--topic", "别把休息当成落后"]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            lock_path = output / "BRAND_LOCK.json"
            before = lock_path.read_bytes()
            lock = json.loads(before)
            self.assertIsNone(lock["selected_voice_id"])
            self.assertIsNone(lock["selected_music"])
            for item in lock["files"]:
                self.assertEqual(prepare.digest(output / item["path"]), item["sha256"])
            repeat = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(repeat.returncode, 0)
            self.assertEqual(before, lock_path.read_bytes())

    def test_tampered_asset_is_rejected(self):
        with patch.object(prepare, "digest", return_value="0" * 64):
            with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                prepare.validate(ROOT)

    def test_quality_criteria_are_frozen_with_the_project(self):
        with tempfile.TemporaryDirectory(prefix="cartoon-quality-test-") as temp:
            output = Path(temp) / "episode"
            result = subprocess.run([sys.executable, str(SCRIPT), "--output", str(output)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            source = ROOT / "references/quality-regression.md"
            copied = output / "brand/references/quality-regression.md"
            self.assertEqual(source.read_bytes(), copied.read_bytes())
            lock = json.loads((output / "BRAND_LOCK.json").read_text())
            entry = next(x for x in lock["files"] if x["path"] == "brand/references/quality-regression.md")
            self.assertEqual(entry["sha256"], prepare.digest(source))

    def test_asset_path_cannot_escape_pack(self):
        for path in ("../outside.png", "/tmp/outside.png"):
            with self.assertRaisesRegex(ValueError, "Unsafe asset path"):
                prepare.inside(ROOT, path)

    def test_approved_visual_calibration_is_copied_without_promoting_candidates(self):
        profile, _ = prepare.validate(ROOT)
        reference = next(x for x in profile["assets"] if x["id"] == "approved-95s-encoded-calibration")
        self.assertEqual(reference["status"], "user_approved_film_visual_calibration_only")
        candidate = next(x for x in profile["assets"] if x["id"] == "acting-sheet-v3-candidate")
        self.assertEqual(candidate["status"], "candidate_generated_not_yet_user_approved")
        with tempfile.TemporaryDirectory(prefix="cartoon-calibration-test-") as temp:
            output = Path(temp) / "episode"
            result = subprocess.run([sys.executable, str(SCRIPT), "--output", str(output)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((ROOT / reference["path"]).read_bytes(), (output / "brand" / reference["path"]).read_bytes())

    def test_falsely_approved_voice_is_rejected(self):
        profile = json.loads((ROOT / "assets/brand.json").read_text())
        profile["voice"]["status"] = "user_approved"
        with patch.object(prepare.json, "loads", return_value=profile):
            with self.assertRaisesRegex(ValueError, "Approved voice requires"):
                prepare.validate(ROOT)

    def test_credentials_do_not_enter_profile_snapshot(self):
        profile = json.loads((ROOT / "assets/brand.json").read_text())
        profile["voice"]["api_key"] = "test-value-not-a-real-key"
        with patch.object(prepare.json, "loads", return_value=profile):
            with self.assertRaisesRegex(ValueError, "Credential field forbidden"):
                prepare.validate(ROOT)


if __name__ == "__main__":
    unittest.main()

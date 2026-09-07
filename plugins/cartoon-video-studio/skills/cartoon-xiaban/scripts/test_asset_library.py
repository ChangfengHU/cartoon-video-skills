import copy
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import tempfile
import threading
import unittest
import asset_library as lib


class MemoryStore:
    bucket = "test-private"

    def __init__(self):
        self.objects = {}
        self.lock = threading.Lock()

    def private(self):
        return {"r2_dev_enabled": False, "custom_domains": []}

    def put_new(self, key, data):
        with self.lock:
            if key in self.objects:
                raise ValueError("overwrite")
            self.objects[key] = data

    def get(self, key):
        return self.objects[key]

    def list(self, prefix):
        with self.lock:
            return [{"key": k} for k in sorted(self.objects) if k.startswith(prefix)]


def card(kind="sfx"):
    return {"schema_version": 1, "kind": kind, "title": "通知", "tags": ["轻巧"],
            "source_url": "project://test/original.py", "source_type": "original_algorithm",
            "use_cases": ["消息弹出"], "review_status": "candidate", "audition": {"status": "not_listened"},
            "license": {"status": "user_authorized_generated", "scope": "private archive", "evidence": "fixture permission", "archive_allowed": True}}


class LibraryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.source = self.root / "notify.wav"
        self.source.write_bytes(b"sample fixture")
        self.store = MemoryStore()

    def tearDown(self):
        self.temp.cleanup()

    def imported(self, kind="sfx"):
        return lib.add(self.store, card(kind), self.root, "notify.wav")

    def selection(self, ident):
        return {"project": "test-project", "story_intent": "消息带来误会", "platform": "douyin", "selected": [
            {"asset_id": ident, "reason": "通知动作", "project_review": {"status": "verified_for_project", "allowed_platforms": ["douyin"], "evidence": "fixture review", "checked_at": lib.now()}}]}

    def test_roundtrip_hash_and_no_overwrite(self):
        result = self.imported()
        loaded = lib.load_record(self.store, "records", result["id"])
        target = self.root / "download.wav"
        lib.download(self.store, loaded, target)
        self.assertEqual(target.read_bytes(), self.source.read_bytes())
        with self.assertRaises(FileExistsError):
            lib.download(self.store, loaded, target)
        self.store.objects[loaded["object"]["key"]] = b"changed"
        with self.assertRaisesRegex(ValueError, "SHA256"):
            lib.download(self.store, loaded, self.root / "bad.wav")
        self.assertFalse((self.root / "bad.wav").exists())

    def test_record_tampering_is_detected(self):
        result = self.imported()
        self.store.objects[lib.record_key("records", result["id"])] = b"{}"
        with self.assertRaisesRegex(ValueError, "SHA256"):
            lib.index(self.store)

    def test_rights_gate_and_personal_audio(self):
        c = card("bgm")
        c["license"] = {"status": "unknown", "scope": "unknown", "evidence": "source only", "archive_allowed": False}
        result = lib.add(self.store, c)
        self.assertIsNone(result["record"]["object"])
        with self.assertRaisesRegex(ValueError, "archive rights"):
            lib.add(self.store, c, self.root, "notify.wav")
        for change in ({"voice_identity": "user_clone"}, {"personal_reference": True}, {"api_token": "dummy"}):
            c = {**card("voice"), **change}
            with self.assertRaises(ValueError):
                lib.add(self.store, c, self.root, "notify.wav")

    def test_paths_and_symlinks(self):
        for name in ("../notify.wav", "/tmp/x.wav", "a/../../x", "a\\x"):
            with self.assertRaises(ValueError):
                lib.local_source(self.root, name)
        (self.root / "escape").symlink_to(self.root.parent, target_is_directory=True)
        with self.assertRaises(ValueError):
            lib.write_new(self.root / "escape" / "must-not-exist.wav", b"x")
        (self.root / "link.wav").symlink_to(self.source)
        with self.assertRaises(ValueError):
            lib.write_new(self.root / "link.wav", b"x")
        with self.assertRaises(ValueError):
            lib.record_key("records", "../../escape")

    def test_concurrent_append_and_feedback_not_lost(self):
        def publish(i):
            result = lib.add(self.store, {**card(), "title": f"asset-{i}"})
            lib.feedback(self.store, {"asset_id": result["id"], "project": "fixture", "outcome": "rejected", "reason": "too dense", "reviewer": "editor", "observed_at": lib.now()})
            return result["id"]
        with ThreadPoolExecutor(max_workers=8) as pool:
            ids = list(pool.map(publish, range(24)))
        value = lib.index(self.store)
        self.assertEqual(len(set(ids)), 24)
        self.assertEqual(len(value["records"]), 24)
        self.assertEqual(len(value["feedback"]), 24)
        self.assertTrue(all(r["review_status"] == "candidate" for r in value["records"]))
        self.assertEqual(len(lib.search(value, "asset-13")[0]["feedback"]), 1)

    def test_freeze_is_immutable_and_requires_fresh_bgm_research(self):
        result = self.imported("bgm")
        selection = self.selection(result["id"])
        with self.assertRaisesRegex(ValueError, "new music research"):
            lib.freeze(self.store, selection, self.root / "snapshot")
        self.assertFalse((self.root / "snapshot").exists())
        selection["new_music_research"] = {"performed": True, "checked_at": lib.now(), "queries": ["sparse comedy"], "source_urls": ["https://example.com/source"], "new_candidates": [], "no_new_candidate_reason": "fixture search yielded none"}
        lib.freeze(self.store, selection, self.root / "snapshot")
        lock = json.loads((self.root / "snapshot/ASSET_LIBRARY_LOCK.json").read_text())
        self.assertEqual(lock["records"][0]["audition"]["status"], "not_listened")
        file = lock["files"][0]
        self.assertEqual(lib.sha((self.root / "snapshot" / file["path"]).read_bytes()), file["sha256"])
        with self.assertRaises(ValueError):
            lib.freeze(self.store, selection, self.root / "snapshot")

    def test_project_rights_not_inherited(self):
        result = self.imported()
        selection = self.selection(result["id"])
        selection["platform"] = "unreviewed-platform"
        with self.assertRaisesRegex(ValueError, "project-specific rights"):
            lib.freeze(self.store, selection, self.root / "snapshot")

    def test_rest_pagination_and_broken_cursor(self):
        r2 = lib.R2("0" * 32, "test-token", "private-fixture")
        requests = []
        def request(method, path):
            requests.append(path)
            if "cursor=" not in path:
                return {"result": [{"key": "a"}], "result_info": {"is_truncated": True, "cursor": "next/page"}}
            return {"result": [{"key": "b"}], "result_info": {"is_truncated": False}}
        r2.request = request
        self.assertEqual(len(r2.list("xiaban/v1/records/")), 2)
        self.assertIn("cursor=next%2Fpage", requests[1])
        r2.request = lambda *args: {"result": [], "result_info": {"is_truncated": True, "cursor": "same"}}
        with self.assertRaisesRegex(ValueError, "cursor"):
            r2.list("xiaban/v1/records/")

    def test_native_public_access_is_rejected(self):
        r2 = lib.R2("0" * 32, "test-token", "private-fixture")
        r2.request = lambda method, path: {"result": {"enabled": True} if path.endswith("managed") else {"domains": []}}
        with self.assertRaisesRegex(ValueError, "r2.dev"):
            r2.private()


if __name__ == "__main__":
    unittest.main()

"""离线发布可靠性测试；不读取 token、不调用 Cloudflare、不上传。"""
import importlib.util
import pathlib
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("deploy_pages", pathlib.Path(__file__).with_name("deploy_pages.py"))
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)


class DeploymentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.temp.name)
        self.patches = [patch.object(d, "ROOT", self.root),
                        patch.object(d, "STAGE", self.root / "old"),
                        patch.object(d, "MANIFEST_FILE", self.root / "baseline.json")]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()
        self.temp.cleanup()

    def test_fresh_stage_does_not_upload_deleted_or_private_files(self):
        (self.root / "index.html").write_text("one")
        old = self.root / "old"
        old.mkdir()
        (old / "obsolete.html").write_text("stale")
        with patch.object(d, "build_keep", return_value=["index.html"]):
            d.stage()
            first = d.STAGE
            d.stage()
        self.assertNotEqual(first, d.STAGE)
        self.assertFalse((d.STAGE / "obsolete.html").exists())
        self.assertTrue((old / "obsolete.html").exists())
        for rel in ("admin/index.html", "data/vehicles.json", ".workbuddy/cf_token.txt"):
            self.assertFalse(d._manifest_path(rel))

    def test_snapshot_rejects_unlisted_file_and_changed_content(self):
        d.STAGE.mkdir()
        page = d.STAGE / "index.html"
        page.write_text("one")
        manifest = d.build_manifest()
        d.verify_snapshot(manifest)
        page.write_text("two")
        with self.assertRaises(ValueError):
            d.verify_snapshot(manifest)
        manifest = d.build_manifest()
        (d.STAGE / ".secret").write_text("private")
        with self.assertRaises(ValueError):
            d.verify_snapshot(manifest)

    def test_purge_deleted_paths_queries_and_both_hosts_without_full_zone(self):
        old = {"files": {"en/cars/1/index.html": "a", "assets/x.css": "b"},
               "query_urls": {"assets/x.css": ["https://jinbacars.com/assets/x.css?v=old"]}}
        new = {"files": {"assets/x.css": "c"}, "query_urls": {}}
        full, urls = d.purge_plan(new, old)
        self.assertFalse(full)
        self.assertIn("https://www.jinbacars.com/en/cars/1/", urls)
        self.assertIn("https://jinbacars.com/assets/x.css?v=old", urls)
        self.assertIn("https://www.jinbacars.com/assets/x.css?v=old", urls)
        self.assertTrue(all(d.urlsplit(u).hostname in d.PUBLIC_HOSTS for u in urls))
        full, initial = d.purge_plan(new, None)
        self.assertFalse(full)
        self.assertIn("https://www.jinbacars.com/assets/x.css", initial)

    def test_purge_failure_keeps_baseline_and_returns_failure(self):
        token = self.root / "fake-token"
        token.write_text("test-value")
        zone = self.root / "zone"
        zone.write_text("test-zone")
        d.MANIFEST_FILE.write_text("previous baseline")
        with patch.object(d, "TOKEN_FILE", token), patch.object(d, "ZONE_CACHE", zone), \
             patch.object(d, "load_manifest", return_value=None), \
             patch.object(d, "_cf_api", return_value=(429, '{"success":false}')), \
             patch.object(d.sys, "argv", ["deploy_pages.py"]):
            self.assertEqual(d.purge_cache({"files": {}, "query_urls": {}}), 1)
        self.assertEqual(d.MANIFEST_FILE.read_text(), "previous baseline")

    def test_upload_success_with_failed_purge_is_nonzero(self):
        d.STAGE.mkdir()
        (d.STAGE / "index.html").write_text("one")
        with patch.object(d.sys, "argv", ["deploy_pages.py"]), \
             patch.object(d, "stage"), patch.object(d, "load_manifest", return_value=None), \
             patch.object(d, "deploy", return_value=0), patch.object(d, "purge_cache", return_value=1):
            self.assertEqual(d.main(), 1)


if __name__ == "__main__":
    unittest.main()

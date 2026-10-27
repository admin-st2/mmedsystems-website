#!/usr/bin/env python3
"""No-network acceptance tests for the staging build's safety defaults."""
import os
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch

import build_private_staging as stage


class StagingSafetyTests(unittest.TestCase):
    def tearDown(self):
        if stage.OUTPUT.exists():
            shutil.rmtree(stage.OUTPUT)

    def test_default_deployment_contains_placeholder_not_real_site(self):
        with patch.dict(os.environ, {"MMED_STAGING_MODE": "locked"}, clear=False):
            stage.main()
        files = {p.relative_to(stage.OUTPUT).as_posix()
                 for p in stage.OUTPUT.rglob("*") if p.is_file()}
        self.assertEqual(files, {"index.html", "_headers", "robots.txt"})
        self.assertIn("Private staging is not active", (stage.OUTPUT / "index.html").read_text())
        self.assertIn("Disallow: /", (stage.OUTPUT / "robots.txt").read_text())
        self.assertTrue((stage.OUTPUT / "_headers").read_text().startswith("/*\n"))

    def test_private_mode_fails_closed_if_access_is_not_confirmed(self):
        with patch.dict(os.environ, {
            "MMED_STAGING_MODE": "private",
            "MMED_STAGING_HOST": "example.pages.dev",
        }):
            with patch.object(stage, "access_is_active", return_value=False):
                with self.assertRaises(SystemExit):
                    stage.main()
        self.assertFalse((stage.OUTPUT / "where-we-serve" / "index.html").exists())

    def test_invalid_pages_host_rejected_before_any_network(self):
        for host in ["mmedsystems.com", "example.com", "https://other.pages.dev/",
                     "example.pages.dev.evil.example", ""]:
            self.assertFalse(stage.access_is_active(host))

    def test_staging_export_clones_public_design_without_secrets(self):
        # Simulates Access being verified, but makes no actual network request
        # and does not publish or upload any files.
        with patch.dict(os.environ, {
            "MMED_STAGING_MODE": "private",
            "MMED_STAGING_HOST": "example.pages.dev",
        }):
            with patch.object(stage, "access_is_active", return_value=True):
                stage.main()
        public_home = (stage.ROOT / "index.html").read_text()
        copied = (stage.OUTPUT / "index.html").read_text()
        self.assertIn("Make room", copied)
        self.assertIn("Make room", public_home)
        self.assertIn('href="/mmed-v6.css', copied)
        self.assertIn("__staging_guard", copied)
        self.assertTrue((stage.OUTPUT / "where-we-serve" / "index.html").exists())
        self.assertTrue((stage.OUTPUT / "mmed-v6.js").exists())
        self.assertFalse((stage.OUTPUT / "CNAME").exists())
        self.assertFalse((stage.OUTPUT / "sitemap.xml").exists())
        self.assertFalse((stage.OUTPUT / "prototype").exists())
        self.assertFalse((stage.OUTPUT / "supabase").exists())
        self.assertFalse((stage.OUTPUT / "deployment").exists())
        self.assertFalse((stage.OUTPUT / "scripts").exists())
        self.assertIn("noindex", (stage.OUTPUT / "where-we-serve" / "index.html").read_text())
        self.assertIn("X-Robots-Tag: noindex", (stage.OUTPUT / "_headers").read_text())
        self.assertTrue((stage.OUTPUT / "_headers").read_text().startswith("/*\n"))


if __name__ == "__main__":
    unittest.main()

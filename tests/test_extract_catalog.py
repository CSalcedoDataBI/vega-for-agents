"""Tests for scripts/extract_catalog.py: the catalogues match the schemas on disk."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts import extract_catalog as ec  # noqa: E402


class TestExtract(unittest.TestCase):
    def setUp(self):
        self.catalogs = ec.build_all()

    def test_in_sync_with_schemas(self):
        """The committed catalogues are exactly what the extractor produces now."""
        self.assertEqual(ec.check_all(self.catalogs), [])

    def test_vega_lite_vocabularies(self):
        vl = self.catalogs["vega-lite"]
        self.assertIn("bar", vl["marks"])
        self.assertIn("boxplot", vl["marks"])          # composite mark
        self.assertNotIn("bubble", vl["marks"])         # invented
        self.assertIn("x", vl["channels"])
        self.assertIn("theta", vl["channels"])
        self.assertIn("filter", vl["transforms"])
        self.assertIn("pivot", vl["transforms"])
        self.assertIn("log", vl["scaleTypes"])
        self.assertIn("field", vl["properties"])

    def test_vega_vocabularies(self):
        v = self.catalogs["vega"]
        self.assertIn("symbol", v["marks"])             # from VL MarkType (documented)
        self.assertIn("force", v["transforms"])         # Vega-only transform
        self.assertIn("band", v["scaleTypes"])
        self.assertIn("signals", v["properties"])

    def test_meta_pins_the_schema(self):
        for lang, cat in self.catalogs.items():
            meta = cat["meta"]
            self.assertEqual(len(meta["schemaSha256"]), 64)
            self.assertEqual(meta["language"], lang)
            self.assertTrue(meta["schemaFile"].endswith(".schema.json"))


if __name__ == "__main__":
    unittest.main()

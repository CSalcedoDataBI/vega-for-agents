"""Tests for scripts/extract_catalog.py: the catalogues match the schemas on disk."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts import extract_catalog as ec  # noqa: E402
import vega_language as vl  # noqa: E402  (extract_catalog puts scripts/ on sys.path)
import vega_sources as vs  # noqa: E402


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
        # MarkType leak: Vega scenegraph marks are NOT valid Vega-Lite `"mark"` values.
        for scenegraph_only in ("symbol", "path", "group", "shape"):
            self.assertNotIn(scenegraph_only, vl["marks"])
        self.assertIn("x", vl["channels"])
        self.assertIn("theta", vl["channels"])
        self.assertIn("filter", vl["transforms"])
        self.assertIn("pivot", vl["transforms"])
        self.assertIn("log", vl["scaleTypes"])
        self.assertIn("mercator", vl["projectionTypes"])
        self.assertIn("field", vl["properties"])

    def test_vega_vocabularies(self):
        v = self.catalogs["vega"]
        self.assertIn("symbol", v["marks"])             # from VL MarkType (documented)
        self.assertIn("force", v["transforms"])         # Vega-only transform
        self.assertIn("band", v["scaleTypes"])
        self.assertIn("signals", v["properties"])

    def test_meta_pins_the_schema(self):
        for lang in ec.SCHEMAS:
            meta = self.catalogs[lang]["meta"]
            self.assertEqual(len(meta["schemaSha256"]), 64)
            self.assertEqual(meta["language"], lang)
            self.assertTrue(meta["schemaFile"].endswith(".schema.json"))

    def test_meta_pins_the_vega_source(self):
        for lang in ec.SOURCE_CATALOGS:
            meta = self.catalogs[lang]["meta"]
            self.assertEqual(meta["vegaVersion"], vs.VERSION)
            self.assertEqual(meta["commit"], vs.COMMIT)
            for path, sha in meta["files"].items():
                self.assertEqual(sha, vs.FILES[path])


class TestVegaSources(unittest.TestCase):
    def test_vendored_files_match_pins(self):
        self.assertEqual(vs.verify(), [])

    def test_edited_source_fails(self):
        path = vs.DIR / "packages/vega-expression/src/constants.js"
        original = path.read_bytes()
        try:
            path.write_bytes(original + b"\n// edited\n")
            self.assertTrue(any("constants.js" in e for e in vs.verify()))
            self.assertTrue(any("constants.js" in e for e in ec.check_all(ec.build_all())))
        finally:
            path.write_bytes(original)


class TestExpressions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cat = vl.expressions_catalog()
        cls.fn = {f["name"]: f for f in cls.cat["functions"]}

    def test_code_and_doc_agree(self):
        # Every documented name is registered in the code (the extractor raises otherwise).
        for f in self.cat["functions"]:
            if f["documented"]:
                self.assertTrue(f["signatures"], f["name"])

    def test_known_functions(self):
        self.assertEqual(self.fn["if"]["categories"], ["control-flow-functions"])
        self.assertEqual(self.fn["indexof"]["categories"], ["array-functions", "string-functions"])
        self.assertIn("rgb(specifier)", self.fn["rgb"]["signatures"])
        self.assertEqual(self.fn["luminance"]["since"], "5.7")
        self.assertIn("easeElasticInOut", self.fn)          # spread from functions/ease.js
        self.assertFalse(self.fn["vlSelectionTest"]["documented"])
        self.assertEqual(self.fn["_scale"]["kind"], "internal")
        self.assertNotIn("pbiFormat", self.fn)              # Deneb adds it; Vega does not have it
        self.assertNotIn("toUpperCase", self.fn)

    def test_constants_and_bound_variables(self):
        self.assertIn({"name": "PI", "value": "Math.PI"}, self.cat["constants"])
        self.assertEqual(self.cat["boundVariables"], ["datum", "event", "item"])

    def test_called_functions_ignores_strings_and_members(self):
        self.assertEqual(vl.called_functions("format(datum.x, ',.2f') + 'abs(1)'"), ["format"])
        self.assertEqual(vl.called_functions("event.preventDefault()"), [])
        self.assertEqual(vl.called_functions("test(/a(b)/, s)"), ["test"])


class TestEventSelector(unittest.TestCase):
    MARKS = None

    @classmethod
    def setUpClass(cls):
        cls.cat = vl.event_streams_catalog()
        cls.MARKS = cls.cat["markTypes"]

    def parse(self, s):
        return vl.parse_selector(s, mark_types=self.MARKS)

    def test_doc_examples(self):
        self.assertEqual(self.parse("symbol:mousedown!"),
                         [{"source": "view", "type": "mousedown", "marktype": "symbol",
                           "consume": True}])
        self.assertEqual(self.parse("mousemove{0, 200}"),
                         [{"source": "view", "type": "mousemove", "debounce": 200}])
        drag = self.parse("[rect:mousedown, window:mouseup] > window:mousemove")[0]
        self.assertEqual(drag["source"], "window")
        self.assertEqual(len(drag["between"]), 2)
        self.assertEqual(self.parse("@cell:click[event.shiftKey]")[0]["markname"], "cell")

    def test_errors(self):
        for bad in ("", "[a:click] > b:click", "click[", "click{x}", "click}"):
            with self.assertRaises(vl.SelectorError, msg=bad):
                self.parse(bad)

    def test_vocabulary(self):
        self.assertIn("rect", self.MARKS)
        self.assertIn("timer", [t["type"] for t in self.cat["specialEventTypes"]])
        self.assertIn("mousemove", self.cat["markEventTypes"])
        self.assertIn("container", self.cat["namedSources"])
        self.assertIn("throttle", [p["name"] for p in self.cat["objectProperties"]])


if __name__ == "__main__":
    unittest.main()

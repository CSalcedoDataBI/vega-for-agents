"""Tests for scripts/extract_catalog.py: the catalogues match the schemas on disk."""

import hashlib
import json
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
        for key, cfg in ec.SCHEMAS.items():
            meta = self.catalogs[key]["meta"]
            self.assertEqual(len(meta["schemaSha256"]), 64)
            self.assertEqual(meta["language"], cfg["language"])
            self.assertEqual(meta["schemaVersion"], cfg["version"])
            self.assertEqual(meta["package"], cfg["package"])
            self.assertTrue(meta["schemaFile"].endswith(".schema.json"))
            if "exactVersion" in cfg:
                self.assertEqual(meta["exactVersion"], cfg["exactVersion"])
            else:
                self.assertNotIn("exactVersion", meta)

    def test_v6_is_the_default_and_v5_is_kept(self):
        for key, cfg in ec.SCHEMAS.items():
            notes = " ".join(self.catalogs[key]["meta"]["notes"])
            self.assertIn("Deneb in Power BI", notes)
            self.assertIn("`$schema` v5", notes)
            self.assertIn("Vega" if cfg["language"] == "vega" else "Vega-Lite", notes)
            if cfg["version"] == "v6":
                self.assertIn("is the default. The v5 catalogue is kept", notes)
            else:
                self.assertIn("6 is the default. Check this catalogue", notes)

    def test_vega_lite_v6_vocabularies(self):
        v6 = self.catalogs["vega-lite-v6"]
        v5 = self.catalogs["vega-lite"]
        self.assertIn("week", v6["properties"])       # added in v6
        self.assertNotIn("week", v5["properties"])
        self.assertEqual(v6["marks"], v5["marks"])

    def test_vega_v6_vocabularies(self):
        v6 = self.catalogs["vega-v6"]
        v5 = self.catalogs["vega"]
        self.assertIn("inferUnits", v6["properties"])  # added in v6
        self.assertNotIn("inferUnits", v5["properties"])
        self.assertEqual(v6["transforms"], v5["transforms"])

    def test_diff_report_is_generated_from_the_catalogues(self):
        report = ec.diff_report(self.catalogs)
        self.assertIn("## Vega-Lite", report)
        self.assertIn("## Vega", report)
        self.assertIn("Added: `week`", report)
        self.assertIn("Added: `inferUnits`", report)
        self.assertEqual(ec.DIFF_REPORT.read_text(encoding="utf-8"), report)

    def test_diff_report_out_of_sync_fails(self):
        original = ec.DIFF_REPORT.read_bytes()
        try:
            ec.DIFF_REPORT.write_bytes(original + b"\nstale\n")
            errors = ec.check_all(self.catalogs)
            self.assertTrue(any("schema-diff-v5-v6.md" in e for e in errors), errors)
        finally:
            ec.DIFF_REPORT.write_bytes(original)

    def test_meta_pins_the_vega_source(self):
        for lang in ec.SOURCE_CATALOGS:
            meta = self.catalogs[lang]["meta"]
            self.assertEqual(meta["vegaVersion"], vs.VERSION)
            self.assertEqual(meta["commit"], vs.COMMIT)
            for path, sha in meta["files"].items():
                self.assertEqual(sha, vs.FILES[path])


class TestAdoptedTraps(unittest.TestCase):
    def setUp(self):
        self.catalogs = ec.build_all()
        self.traps = self.catalogs["adopted-traps"]["traps"]

    def test_every_issue_trap_has_a_stable_unique_id(self):
        self.assertEqual(len(self.traps), 11)
        ids = [trap["id"] for trap in self.traps]
        self.assertEqual(len(ids), len(set(ids)))
        for trap in self.traps:
            self.assertTrue(trap["id"])
            self.assertIn(trap["language"], ("vega", "vega-lite"))
            self.assertIn(trap["status"], ("adopted", "merged", "rejected"))
            for key in ("title", "symptom", "cause", "fix", "reason"):
                self.assertTrue(trap[key].strip(), f"{trap['id']}: empty {key}")

    def test_merged_traps_name_the_existing_note(self):
        merged = [trap for trap in self.traps if trap["status"] == "merged"]
        self.assertEqual(len(merged), 5)
        for trap in merged:
            self.assertTrue((ec.ROOT / trap["mergedInto"]).exists(), trap["mergedInto"])

    def test_adopted_traps_name_their_note(self):
        adopted = [trap for trap in self.traps if trap["status"] == "adopted"]
        self.assertEqual(len(adopted), 6)
        for trap in adopted:
            self.assertTrue((ec.ROOT / trap["card"]).exists(), trap["card"])

    def test_trap_catalogue_is_generated_and_in_the_manifest(self):
        self.assertEqual(ec.check_trap_catalog(self.catalogs["adopted-traps"]), [])
        files = {entry["path"]: entry for entry in ec.build_manifest(self.catalogs)["files"]}
        entry = files["exports/adopted-traps.catalog.json"]
        self.assertEqual(entry["kind"], "catalog")
        self.assertEqual(entry["contract"], ec.CONTRACT_VERSION)
        self.assertEqual(entry["version"], "v6")

    def test_missing_trap_catalogue_fails_check(self):
        catalogs = dict(self.catalogs)
        del catalogs["adopted-traps"]
        errors = ec.check_all(catalogs)
        self.assertTrue(any("adopted-traps.catalog.json" in e for e in errors), errors)


class TestContractAndManifest(unittest.TestCase):
    def setUp(self):
        self.catalogs = ec.build_all()

    def test_every_catalogue_has_the_contract(self):
        for key, catalog in self.catalogs.items():
            self.assertEqual(catalog["meta"]["contract"], ec.CONTRACT_VERSION, key)

    def test_manifest_lists_every_exports_file_with_its_real_sha256(self):
        manifest = ec.build_manifest(self.catalogs)
        listed = {entry["path"] for entry in manifest["files"]}
        actual = {path.relative_to(ec.ROOT).as_posix()
                  for path in ec.EXPORTS.iterdir()
                  if path.is_file() and path != ec.MANIFEST}
        self.assertEqual(listed, actual)
        for entry in manifest["files"]:
            path = ec.ROOT / entry["path"]
            self.assertEqual(entry["sha256"],
                             hashlib.sha256(path.read_bytes()).hexdigest(), entry["path"])

    def test_manifest_records_what_the_catalogue_meta_knows(self):
        files = {entry["path"]: entry for entry in ec.build_manifest(self.catalogs)["files"]}
        self.assertEqual(files["exports/vega-v6.catalog.json"]["source"],
                         {"package": "vega", "version": "6.4.0"})
        # The v5 catalogue has no pinned release, so its source has no version to invent.
        self.assertEqual(files["exports/vega-lite-v5.catalog.json"]["source"],
                         {"package": "vega-lite"})
        expressions = files["exports/vega-v6.expressions.catalog.json"]
        self.assertEqual(expressions["language"], "vega")
        self.assertEqual(expressions["version"], "v6")
        self.assertEqual(expressions["source"], {"version": vs.VERSION, "commit": vs.COMMIT})

    def test_manifest_is_deterministic(self):
        first = ec.build_manifest(self.catalogs)
        second = ec.build_manifest(ec.build_all())
        self.assertEqual(ec.manifest_text(first), ec.manifest_text(second))
        self.assertTrue(ec.manifest_text(first).endswith("\n"))
        self.assertEqual(json.loads(ec.manifest_text(first)), first)

    def test_committed_manifest_is_in_sync(self):
        self.assertEqual(ec.check_all(self.catalogs), [])

    def test_missing_manifest_fails_check(self):
        original = ec.MANIFEST.read_bytes()
        try:
            ec.MANIFEST.unlink()
            errors = ec.check_all(self.catalogs)
            self.assertTrue(any("manifest missing" in error for error in errors), errors)
        finally:
            ec.MANIFEST.write_bytes(original)

    def test_edited_catalogue_byte_fails_check(self):
        path = ec.catalog_path("vega-v6")
        original = path.read_bytes()
        try:
            path.write_bytes(original + b" ")
            errors = ec.check_all(self.catalogs)
            self.assertTrue(any(path.name in error for error in errors), errors)
        finally:
            path.write_bytes(original)

    def test_catalogue_without_contract_fails_check(self):
        path = ec.catalog_path("vega-v6")
        original = path.read_bytes()
        try:
            data = json.loads(original)
            del data["meta"]["contract"]
            path.write_bytes(ec.catalog_text(data).encode("utf-8"))
            errors = ec.check_all(self.catalogs)
            self.assertTrue(any("meta.contract" in error for error in errors), errors)
        finally:
            path.write_bytes(original)


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

"""Tests for scripts/check_repo.py: valid specs pass, invented names fail."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts import check_repo as cr  # noqa: E402


class TestNameCheck(unittest.TestCase):
    def setUp(self):
        self.cats = cr.load_catalogs()
        self.assertIn("vega-lite", self.cats)
        self.assertIn("vega", self.cats)

    def v(self, spec, lang):
        return cr.validate_spec(spec, lang, self.cats[lang], "T")

    # --- valid specs produce no error (no false positives) ---

    def test_valid_vega_lite(self):
        spec = {
            "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
            "data": {"values": [{"a": "A", "b": 28, "my field": 3}]},
            "transform": [{"filter": "datum.b > 5"}, {"calculate": "datum.b*2", "as": "c"}],
            "mark": {"type": "bar", "tooltip": True},
            "encoding": {
                "x": {"field": "a", "type": "nominal", "axis": {"labelAngle": 0}},
                "y": {"field": "b", "type": "quantitative", "scale": {"type": "log"}},
                "tooltip": [{"field": "a", "title": "Cat"}, {"field": "b", "title": "Val"}],
            },
        }
        self.assertEqual(self.v(spec, "vega-lite"), [])

    def test_valid_vega(self):
        spec = {
            "$schema": "https://vega.github.io/schema/vega/v5.json",
            "width": 400, "height": 200,
            "signals": [{"name": "hover", "value": None}],
            "data": [{"name": "table", "values": [{"x": 1, "y": 2}]}],
            "scales": [{"name": "xs", "type": "linear",
                        "domain": {"data": "table", "field": "x"}, "range": "width"}],
            "marks": [{"type": "symbol", "from": {"data": "table"},
                       "encode": {"enter": {"x": {"scale": "xs", "field": "x"},
                                            "fill": {"value": "steelblue"}}}}],
        }
        self.assertEqual(self.v(spec, "vega"), [])

    def test_free_key_containers(self):
        spec = {"datasets": {"mine": [{"weird key": 1}]},
                "config": {"style": {"myStyle": {"fill": "red"}}},
                "mark": "bar", "encoding": {"x": {"field": "a", "type": "nominal"}}}
        self.assertEqual(self.v(spec, "vega-lite"), [])

    # --- invented names fail ---

    def test_invented_mark(self):
        self.assertTrue(any("mark 'bubble'" in e for e in self.v({"mark": "bubble"}, "vega-lite")))

    def test_invented_channel(self):
        errs = self.v({"mark": "point", "encoding": {"radius3": {"field": "a"}}}, "vega-lite")
        self.assertTrue(any("channel 'radius3'" in e for e in errs))

    def test_invented_transform(self):
        errs = self.v({"mark": "bar", "transform": [{"piveot": "x"}]}, "vega-lite")
        self.assertTrue(any("no known transform keyword" in e for e in errs))

    def test_invented_scale_type(self):
        errs = self.v({"mark": "bar",
                       "encoding": {"y": {"field": "b", "scale": {"type": "lne"}}}}, "vega-lite")
        self.assertTrue(any("scale type 'lne'" in e for e in errs))

    def test_invented_property(self):
        self.assertTrue(any("property 'wobble'" in e for e in self.v({"wobble": 1}, "vega-lite")))

    def test_valid_projection(self):
        spec = {"mark": "geoshape", "projection": {"type": "mercator"}}
        self.assertEqual(self.v(spec, "vega-lite"), [])

    def test_invented_projection(self):
        errs = self.v({"mark": "geoshape", "projection": {"type": "flatearth"}}, "vega-lite")
        self.assertTrue(any("projection type 'flatearth'" in e for e in errs))

    def test_scenegraph_mark_rejected_in_vega_lite(self):
        # `symbol` is a valid Vega mark but not a valid Vega-Lite `"mark"` value.
        self.assertTrue(any("mark 'symbol'" in e for e in self.v({"mark": "symbol"}, "vega-lite")))
        self.assertEqual(self.v({"marks": [{"type": "symbol"}]}, "vega"), [])

    def test_invented_vega_mark_and_transform(self):
        errs = self.v({"marks": [{"type": "blob"}], "transform": [{"type": "frobnicate"}]}, "vega")
        self.assertTrue(any("mark 'blob'" in e for e in errs))
        self.assertTrue(any("transform 'frobnicate'" in e for e in errs))


class TestRepoShape(unittest.TestCase):
    def test_catalogs_present(self):
        self.assertTrue((cr.ROOT / "exports" / "vega-lite-v5.catalog.json").exists())
        self.assertTrue((cr.ROOT / "exports" / "vega-v5.catalog.json").exists())

    def test_full_repo_check_passes(self):
        """The repository as committed passes every check."""
        self.assertEqual(cr.check_skills() + cr.check_workflows() + cr.check_names(), [])


if __name__ == "__main__":
    unittest.main()

"""Extract the catalogue of valid names from the official Vega / Vega-Lite JSON Schemas.

The schemas under exports/ are the source of truth. This script reads them and writes, for each
language, exports/<name>.catalog.json: the closed vocabularies an agent must not invent (marks,
encoding channels, transforms, scale types) and the full set of structural property names. The
exact schema is pinned by SHA-256 in each catalogue's `meta`.

    python scripts/extract_catalog.py            # (re)write the catalogues
    python scripts/extract_catalog.py --check     # fail if a catalogue is out of sync with its schema

Standard library only, so CI needs no install step.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXPORTS = ROOT / "exports"

SCHEMAS = {
    "vega-lite": {
        "schema": "vega-lite-v5.schema.json",
        "catalog": "vega-lite-v5.catalog.json",
        "version": "v5",
        "source": "https://vega.github.io/schema/vega-lite/v5.json",
    },
    "vega": {
        "schema": "vega-v5.schema.json",
        "catalog": "vega-v5.catalog.json",
        "version": "v5",
        "source": "https://vega.github.io/schema/vega/v5.json",
    },
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def all_property_names(schema: dict) -> set[str]:
    """Every key that appears inside a JSON-Schema `properties` object, anywhere in the tree."""
    names: set[str] = set()

    def walk(node) -> None:
        if isinstance(node, dict):
            props = node.get("properties")
            if isinstance(props, dict):
                names.update(props.keys())
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(schema)
    return names


def extract_vega_lite(schema: dict) -> dict:
    defs = schema["definitions"]
    # Marks: the values allowed for `"mark"` are the `Mark` enum plus the three composite marks.
    # NOT MarkType: that enum is the Vega scenegraph mark set (symbol, path, group, shape, used in
    # selection/event filters), which the Vega-Lite compiler rejects as a `"mark"` value.
    marks = set(defs["Mark"]["enum"])
    for name in ("BoxPlot", "ErrorBar", "ErrorBand"):
        const = defs.get(name, {}).get("const")
        if const:
            marks.add(const)
    # Channels: the properties of the faceted encoding object.
    channels = set(defs["FacetedEncoding"]["properties"].keys())
    # Transforms: the discriminator key of each variant of the Transform union.
    transforms = set()
    for variant in defs["Transform"].get("anyOf", []):
        ref = variant.get("$ref", "").split("/")[-1]
        required = defs.get(ref, {}).get("required", [])
        if required:
            transforms.add(required[0])
    scale_types = set(defs["ScaleType"]["enum"])
    projection_types = set(defs["ProjectionType"]["enum"])
    return {
        "marks": sorted(marks),
        "channels": sorted(channels),
        "transforms": sorted(transforms),
        "scaleTypes": sorted(scale_types),
        "projectionTypes": sorted(projection_types),
        "properties": sorted(all_property_names(schema)),
    }


def _enum_of_type(node) -> list[str]:
    """Collect every enum found on a `type` property anywhere under `node` (for scale types)."""
    out: list[str] = []

    def walk(n) -> None:
        if isinstance(n, dict):
            t = n.get("type")
            if isinstance(t, dict) and t.get("enum"):
                out.extend(t["enum"])
            for v in n.values():
                walk(v)
        elif isinstance(n, list):
            for x in n:
                walk(x)

    walk(node)
    return out


def extract_vega(schema: dict, vega_lite_marks: list[str]) -> dict:
    defs = schema["definitions"]
    # Transforms: the `type` const of every *Transform definition.
    transforms = set()
    for name, node in defs.items():
        if name.endswith("Transform"):
            t = node.get("properties", {}).get("type", {})
            if t.get("const"):
                transforms.add(t["const"])
            transforms.update(t.get("enum", []))
    scale_types = set(_enum_of_type(defs["scale"]))
    return {
        # The Vega schema leaves `marktype` as a free string; the primitive mark set is the same
        # as Vega-Lite's MarkType enum (both from the official Vega project). See meta.notes.
        "marks": sorted(set(vega_lite_marks)),
        "transforms": sorted(transforms),
        "scaleTypes": sorted(scale_types),
        "properties": sorted(all_property_names(schema)),
    }


def build_catalog(language: str, vega_lite_marktypes: list[str] | None = None) -> dict:
    cfg = SCHEMAS[language]
    schema_path = EXPORTS / cfg["schema"]
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    meta = {
        "language": language,
        "schemaVersion": cfg["version"],
        "schemaFile": cfg["schema"],
        "schemaSha256": sha256(schema_path),
        "schemaDraft": schema.get("$schema"),
        "definitions": len(schema.get("definitions", {})),
        "source": cfg["source"],
        "generatedBy": "scripts/extract_catalog.py",
    }
    if language == "vega-lite":
        body = extract_vega_lite(schema)
    else:
        body = extract_vega(schema, vega_lite_marktypes or [])
        meta["notes"] = [
            "The Vega schema leaves `marktype` as a free string (no enum); `marks` is taken from "
            "the Vega-Lite MarkType enum, the same primitive mark set of the official Vega project.",
            "Signals are user-named and have no closed vocabulary, so they are not catalogued; "
            "signal-related property names are in `properties`.",
            "Projection `type` in Vega is a stringOrSignal (free), so there is no projectionTypes "
            "vocabulary here; Vega-Lite does enumerate ProjectionType.",
        ]
    return {"meta": meta, **body}


def marktypes_from_vega_lite() -> list[str]:
    schema = json.loads((EXPORTS / SCHEMAS["vega-lite"]["schema"]).read_text(encoding="utf-8"))
    return schema["definitions"]["MarkType"]["enum"]


def build_all() -> dict[str, dict]:
    marktypes = marktypes_from_vega_lite()
    return {
        "vega-lite": build_catalog("vega-lite"),
        "vega": build_catalog("vega", marktypes),
    }


def write_all(catalogs: dict[str, dict]) -> None:
    for language, catalog in catalogs.items():
        path = EXPORTS / SCHEMAS[language]["catalog"]
        path.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def check_all(catalogs: dict[str, dict]) -> list[str]:
    errors = []
    for language, catalog in catalogs.items():
        path = EXPORTS / SCHEMAS[language]["catalog"]
        if not path.exists():
            errors.append(f"{path.name}: catalogue missing; run scripts/extract_catalog.py")
            continue
        on_disk = json.loads(path.read_text(encoding="utf-8"))
        if on_disk != catalog:
            errors.append(
                f"{path.name}: out of sync with {SCHEMAS[language]['schema']}; "
                f"run scripts/extract_catalog.py"
            )
    return errors


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Extract Vega / Vega-Lite name catalogues from schemas.")
    ap.add_argument("--check", action="store_true",
                    help="fail if a catalogue on disk differs from the schema, instead of writing")
    args = ap.parse_args(argv)
    catalogs = build_all()
    if args.check:
        errors = check_all(catalogs)
        for error in errors:
            print(f"FAIL {error}")
        if not errors:
            print("OK catalogues in sync with schemas")
        return 1 if errors else 0
    write_all(catalogs)
    for language, catalog in catalogs.items():
        counts = {k: len(v) for k, v in catalog.items() if isinstance(v, list)}
        print(f"wrote {SCHEMAS[language]['catalog']}: {counts}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

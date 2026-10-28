"""Extract the catalogue of valid names from the official Vega / Vega-Lite sources.

The schemas under exports/ are the source of truth for spec structure. This script reads them and
writes, for each language, exports/<name>.catalog.json: the closed vocabularies an agent must not
invent (marks, encoding channels, transforms, scale types) and the full set of structural property
names. The exact schema is pinned by SHA-256 in each catalogue's `meta`.

The expression language and the event-stream grammar are in no schema (both are free strings
there), so they come from the Vega 6 source files pinned in scripts/vega_sources.py:
exports/vega-v6.expressions.catalog.json, exports/vega-v6.event-streams.catalog.json, and the
reference cards under reference/vega/, rendered from those two catalogues.

    python scripts/extract_catalog.py            # (re)write the catalogues and the cards
    python scripts/extract_catalog.py --check     # fail if anything is out of sync with its source

Standard library only, so CI needs no install step.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import vega_cards  # noqa: E402
import vega_language  # noqa: E402
import vega_sources  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
EXPORTS = ROOT / "exports"
CARDS = ROOT / "reference" / "vega"

# Catalogues extracted from the pinned Vega source instead of a schema.
SOURCE_CATALOGS = {
    "vega-expressions": "vega-v6.expressions.catalog.json",
    "vega-event-streams": "vega-v6.event-streams.catalog.json",
}

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
        "vega-expressions": vega_language.expressions_catalog(),
        "vega-event-streams": vega_language.event_streams_catalog(),
    }


def catalog_path(language: str) -> Path:
    if language in SOURCE_CATALOGS:
        return EXPORTS / SOURCE_CATALOGS[language]
    return EXPORTS / SCHEMAS[language]["catalog"]


def build_cards(catalogs: dict[str, dict]) -> dict[str, str]:
    """The reference cards (repo-relative path -> text), rendered from the catalogues only."""
    return {**vega_cards.expression_cards(catalogs["vega-expressions"]),
            **vega_cards.event_stream_card(catalogs["vega-event-streams"])}


def write_all(catalogs: dict[str, dict]) -> None:
    for language, catalog in catalogs.items():
        text = json.dumps(catalog, indent=2, ensure_ascii=False) + "\n"
        catalog_path(language).write_bytes(text.encode("utf-8"))
    cards = build_cards(catalogs)
    for stale in CARDS.glob("**/*.md"):
        if stale.relative_to(ROOT).as_posix() not in cards:
            stale.unlink()
    for rel, text in cards.items():
        path = ROOT / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode("utf-8"))


def check_all(catalogs: dict[str, dict]) -> list[str]:
    errors = list(vega_sources.verify())
    for language, catalog in catalogs.items():
        path = catalog_path(language)
        source = (SCHEMAS[language]["schema"] if language in SCHEMAS
                  else f"the pinned Vega {vega_sources.VERSION} source")
        if not path.exists():
            errors.append(f"{path.name}: catalogue missing; run scripts/extract_catalog.py")
            continue
        on_disk = json.loads(path.read_text(encoding="utf-8"))
        if on_disk != catalog:
            errors.append(f"{path.name}: out of sync with {source}; run scripts/extract_catalog.py")
    cards = build_cards(catalogs)
    for rel, text in cards.items():
        path = ROOT / rel
        if not path.exists():
            errors.append(f"{rel}: card missing; run scripts/extract_catalog.py")
        elif path.read_bytes().decode("utf-8").replace("\r\n", "\n") != text:
            errors.append(f"{rel}: card out of sync with its catalogue; run "
                          f"scripts/extract_catalog.py (cards are never edited by hand)")
    for extra in sorted(CARDS.glob("**/*.md")):
        rel = extra.relative_to(ROOT).as_posix()
        if rel not in cards:
            errors.append(f"{rel}: not generated from any catalogue; remove it")
    return errors


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Extract Vega / Vega-Lite name catalogues.")
    ap.add_argument("--check", action="store_true",
                    help="fail if a catalogue or card on disk differs from its source, "
                         "instead of writing")
    args = ap.parse_args(argv)
    catalogs = build_all()
    if args.check:
        errors = check_all(catalogs)
        for error in errors:
            print(f"FAIL {error}")
        if not errors:
            print("OK catalogues and cards in sync with their sources")
        return 1 if errors else 0
    pins = vega_sources.verify()
    if pins:
        for error in pins:
            print(f"FAIL {error}")
        return 1
    write_all(catalogs)
    for language, catalog in catalogs.items():
        counts = {k: len(v) for k, v in catalog.items() if isinstance(v, list)}
        print(f"wrote {catalog_path(language).name}: {counts}")
    print(f"wrote {len(build_cards(catalogs))} cards under reference/vega/")
    return 0


if __name__ == "__main__":
    sys.exit(main())

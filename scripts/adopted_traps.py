"""The adopted Vega / Vega-Lite authoring traps (issue #20).

Traps are authored reference content: they describe a symptom, a cause and a fix, not a closed
vocabulary, so they cannot be extracted from a JSON Schema. This module is their single source.
`scripts/extract_catalog.py` writes `exports/adopted-traps.catalog.json` from it, so the exported
file is generated and is never edited by hand.

Each trap has a stable `id`, independent of its wording. Never rename an id when the note changes;
downstream tools use it to drop their own copy of the trap.

`status` records the deduplication against the existing draft notes under `reference/drafts/`:

- `adopted`: no existing note covered it, so a new note was added;
- `merged`: an existing note covered it, so the issue's symptom/cause/fix were merged into that note;
- `rejected`: it was not added, and `reason` says why.

Every entry keeps its `reason` even when adopted or merged, so the decision is readable from the
catalogue alone.
"""

from __future__ import annotations

MEASURED_WITH = {"vega": "6.4.0", "vega-lite": "6.4.3"}
SOURCE = "https://github.com/CSalcedoDataBI/vega-for-agents/issues/20"

TRAPS = [
    {
        "id": "vl-wrong-encoding-type",
        "language": "vega-lite",
        "title": "Wrong encoding type for the data",
        "symptom": "A wrong scale, odd aggregations, or an arbitrary order.",
        "cause": "`type` does not match the data: `nominal` on dates or `quantitative` on text.",
        "fix": "Pick `type` from the data: `temporal` for dates, `ordinal` when order matters, "
               "`nominal` for categories and `quantitative` for measures.",
        "status": "adopted",
        "reason": "No existing draft note covers encoding type values; added as a new note.",
        "card": "reference/drafts/encoding-type.md",
    },
    {
        "id": "vl-field-name-escaping",
        "language": "vega-lite",
        "title": "Field names with spaces or dots",
        "symptom": "A parse error, or the field is read as a nested path.",
        "cause": "`datum.field name` and `datum.a.b` are parsed as property accesses, not as one "
                 "field name.",
        "fix": "Use `datum['field name']` in an expression; in `field:` escape a dot as "
               "`\"a\\\\.b\"`.",
        "status": "merged",
        "reason": "The existing field-name note covered the escaping rule; the issue's symptom, "
                  "cause and fix were merged into it.",
        "mergedInto": "reference/drafts/field-names.md",
    },
    {
        "id": "vl-tooltip-array",
        "language": "vega-lite",
        "title": "Tooltip as an object",
        "symptom": "Only one field shows in the tooltip.",
        "cause": "`tooltip: { field, title }` is one field definition; it does not become a list.",
        "fix": "Use an array: `tooltip: [{ field: \"x\" }, { field: \"y\" }]`.",
        "status": "merged",
        "reason": "The existing tooltip note covered the array form; the issue's symptom and "
                  "cause were merged into it.",
        "mergedInto": "reference/drafts/tooltip-array.md",
    },
    {
        "id": "vl-transform-placement",
        "language": "vega-lite",
        "title": "Transform in the wrong place",
        "symptom": "A filter or aggregate is ignored.",
        "cause": "`transform` is nested in `encoding`, or in a layer that does not own the data.",
        "fix": "Put `transform` at the same level as `mark` and `encoding` of the view that owns "
               "the data.",
        "status": "merged",
        "reason": "The existing filter-transform note covered view-level and ordered transforms; "
                  "the issue's layer case was merged into it.",
        "mergedInto": "reference/drafts/filter-transform.md",
    },
    {
        "id": "vl-layer-encoding",
        "language": "vega-lite",
        "title": "Layer without its own encoding",
        "symptom": "A layer does not draw, or it takes the wrong channels.",
        "cause": "The layer expects channels from a sibling layer instead of inheriting them from "
                 "the parent.",
        "fix": "Put shared channels in the parent `encoding`; put every other channel in each "
               "layer's own `encoding`.",
        "status": "merged",
        "reason": "The existing layers note covered marks and per-layer encoding; the issue's "
                  "sibling-channel case was merged into it.",
        "mergedInto": "reference/drafts/layers.md",
    },
    {
        "id": "vega-signal-declaration-order",
        "language": "vega",
        "title": "Signal referenced before it is declared",
        "symptom": "`Unknown signal name`.",
        "cause": "An expression earlier in the spec reads a signal that is declared later.",
        "fix": "Declare signals before the marks and data that read them.",
        "status": "merged",
        "reason": "The existing signals note covered signal declaration; its ordering case was "
                  "expanded with the issue's text.",
        "mergedInto": "reference/drafts/signals.md",
    },
    {
        "id": "vega-data-forward-reference",
        "language": "vega",
        "title": "`data('x')` reads a dataset declared later",
        "symptom": "The spec compiles with no error and renders blank.",
        "cause": "`data('x')` compiles even when `x` is further down in `data[]` (or is the "
                 "dataset itself), but returns `null` while the reading dataset is computed; the "
                 "`formula` throws and the dataset stays empty. Forward `source`, `lookup.from` "
                 "and `indata()` do fail at compile time, so only this one is silent.",
        "fix": "Declare the dataset being read before the dataset that reads it.",
        "status": "adopted",
        "reason": "No existing draft note covers the silent forward reference; added as a new "
                  "note.",
        "card": "reference/drafts/data-forward-reference.md",
    },
    {
        "id": "vega-random-in-transform",
        "language": "vega",
        "title": "`random()` in a transform moves the scene on every re-render",
        "symptom": "Generated points jump on resize or on any re-run.",
        "cause": "Transforms re-evaluate on every dataflow run and `random()` has no seed.",
        "fix": "Derive positions from an index (`sequence` transform, `as: \"i\"`) with a "
               "deterministic function.",
        "status": "adopted",
        "reason": "No existing draft note covers unseeded randomness in a transform; added as a "
                  "new note.",
        "card": "reference/drafts/random-transform.md",
    },
    {
        "id": "vega-index-lcg",
        "language": "vega",
        "title": "An \"LCG\" evaluated over the index draws diagonals",
        "symptom": "A pseudo-random point field shows regular stripes.",
        "cause": "`((i * a + b) % m) / m` over consecutive `i` is an arithmetic progression modulo "
                 "`m`, not an iterated generator, so the points fall on a few lines.",
        "fix": "Use a sine hash: `abs(sin(datum.i * 12.9898 + 1.0) * 43758.5453) % 1`.",
        "status": "adopted",
        "reason": "No existing draft note covers the index-LCG artefact; added as a new note.",
        "card": "reference/drafts/index-lcg.md",
    },
    {
        "id": "vega-layout-bounds-flush",
        "language": "vega",
        "title": "`bounds: \"flush\"` drops marks drawn at negative offsets from the cell size",
        "symptom": "With `\"full\"` a mark at negative `y` counts toward the row height; with "
                   "`\"flush\"` it is excluded and overlaps the previous row. Telltale sign: only "
                   "the first row's header is fully visible.",
        "cause": "The `flush` bounds ignore the part of a mark that extends past the cell's top "
                 "or left edge.",
        "fix": "Use `layout.bounds: \"full\"` when a mark draws at a negative offset from the "
               "cell, or move the mark inside the cell.",
        "status": "adopted",
        "reason": "No existing draft note covers layout bounds in groups; added as a new note.",
        "card": "reference/drafts/layout-bounds-flush.md",
    },
    {
        "id": "vega-layout-header-offset",
        "language": "vega",
        "title": "`bounds` and `offset` do not move a group with a header role",
        "symptom": "Switching `bounds` changes nothing, and `offset.rowHeader` moves the group "
                   "horizontally, never vertically.",
        "cause": "A group with `role: \"row-header\"` (or another header role) is placed by the "
                 "header logic, not by the grid bounds or the row-header offset.",
        "fix": "Use `layout.padding.row` to create the space between rows; the header's own "
               "negative `y` decides where it sits inside that space. They are two independent "
               "controls.",
        "status": "adopted",
        "reason": "No existing draft note covers header roles in a layout; added as a new note.",
        "card": "reference/drafts/layout-header-offset.md",
    },
]


def traps_catalog() -> dict:
    """The generated catalogue, before `meta.contract` is prepended by the extractor."""
    return {
        "meta": {
            "kind": "traps",
            "language": "vega-vega-lite",
            "schemaVersion": "v6",
            "measuredWith": dict(MEASURED_WITH),
            "source": SOURCE,
            "generatedBy": "scripts/extract_catalog.py",
            "notes": [
                "One entry per trap, with a stable `id`; ids never change when wording changes.",
                "`status` is the deduplication result: adopted, merged or rejected, always with a "
                "`reason`.",
                "This catalogue is authored reference content, not a name vocabulary; the schema "
                "and expression catalogues remain the source of truth for every name.",
            ],
        },
        "traps": [dict(trap) for trap in TRAPS],
    }

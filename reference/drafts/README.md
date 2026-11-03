# Draft trap notes and validated examples

> **Drafts.** A model drafted these notes; the maintainer promotes them to reference cards later.
> Every `vega` / `vega-lite` block in these drafts is checked by `scripts/check_repo.py` against the
> v6 catalogues, but the wording has not been reviewed yet.

The stable ids below are the ones in [`exports/adopted-traps.catalog.json`](../../exports/adopted-traps.catalog.json),
which is generated from `scripts/adopted_traps.py`.

| Trap ID | Pitfall | Language |
|---|---|---|
| `vl-wrong-encoding-type` | [Wrong encoding type for the data](encoding-type.md) | Vega-Lite |
| `vl-field-name-escaping` | [Field names with spaces or dots](field-names.md) | Vega-Lite |
| `vl-tooltip-array` | [Tooltips as an array of field definitions](tooltip-array.md) | Vega-Lite |
| `vl-transform-placement` | [Transforms at the view level, in order](filter-transform.md) | Vega-Lite |
| `vl-layer-encoding` | [Layers carry their own mark and, when needed, encoding](layers.md) | Vega-Lite |
| `vega-signal-declaration-order` | [A Vega signal must be declared in scope](signals.md) | Vega |
| `vega-data-forward-reference` | [`data('x')` reads a dataset declared later](data-forward-reference.md) | Vega |
| `vega-random-in-transform` | [`random()` in a transform moves the scene on every re-render](random-transform.md) | Vega |
| `vega-index-lcg` | [An "LCG" evaluated over the index draws diagonals](index-lcg.md) | Vega |
| `vega-layout-bounds-flush` | [`bounds: "flush"` drops marks drawn at negative offsets](layout-bounds-flush.md) | Vega |
| `vega-layout-header-offset` | [`bounds` and `offset` do not move a header group](layout-header-offset.md) | Vega |
| — | [`width: "container"` needs a sized container](width-container.md) | Vega-Lite |

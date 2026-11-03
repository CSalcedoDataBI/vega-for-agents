# Transforms at the view level, in order

> Draft. Vega-Lite v6. Trap ID: `vl-transform-placement`.

**Symptom:** a filter or aggregate is ignored.

**The trap:** a transform belongs in the view-level `transform` array next to `mark`, not inside
`encoding`, and transforms run in the order they are listed. A layer that does not own the data
does not get a transform either.

**Why it happens:** `encoding` maps fields to visual channels; it does not change the data. A
`filter` inside `encoding` is not a channel; Vega-Lite drops it with a warning and does not filter
the data. A transform nested in a layer that does not own the data is ignored for the same reason.
Order matters too: a filter that uses a calculated field must come after the `calculate` that
creates it.

**Wrong form:** `"encoding": {"filter": ...}` instead of a top-level `transform` — Vega-Lite drops
the filter with a warning and does not filter the data — a `transform` nested in `encoding`, or a
transform in a layer that does not own the data.

**Fix:** put `transform` at the same level as `mark` and `encoding` of the view that owns the data,
in execution order.

```vega-lite
{
  "$schema": "https://vega.github.io/schema/vega-lite/v6.json",
  "data": {
    "values": [
      {"category": "A", "amount": 4},
      {"category": "B", "amount": 9},
      {"category": "C", "amount": 2}
    ]
  },
  "transform": [
    {"calculate": "datum.amount * 2", "as": "double"},
    {"filter": "datum.double > 10"}
  ],
  "mark": "bar",
  "encoding": {
    "x": {"field": "category", "type": "nominal"},
    "y": {"field": "double", "type": "quantitative"}
  }
}
```

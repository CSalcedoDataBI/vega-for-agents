# Transforms at the view level, in order

> Draft. Vega-Lite v6. Trap ID: `vl-transform-placement`.

**Symptom:** a filter or aggregate is ignored.

**The trap:** a transform belongs in the view-level `transform` array next to `mark`, not inside
`encoding`, and transforms run in the order they are listed. A transform inside one layer is not
shared with its siblings.

**Why it happens:** `encoding` maps fields to visual channels; it does not change the data. A
`filter` inside `encoding` is not a channel; Vega-Lite drops it with a warning and does not filter
the data. A transform written inside one layer applies to that layer only, so the sibling layers
do not see its result. Order matters too: a filter that uses a calculated field must come after
the `calculate` that creates it.

**Wrong form:** `"encoding": {"filter": ...}` instead of a top-level `transform` — Vega-Lite drops
the filter with a warning and does not filter the data — or a `transform` in one layer that the
other layers are expected to see.

**Fix:** put `transform` at the same level as `mark` and `encoding`, in execution order; put it in
the parent view, not in one layer, when every layer needs its result.

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

# Filter transforms at the view level, in order

> Draft. Vega-Lite v6.

**The trap:** a filter belongs in the view-level `transform` array next to `mark`, not inside
`encoding`, and transforms run in the order they are listed.

**Why it happens:** `encoding` maps fields to visual channels; it does not change the data. A
`filter` written under `encoding` is read as an encoding channel and is not a transform. Order
matters too: a filter that uses a calculated field must come after the `calculate` that creates it.

**Wrong form:** `"encoding": {"filter": ...}` instead of a top-level `transform`, or the filter
placed before the `calculate` whose output it tests.

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

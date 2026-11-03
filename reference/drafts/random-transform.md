# `random()` in a transform moves the scene on every re-render

> Draft. Vega v6. Trap ID: `vega-random-in-transform`.

**Symptom:** generated points jump on resize or on any re-run.

**Cause:** a transform re-evaluates whenever something it reads changes: a signal, a field or its
input data, such as `width` after a resize. `random()` has no seed, so every re-evaluation draws new
values and the scene moves even though the spec did not change.

**Wrong form:** a `formula` or other transform that sets a position with `random()`.

**Fix:** derive positions from an index (`sequence` transform, `as: "i"`) with a deterministic
function.

```vega
{
  "$schema": "https://vega.github.io/schema/vega/v6.json",
  "width": 300,
  "height": 100,
  "data": [
    {
      "name": "points",
      "transform": [
        {"type": "sequence", "start": 0, "stop": 20, "step": 1, "as": "i"}
      ]
    }
  ],
  "marks": [
    {
      "type": "symbol",
      "from": {"data": "points"},
      "encode": {
        "update": {
          "x": {"signal": "datum.i * 15"},
          "y": {"signal": "abs(sin(datum.i * 12.9898 + 1.0) * 43758.5453) % 1 * 100"},
          "size": {"value": 30}
        }
      }
    }
  ]
}
```

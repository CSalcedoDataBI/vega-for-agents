# `data('x')` reads a dataset declared later

> Draft. Vega v6. Trap ID: `vega-data-forward-reference`.

**Symptom:** the spec compiles with no error and renders blank.

**Cause:** `data('x')` compiles even when `x` is further down in `data[]` (or is the dataset
itself), but returns `null` while the reading dataset is computed. The `formula` throws and the
dataset stays empty. Forward `source`, `lookup.from` and `indata()` do fail at compile time, so only
this one is silent.

**Wrong form:** a `formula` that calls `data('later')` while `later` is declared after the dataset
that contains the formula.

**Fix:** declare the dataset being read before the dataset that reads it.

```vega
{
  "$schema": "https://vega.github.io/schema/vega/v6.json",
  "width": 200,
  "height": 100,
  "data": [
    {"name": "source", "values": [{"a": 1}, {"a": 2}]},
    {
      "name": "derived",
      "source": "source",
      "transform": [
        {"type": "formula", "expr": "data('source')[0].a + datum.a", "as": "b"}
      ]
    }
  ],
  "marks": [
    {
      "type": "symbol",
      "from": {"data": "derived"},
      "encode": {"enter": {"x": {"value": 20}, "y": {"value": 20}}}
    }
  ]
}
```

# Layers carry their own mark and, when needed, encoding

> Draft. Vega-Lite v6.

**The trap:** every entry in `layer` is a unit spec with its own `mark`; a layer adds its own
`encoding` only when its channels differ from the shared encoding at the top level.

**Why it happens:** a layered view overlays unit specs. The top-level `encoding` is shared and
inherited by every layer, so repeating it in each layer is noise. A layer that needs a different
field or channel declares only that channel in its own `encoding`; the rest is inherited.

**Wrong form:** a `layer` entry with an `encoding` but no `mark`, or a top-level `mark` beside
`layer` when each layer is supposed to supply its own mark.

```vega-lite
{
  "$schema": "https://vega.github.io/schema/vega-lite/v6.json",
  "data": {
    "values": [
      {"date": "2024-01-01", "value": 4, "target": 5},
      {"date": "2024-01-02", "value": 7, "target": 6},
      {"date": "2024-01-03", "value": 5, "target": 8}
    ]
  },
  "encoding": {
    "x": {"field": "date", "type": "temporal"}
  },
  "layer": [
    {"mark": "line", "encoding": {"y": {"field": "value", "type": "quantitative"}}},
    {"mark": "point", "encoding": {"y": {"field": "target", "type": "quantitative"}}}
  ]
}
```

# A Vega signal must be declared in scope

> Draft. Vega v6. Trap ID: `vega-signal-declaration-order`.

**Symptom:** `Unrecognized signal name: "hovered"`, and the spec does not render.

**The trap:** a signal that an expression, mark channel or data transform reads must be declared in
a `signals` entry of the top level or of an enclosing group. Declaration order does not matter:
Vega 6.4.0 resolves a signal declared after the expression that reads it. Only a name that is never
declared fails.

**Why it happens:** a Vega expression has no implicit globals. `{"signal": "barColor"}` reads a
signal called `barColor`, and the dataflow only knows that name once a `signals` entry declares it.
Spelling the name in a mark does not declare it.

**Wrong form:** a mark channel such as `{"signal": "hovered"}` with no `signals` entry that
declares `hovered` at the top level or in the enclosing group.

**Fix:** add a `signals` entry that declares the name, in the top level or in the enclosing group.

```vega
{
  "$schema": "https://vega.github.io/schema/vega/v6.json",
  "width": 200,
  "height": 100,
  "signals": [{"name": "barColor", "value": "steelblue"}],
  "data": [
    {"name": "table", "values": [{"x": 1, "y": 2}, {"x": 2, "y": 4}]}
  ],
  "scales": [
    {"name": "xscale", "type": "linear",
     "domain": {"data": "table", "field": "x"}, "range": "width"},
    {"name": "yscale", "type": "linear",
     "domain": {"data": "table", "field": "y"}, "range": "height"}
  ],
  "marks": [
    {
      "type": "rect",
      "from": {"data": "table"},
      "encode": {
        "enter": {
          "x": {"scale": "xscale", "field": "x"},
          "width": {"value": 20},
          "y": {"scale": "yscale", "field": "y"},
          "height": {"value": 20},
          "fill": {"signal": "barColor"}
        }
      }
    }
  ]
}
```

# Vega signals must be declared before they are read

> Draft. Vega v6. Trap ID: `vega-signal-declaration-order`.

**Symptom:** `Unknown signal name`.

**The trap:** a signal must be declared at the top level or in the enclosing group before a mark
or a data transform references it by name. Declaration order matters: an expression earlier in the
spec than the `signals` entry cannot see that signal yet.

**Why it happens:** a Vega expression has no implicit globals. `{"signal": "barColor"}` reads a
signal called `barColor`, and the dataflow only knows that name once a `signals` entry declares it.
Spelling the name in a mark does not declare it, and a data transform evaluated before the
declaration cannot read it either.

**Wrong form:** a mark channel such as `{"signal": "hovered"}` with no `signals` entry that
declares `hovered`, or a data transform that reads a signal before the `signals` array declares it.

**Fix:** declare signals before the marks and data that read them.

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

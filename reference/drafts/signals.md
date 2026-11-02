# Vega signals must be declared before marks use them

> Draft. Vega v6.

**The trap:** a signal must be declared at the top level or in the enclosing group before a mark
references it by name; an undeclared name in a `signal` or `update` expression fails.

**Why it happens:** a Vega expression has no implicit globals. `{"signal": "barColor"}` reads a
signal called `barColor`, and the dataflow only knows that name if a `signals` entry declares it.
Spelling the name in a mark does not declare it.

**Wrong form:** a mark channel such as `{"signal": "hovered"}` with no `signals` entry that
declares `hovered` at the top level or in the enclosing group.

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

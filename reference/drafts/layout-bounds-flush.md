# `bounds: "flush"` drops marks drawn at negative offsets from the cell size

> Draft. Vega v6. Trap ID: `vega-layout-bounds-flush`.

**Symptom:** with `"full"` a mark at negative `y` counts toward the row height; with `"flush"` it
is excluded and overlaps the previous row. Telltale sign: only the first row's header is fully
visible.

**Cause:** the `flush` bounds ignore the part of a mark that extends past the cell's top or left
edge, so the layout allocates less room than the mark actually uses.

**Wrong form:** `layout.bounds: "flush"` while a cell draws a header at a negative `y`.

**Fix:** use `layout.bounds: "full"` when a mark draws at a negative offset from the cell, or move
the mark inside the cell.

```vega
{
  "$schema": "https://vega.github.io/schema/vega/v6.json",
  "width": 240,
  "height": 120,
  "layout": {"columns": 2, "padding": {"row": 24}, "bounds": "full"},
  "marks": [
    {
      "type": "group",
      "encode": {
        "enter": {
          "x": {"value": 0},
          "y": {"value": -12},
          "width": {"value": 100},
          "height": {"value": 20}
        }
      },
      "marks": [
        {"type": "text", "encode": {"enter": {"text": {"value": "Header"}}}}
      ]
    },
    {
      "type": "group",
      "encode": {
        "enter": {
          "x": {"value": 0},
          "y": {"value": 0},
          "width": {"value": 100},
          "height": {"value": 20}
        }
      },
      "marks": [
        {
          "type": "rect",
          "encode": {
            "enter": {
              "x": {"value": 0},
              "y": {"value": 0},
              "width": {"value": 100},
              "height": {"value": 20},
              "fill": {"value": "steelblue"}
            }
          }
        }
      ]
    }
  ]
}
```

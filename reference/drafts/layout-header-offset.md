# `bounds` and `offset` do not move a group with a header role

> Draft. Vega v6. Trap ID: `vega-layout-header-offset`.

**Symptom:** switching `bounds` changes nothing, and `offset.rowHeader` moves the group
horizontally, never vertically.

**Cause:** a group with `role: "row-header"` (or another header role) is placed by the header
logic, not by the grid bounds. `layout.offset.rowHeader` only shifts it horizontally, away from the
grid edge, and the layout sets its `y`.

**Wrong form:** changing `layout.bounds` or `layout.offset.rowHeader` to move a header group
vertically.

**Fix:** use `layout.padding.row` to create the space between rows. The layout sets the header
group's own `y`, so a `y` in its `encode` is ignored; position the header's content with marks
inside the group.

The example below is the correct form: the space between rows comes from `layout.padding.row`, and
the header group has no `y` of its own.

```vega
{
  "$schema": "https://vega.github.io/schema/vega/v6.json",
  "width": 240,
  "height": 120,
  "layout": {
    "columns": 2,
    "padding": {"row": 24},
    "offset": {"rowHeader": 0}
  },
  "marks": [
    {
      "type": "group",
      "role": "row-header",
      "encode": {
        "enter": {
          "x": {"value": 0},
          "width": {"value": 80},
          "height": {"value": 20}
        }
      },
      "marks": [
        {"type": "text", "encode": {"enter": {"text": {"value": "Row"}}}}
      ]
    },
    {
      "type": "group",
      "encode": {
        "enter": {
          "x": {"value": 0},
          "y": {"value": 0},
          "width": {"value": 80},
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
              "width": {"value": 80},
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

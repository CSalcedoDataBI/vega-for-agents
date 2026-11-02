# `width: "container"` needs a sized container

> Draft. Vega-Lite v6.

**The trap:** `"width": "container"` makes the view follow the width of the element that embeds
it; if that element has no CSS width, the view collapses instead of guessing a size.

**Why it happens:** the value is not a size and not a signal. In a browser embed, Vega-Lite reads
the container element's width at render time; a container whose width is `auto` or `0` has no
usable size for the view, so the chart shrinks to nothing.

**Wrong form:** `"width": "container"` in a page whose embedding element has no CSS size, such as
a bare block element with no width rule.

```vega-lite
{
  "$schema": "https://vega.github.io/schema/vega-lite/v6.json",
  "width": "container",
  "height": 200,
  "data": {
    "values": [
      {"category": "A", "amount": 4},
      {"category": "B", "amount": 9},
      {"category": "C", "amount": 7}
    ]
  },
  "mark": "bar",
  "encoding": {
    "x": {"field": "category", "type": "nominal"},
    "y": {"field": "amount", "type": "quantitative"}
  }
}
```

Give the embedding element a CSS size (for example `width: 600px` or a sized grid cell); then this
spec fills that width and keeps the fixed `height`.

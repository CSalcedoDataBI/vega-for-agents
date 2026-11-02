# `width: "container"` needs a sized container

> Draft. Vega-Lite v6.

**The trap:** `"width": "container"` makes the view follow the width of the element that embeds
it. It fails when that element sizes to its content — `inline` / `inline-block`, a flex or grid
child with no width, a table cell — or when it is hidden (`display: none`, a closed tab) at embed
time, so it measures 0. A bare block element without a width rule does not collapse: it fills its
parent's width by default.

**Why it happens:** `"container"` is not a size and not a signal. Vega-Lite measures the embedding
element at render time. A block element with no width rule fills its parent's width, so it is
fine; an element that sizes to its content or is hidden has no usable width, so the view measures
0 and collapses. The classic "needs a CSS size" case is `"height": "container"`: a block's height
comes from its content, so without an explicit CSS height the view has no height to fill.

**Wrong form:** `"width": "container"` in a page whose embedding element sizes to its content —
`inline` / `inline-block`, a flex or grid child with no width, or a table cell — or is hidden
(`display: none`, a closed tab) at embed time. A bare block element is not the wrong form: it
fills its parent's width.

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

Give the embedding element a real width (for example `width: 600px` or a sized grid cell); then
this spec fills that width and keeps the fixed `height`.

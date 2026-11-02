# Tooltips as an array of field definitions

> Draft. Vega-Lite v6.

**The trap:** to show several fields in a tooltip, use the `tooltip` encoding channel with an array
of field definitions; `"tooltip": true` on the mark is only the shorthand for the default tooltip.

**Why it happens:** `tooltip` exists in two places. As a mark property, `true` turns on the default
tooltip built from the encoded fields. As an encoding channel, it accepts one field definition or
an array of them, which is how you choose the tooltip's fields, titles and formatting.

**Wrong form:** `"tooltip": true` on the mark when the tooltip has to list chosen fields with their
own titles, or a plain string where an array of field definitions is expected.

```vega-lite
{
  "$schema": "https://vega.github.io/schema/vega-lite/v6.json",
  "data": {
    "values": [
      {"category": "A", "amount": 4, "share": 0.2},
      {"category": "B", "amount": 9, "share": 0.45},
      {"category": "C", "amount": 7, "share": 0.35}
    ]
  },
  "mark": "bar",
  "encoding": {
    "x": {"field": "category", "type": "nominal"},
    "y": {"field": "amount", "type": "quantitative"},
    "tooltip": [
      {"field": "category", "type": "nominal", "title": "Category"},
      {"field": "amount", "type": "quantitative", "title": "Amount"},
      {"field": "share", "type": "quantitative", "title": "Share", "format": ".0%"}
    ]
  }
}
```

The alternative is the mark property, for the default tooltip:

```vega-lite
{
  "$schema": "https://vega.github.io/schema/vega-lite/v6.json",
  "data": {"values": [{"category": "A", "amount": 4}]},
  "mark": {"type": "bar", "tooltip": true},
  "encoding": {
    "x": {"field": "category", "type": "nominal"},
    "y": {"field": "amount", "type": "quantitative"}
  }
}
```

# Wrong encoding type for the data

> Draft. Vega-Lite v6. Trap ID: `vl-wrong-encoding-type`.

**Symptom:** a wrong scale, odd aggregations, or an arbitrary order.

**Cause:** `type` does not match the data. `nominal` on dates makes Vega-Lite treat them as
categories, and `quantitative` on text asks for a measure that the values cannot support.

**Wrong form:** `"x": {"field": "date", "type": "nominal"}` on dates, or
`"y": {"field": "label", "type": "quantitative"}` on text.

**Fix:** pick `type` from the data: `temporal` for dates, `ordinal` when order matters, `nominal`
for categories and `quantitative` for measures.

```vega-lite
{
  "$schema": "https://vega.github.io/schema/vega-lite/v6.json",
  "data": {
    "values": [
      {"date": "2024-01-01", "value": 4},
      {"date": "2024-01-02", "value": 7},
      {"date": "2024-01-03", "value": 5}
    ]
  },
  "mark": "line",
  "encoding": {
    "x": {"field": "date", "type": "temporal"},
    "y": {"field": "value", "type": "quantitative"},
    "tooltip": [
      {"field": "date", "type": "temporal"},
      {"field": "value", "type": "quantitative"}
    ]
  }
}
```

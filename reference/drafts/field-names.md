# Field names with spaces or dots

> Draft. Vega-Lite v6. Trap ID: `vl-field-name-escaping`.

**Symptom:** a parse error, or the field is read as a nested path.

**The trap:** a field name that contains a space or a dot has to be written differently in
expressions and in `field` strings: use `datum['field name']` in an expression, and escape a dot as
`"a\\.b"` in an encoding.

**Why it happens:** Vega-Lite reads `.` in `field` as a nested-property path, so `"a.b"` asks for
property `b` of object `a`, not for a column literally named `a.b`. In an expression, `datum.a.b`
walks the same nested path, and a name with a space cannot be written with dot notation at all.

**Wrong form:** `"field": "a.b"` in the encoding, and `datum.a.b` in a `calculate` or `filter`.
Both look for a nested object and find nothing when the column is literally named `a.b`.

**Fix:** use `datum['field name']` in an expression, and escape the dot in a `field` string
(`a\\.b`).

```vega-lite
{
  "$schema": "https://vega.github.io/schema/vega-lite/v6.json",
  "data": {
    "values": [
      {"a.b": 1, "a b": 10},
      {"a.b": 2, "a b": 20},
      {"a.b": 3, "a b": 30}
    ]
  },
  "transform": [{"calculate": "datum['a b'] * 2", "as": "doubled"}],
  "mark": "point",
  "encoding": {
    "x": {"field": "a\\.b", "type": "quantitative"},
    "y": {"field": "doubled", "type": "quantitative"},
    "tooltip": [
      {"field": "a b", "type": "quantitative"},
      {"field": "doubled", "type": "quantitative"}
    ]
  }
}
```

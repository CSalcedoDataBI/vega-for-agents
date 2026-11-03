# An "LCG" evaluated over the index draws diagonals

> Draft. Vega v6. Trap ID: `vega-index-lcg`.

**Symptom:** a pseudo-random point field shows regular stripes.

**Cause:** `((i * a + b) % m) / m` over consecutive `i` is an arithmetic progression modulo `m`,
not an iterated generator, so the points fall on a few lines. Calling it an LCG does not make it
one: an LCG feeds the previous output back into the next step, while this expression only reads the
index.

**Wrong form:** `((datum.i * 9301 + 49297) % 233280) / 233280` as a pseudo-random position.

**Fix:** use a sine hash, `abs(sin(datum.i * 12.9898 + 1.0) * 43758.5453) % 1`, which mixes each
index instead of walking a line modulo `m`.

```vega
{
  "$schema": "https://vega.github.io/schema/vega/v6.json",
  "width": 300,
  "height": 100,
  "data": [
    {
      "name": "points",
      "transform": [
        {"type": "sequence", "start": 0, "stop": 20, "step": 1, "as": "i"}
      ]
    }
  ],
  "marks": [
    {
      "type": "symbol",
      "from": {"data": "points"},
      "encode": {
        "update": {
          "x": {"signal": "datum.i * 15"},
          "y": {"signal": "abs(sin(datum.i * 12.9898 + 1.0) * 43758.5453) % 1 * 100"},
          "size": {"value": 30}
        }
      }
    }
  ]
}
```

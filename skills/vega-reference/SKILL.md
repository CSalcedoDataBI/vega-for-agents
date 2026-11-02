---
name: vega-reference
description: Use when an agent is writing or reviewing a Vega or Vega-Lite spec, choosing a mark, encoding channel, transform, scale or projection, checking an expression function or event selector, or answering whether a name is valid in Vega-Lite and which schema version applies. Resolves every name against the catalogue for the declared language and major version instead of memory.
---

# Vega and Vega-Lite reference

Vega and Vega-Lite are different languages with different schemas. A name valid in one is not
automatically valid in the other, so fix the language first and then the name. One hop: read the
catalogue key you need, not the whole file. All paths below are from the plugin root.

## 1. Fix the language and the major version

Read `$schema` in the spec.

- The path segment after `/schema/` names the language: `vega-lite` → Vega-Lite, `vega` → Vega.
  Do not carry a mark, channel, transform or property from one language to the other.
- Major version: v6 is the default; use v5 only when `$schema` declares v5. A version mismatch is
  a different vocabulary, not a fallback.

| Language | v6 (default) | v5 |
|---|---|---|
| Vega-Lite | `exports/vega-lite-v6.catalog.json` | `exports/vega-lite-v5.catalog.json` |
| Vega | `exports/vega-v6.catalog.json` | `exports/vega-v5.catalog.json` |

If the spec has no `$schema`, treat it as v6 and say so; ask for the version when the answer
depends on it.

## 2. Look the name up in that catalogue

The catalogue is a JSON object. These are its keys:

| What you are checking | Vega-Lite | Vega |
|---|---|---|
| Mark (`mark`) | `marks` | `marks` |
| Encoding channel (key under `encoding`) | `channels` | No encoding channels in Vega |
| Transform | `transforms` | `transforms` |
| Scale type (`scale.type`) | `scaleTypes` | `scaleTypes` |
| Projection type (`projection.type`) | `projectionTypes` | Not enumerated (free string or signal) |
| Any property key | `properties` | `properties` |

Search the exact name under the key; do not read the whole catalogue and do not infer a name
from a nearby one. A name can be a valid property and still be invalid as a mark, channel,
transform or scale type; the key decides the role. `$schema` is always accepted.

If the catalogue has a `meta` block, `meta.schemaVersion` names the schema version and
`meta.schemaSha256` is the SHA-256 of the schema it came from; use them to confirm the version.

## 3. Expressions and event selectors

The JSON Schemas type these as free strings, so the schema catalogues cannot answer them.

- Expression functions: `exports/vega-v6.expressions.catalog.json`. The `functions` array holds
  each name; `categories` groups them and `signatures` gives the arguments. Cards:
  `reference/vega/expressions/README.md` and one page per category in `reference/vega/expressions/`.
- Event selectors: `exports/vega-v6.event-streams.catalog.json`. The `markTypes`, `markEventTypes`,
  `namedSources` and `specialEventTypes` keys are the vocabulary; `syntax` and `examples` show the
  grammar. Card: `reference/vega/event-streams.md`.

These two are Vega 6 vocabularies and are the only ones in the plugin. Vega-Lite expressions
compile to Vega expressions, so the same function list applies; its `on` and `clear` selectors
use the Vega selector grammar.

## 4. If the name is not there

It does not exist for that language and role. Do not use it, and do not "fix" the catalogue:
`exports/*.catalog.json` is generated from the official schemas by `scripts/extract_catalog.py` and
is never edited by hand. A missing name means a new schema version and a re-extraction, following
`CONTRIBUTING.md`. Report it with the `vega-feedback` skill or a plain issue.

## 5. Out of scope

Power BI and Deneb authoring (`pbiFormat`, templates, cross-filter) lives in a separate private
sibling. This skill is a reference, not a tutorial, and it does not render specs; the Vega engine
does.

## Example

A v5 Vega-Lite spec declares the version in `$schema`. The mark, channel and structural property
names below are from the v5 catalogue; the objects inside `values` are data, not names.

```vega-lite
{
  "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
  "data": {"values": [{"category": "A", "amount": 28}]},
  "mark": "bar",
  "encoding": {
    "x": {"field": "category", "type": "nominal"},
    "y": {"field": "amount", "type": "quantitative"}
  }
}
```

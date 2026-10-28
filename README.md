# vega-for-agents

> **Pre-release.** This repository is public from day one, but nothing in it is ready to install
> yet. The catalogues are generated and the checks run in CI, but the function cards and the
> plugin are still planned. Watch the repository or follow the
> [v0.1 epic](https://github.com/CSalcedoDataBI/vega-for-agents/issues/2) if you want to know when
> that changes.

The Vega and Vega-Lite reference for AI agents: two catalogues in one repository, with every
valid name — mark, encoding channel, transform, scale, projection and property — **extracted from
the official JSON Schemas** instead of typed from memory. Each one comes with the traps the
documentation leaves out and an example that was validated against the schema.

It is the sibling of [spark-for-agents](https://github.com/CSalcedoDataBI/spark-for-agents),
[dax-for-agents](https://github.com/CSalcedoDataBI/dax-for-agents) and
[powerquery-m-for-agents](https://github.com/CSalcedoDataBI/powerquery-m-for-agents), and it
follows the same rule: **an agent never reads a name that did not come from the source of truth.**
Here the source of truth is the published schema of each language.

## Two catalogues in one repo

| Catalogue | Source of truth | Vocabularies |
|---|---|---|
| **Vega-Lite v5** | [`vega-lite-v5.schema.json`](exports/vega-lite-v5.schema.json) | marks, encoding channels, transforms, scale types, projection types, every property |
| **Vega v5** | [`vega-v5.schema.json`](exports/vega-v5.schema.json) | marks, transforms, scale types, every property (projection `type` is a free signal, so it is not enumerated) |

`scripts/extract_catalog.py` reads each schema and writes the catalogue of valid names
(`exports/*.catalog.json`). `scripts/check_repo.py` — the required `Validate` check — fails if
anything an agent reads (a card, or an example spec) uses a mark, channel, transform, scale type,
projection type or structural property that is **not in the schema**. That is "no invented name",
applied to Vega and Vega-Lite.

## Expressions and event streams (Vega 6)

The schema types an expression (`"update": "…"`) and an event selector (`"events": "…"`) as free
strings, so neither vocabulary can come from it. They come from the Vega source itself, pinned at
**Vega 6.4.0** under [`sources/vega-6.4.0/`](sources/vega-6.4.0/) with a SHA-256 per file
([`scripts/vega_sources.py`](scripts/vega_sources.py)):

| Catalogue | Extracted from | Cards |
|---|---|---|
| [`vega-v6.expressions.catalog.json`](exports/vega-v6.expressions.catalog.json) | the function registry of `vega-functions` and `vega-expression`, plus the signatures and categories of the expressions doc page | [`reference/vega/expressions/`](reference/vega/expressions/README.md), one per category |
| [`vega-v6.event-streams.catalog.json`](exports/vega-v6.event-streams.catalog.json) | the `vega-event-selector` parser and the event streams doc page | [`reference/vega/event-streams.md`](reference/vega/event-streams.md) |

The cards are generated from the catalogues, never written by hand. `Validate` fails if a vendored
file no longer matches its pin, if a catalogue or a card is out of sync with the pinned source, if
an example spec or a card calls an expression function that Vega does not have, or if an event
selector does not parse or names an event or mark type Vega does not fire. Vega-Lite expressions
compile to Vega expressions, so the same function list applies to them.

The vendored Vega files are © the University of Washington Interactive Data Lab, under their
[BSD-3-Clause license](sources/vega-6.4.0/LICENSE).

## What it will contain

| Piece | Source | Status |
|---|---|---|
| Name catalogues (Vega-Lite + Vega) | the two official JSON Schemas | done |
| Schema-backed name check in CI | `scripts/check_repo.py` | done |
| Expression functions + event-stream grammar (Vega 6) and their cards | the pinned Vega 6.4.0 source | done |
| Trap notes + validated examples | drafted by a model, every name checked against the schema | drafting |
| Reference cards and a plugin | promoted from the drafts | planned |
| `vega-feedback` skill | report a wrong or missing card as a public issue | planned |

## Pinned schema versions

The catalogue is only as good as the schema it came from, so the exact schema is pinned by
SHA-256 in each catalogue's `meta` block. Changing a schema is a new extraction, never a hand edit.

## Not in scope

- The craft of authoring Deneb visuals for Power BI (`pbiFormat`, templates, cross-filter). That
  lives apart, in a private sibling.
- A tutorial on how to build charts. This is a reference an agent consults, not a course.

## License

[MIT](LICENSE).

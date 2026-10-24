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

## What it will contain

| Piece | Source | Status |
|---|---|---|
| Name catalogues (Vega-Lite + Vega) | the two official JSON Schemas | done |
| Schema-backed name check in CI | `scripts/check_repo.py` | done |
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

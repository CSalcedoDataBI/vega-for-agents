# Agent instructions

This repository is **public and in pre-release**. Write every issue and commit with that in mind:
no client names, no real engagements, no credentials, and nothing from private repositories.

It is maintained under the maintainer's internal rules: its north is [FICHA.md](FICHA.md), and the
`experto` agent (`.claude/agents/experto.md`) merges against it.

## Rules specific to this repo

- **Never add a name — a mark, encoding channel, transform, scale type or property — to anything an
  agent reads unless it is in the official schema** (`exports/*.schema.json`, surfaced in
  `exports/*.catalog.json`). This library exists to stop invention, so it cannot contain any. If a
  name is missing, the fix is a new schema version and a re-extraction, not a hand edit.
- **The catalogues are written only by `scripts/extract_catalog.py`.** Never edit
  `exports/*.catalog.json` by hand; re-run the extractor.
- **The schema files are the source of truth.** Do not re-download them except to pin a new exact
  version, and record its SHA-256 in the catalogue `meta`.
- **Every number in the README is counted from the tree**, not typed. Until a check backs a
  number, do not write it.
- **CI runs on GitHub runners, never on a self-hosted one.** The repo is public, and a self-hosted
  runner would execute fork PRs on the maintainer's machine.
- **Vega-Lite vs Vega are two different languages.** A name valid in one is not automatically valid
  in the other; each has its own catalogue. Keep examples labelled by language.
- The repository is in English.

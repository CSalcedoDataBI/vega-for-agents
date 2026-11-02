# Contributing

## Report a bug or a wrong card

Open an [issue](https://github.com/CSalcedoDataBI/vega-for-agents/issues/new). For a name that is
wrong, missing or catalogued under the wrong language, include:

- the language (Vega or Vega-Lite) and the schema version;
- the name and what the catalogue says about it;
- a minimal spec and what the Vega/Vega-Lite compiler did with it.

With the plugin installed, the `vega-feedback` skill collects the same evidence — a minimal
standalone spec with inline data, the renderer and version, what the plugin says and what the
engine did — rewrites anything project-specific, shows you the full text, and files a public issue
only after you approve it. Without the plugin, open the issue directly with that evidence.

## Changes go through a pull request

Every change to `main` comes in through a pull request, and the required `Validate` check must pass
before it can merge. Run the same checks locally first:

```bash
python scripts/check_repo.py
python -m unittest discover -s tests
```

## No name outside the schema

The catalogues under `exports/` are extracted from the official JSON Schemas by
`scripts/extract_catalog.py`, never typed by hand. Anything an agent reads may only name marks,
channels, transforms, scale types and properties that are in them, and `Validate` fails otherwise.
If a name is missing, the fix is a new schema version and a re-extraction, not a hand edit.

Expression functions and event streams follow the same rule against the Vega source pinned in
`scripts/vega_sources.py`. To move to a new Vega version, change `VERSION` and `COMMIT` there, run
`python scripts/vega_sources.py --fetch`, paste the printed SHA-256 pins into `FILES`, and run
`python scripts/extract_catalog.py`. Never edit a file under `sources/` or `reference/vega/`.

## Moving to a new schema version

The structural catalogues are pinned per major version. To pin a new one:

1. Download the published schema byte for byte — no reformatting, no newline changes — to
   `exports/<language>-v<N>.schema.json`. For example:
   `curl -fsSL https://vega.github.io/schema/vega-lite/v6.json -o exports/vega-lite-v6.schema.json`.
2. Verify its SHA-256 (`sha256sum exports/vega-lite-v6.schema.json`) against the release you mean
   to pin. Do not continue if it differs.
3. Add or update the entry in `SCHEMAS` in `scripts/extract_catalog.py`: `schema`, `catalog`,
   `version`, `language`, `package`, `exactVersion` (the release, such as `6.4.3`) and `source`.
   The v5 entries stay: the v5 catalogues are kept for specs that still declare `$schema` v5.
4. Run `python scripts/extract_catalog.py`. It writes the catalogue, the generated
   `reference/schema-diff-v5-v6.md` and the cards; never edit those files by hand.
5. Run `python scripts/extract_catalog.py --check` and `python scripts/check_repo.py`, then the
   tests. The extractor writes the schema's SHA-256 into the catalogue `meta` from the file itself.

## The catalogue format contract

Every catalogue carries `meta.contract`: the semver of the catalogue **format**, set by
`CONTRACT_VERSION` in `scripts/extract_catalog.py`. `exports/manifest.json` records the same
version and the SHA-256 of every exported file. Change the contract when the shape of a catalogue
changes, and bump `CONTRACT_VERSION` in the same pull request:

- **patch** — no change for readers: a typo, or a regenerated value that keeps every key and type;
- **minor** — a new optional key that an existing reader can ignore;
- **major** — a key removed or renamed, or a type changed.

Never edit a catalogue or the manifest by hand: run `python scripts/extract_catalog.py`.

## License

By contributing, you agree that your contribution is licensed under the [MIT License](LICENSE).

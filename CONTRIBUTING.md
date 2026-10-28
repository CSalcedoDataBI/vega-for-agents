# Contributing

## Report a bug or a wrong card

Open an [issue](https://github.com/CSalcedoDataBI/vega-for-agents/issues/new). For a name that is
wrong, missing or catalogued under the wrong language, include:

- the language (Vega or Vega-Lite) and the schema version;
- the name and what the catalogue says about it;
- a minimal spec and what the Vega/Vega-Lite compiler did with it.

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

## License

By contributing, you agree that your contribution is licensed under the [MIT License](LICENSE).

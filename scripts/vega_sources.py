"""The pinned Vega 6 source files that define the expression language and the event-stream grammar.

Neither is in the JSON Schema (the schema types an expression or an event selector as a free
string), so their source of truth is the Vega code and docs themselves. The files are vendored
under sources/vega-<version>/ with their upstream paths, and each one is pinned here by SHA-256:
editing a vendored file, instead of pinning a new version, fails `extract_catalog.py --check`.

    python scripts/vega_sources.py              # verify the vendored files against the pins
    python scripts/vega_sources.py --upstream   # also re-download each file and compare (network)
    python scripts/vega_sources.py --fetch      # (re)download the files at COMMIT (new pin only)

Standard library only.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

VERSION = "6.4.0"
REPO = "vega/vega"
# The commit npm records as gitHead for vega@6.4.0.
COMMIT = "adf0ae7cd5dbc5bd0d7b4fb5566a68adf14cac3f"
# Package versions at that commit (from each package.json), the ones vega@6.4.0 depends on.
PACKAGES = {
    "vega-functions": "6.2.0",
    "vega-expression": "6.2.2",
    "vega-event-selector": "4.0.0",
}
DIR = ROOT / "sources" / f"vega-{VERSION}"

# path inside the vega/vega repository -> SHA-256 of the file at COMMIT.
FILES = {
    "LICENSE":
        "63727832aaf62004a2b249c933e327f3c90caf49e41a72f4bf436edf632cbda8",
    "docs/docs/expressions.md":
        "c3e9249bd97fef08878e070e857b92657b4be17098d5fbd35738443eebc9328e",
    "docs/docs/event-streams.md":
        "8f3432ba2bbb6a845636d5be802a5ef5db7cc410efdef0f8a72742ebd41ae5d2",
    "packages/vega-expression/package.json":
        "a4018be64b9db77ddf98a5ae078800120466afdb68c8d1a3a2be0bca7e06f742",
    "packages/vega-expression/src/constants.js":
        "9b2163fda62bd48c4e11585d05da6935e00e5a90c7b1058a366b99b89f954b6b",
    "packages/vega-expression/src/functions.js":
        "5320819cc538419cda27cf682b047309445c6a71977236cd0d8e97bdf08f5f9f",
    "packages/vega-functions/package.json":
        "7df87e14aa01c67863bbe62172983e9ef413310e6101197d99af70bffed70810",
    "packages/vega-functions/src/codegen.js":
        "dbe4eed91e2c98d02fece34147f9fb8623fc0ec4708085335b2a4c9ee9b7c3c6",
    "packages/vega-functions/src/scales.js":
        "780396938cac43f455ab438eb3e73e0150babbda87f14a13a498680ce67d8cf2",
    "packages/vega-functions/src/functions/ease.js":
        "b8a0231b6f0b9fbc9d90732c8fafa0d731766debbca68673842257f86647a2a3",
    "packages/vega-event-selector/package.json":
        "7abc48ed5549aaff71a301e00ca65ca1a8e3b9faf97a265e437390037f5acaad",
    "packages/vega-event-selector/src/event-selector.js":
        "f071d2bcbd1398a9812f418cd0571cc64dc77ef0c0674010f460ac13b6f7bd77",
}


def raw_url(path: str) -> str:
    return f"https://raw.githubusercontent.com/{REPO}/{COMMIT}/{path}"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read(path: str) -> str:
    return (DIR / path).read_text(encoding="utf-8")


def verify(upstream: bool = False) -> list[str]:
    errors = []
    for path, pinned in FILES.items():
        local = DIR / path
        rel = local.relative_to(ROOT).as_posix()
        if not local.exists():
            errors.append(f"{rel}: missing; run scripts/vega_sources.py --fetch")
            continue
        got = sha256_bytes(local.read_bytes())
        if got != pinned:
            errors.append(f"{rel}: SHA-256 {got[:12]}... does not match the pin {pinned[:12]}...; "
                          f"a vendored source is never edited, pin a new version instead")
        if upstream:
            with urllib.request.urlopen(raw_url(path), timeout=30) as resp:
                remote = sha256_bytes(resp.read())
            if remote != pinned:
                errors.append(f"{rel}: upstream {REPO}@{COMMIT[:7]} has SHA-256 {remote[:12]}..., "
                              f"not the pin {pinned[:12]}...")
    return errors


def fetch() -> None:
    for path in FILES:
        with urllib.request.urlopen(raw_url(path), timeout=30) as resp:
            data = resp.read()
        target = DIR / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        print(f'    "{path}": "{sha256_bytes(data)}",')


def meta() -> dict:
    """The provenance block every catalogue extracted from these files carries."""
    return {
        "vegaVersion": VERSION,
        "source": f"https://github.com/{REPO}/tree/{COMMIT}",
        "commit": COMMIT,
        "packages": dict(PACKAGES),
        "vendoredAt": DIR.relative_to(ROOT).as_posix(),
        "license": "BSD-3-Clause (sources/vega-%s/LICENSE)" % VERSION,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Verify or fetch the pinned Vega source files.")
    ap.add_argument("--fetch", action="store_true", help="download the files at COMMIT")
    ap.add_argument("--upstream", action="store_true", help="also compare against GitHub")
    args = ap.parse_args(argv)
    if args.fetch:
        fetch()
        return 0
    errors = verify(upstream=args.upstream)
    for error in errors:
        print(f"FAIL {error}")
    if not errors:
        print(f"OK vega {VERSION} sources match their pins ({len(FILES)} files)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

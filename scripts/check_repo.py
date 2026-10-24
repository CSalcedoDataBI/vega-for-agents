"""Repository checks that run in CI (the required `Validate` check).

- Every skills/*/SKILL.md opens with frontmatter that has `name` (matching its folder) and
  `description`.
- Every workflow job sets `timeout-minutes` and runs on `ubuntu-latest`, and every workflow
  declares `concurrency` (Actions cost rules R2, R3, R5).
- No name outside the official schema: in what an agent reads (skills/**/*.md fenced ```vega /
  ```vega-lite example specs, and the drafts in lab/drafting/out/), every mark, encoding channel,
  transform, scale type and structural property must be in the language's catalogue
  (exports/*.catalog.json, extracted from exports/*.schema.json). "No invented name", for
  Vega and Vega-Lite.

Standard library only, so CI needs no install step. Exit code 1 lists every failure.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOGS = {
    "vega-lite": ROOT / "exports" / "vega-lite-v5.catalog.json",
    "vega": ROOT / "exports" / "vega-v5.catalog.json",
}
# A fenced block whose info string names the language, capturing the language and the body.
FENCE = re.compile(r"^```(vega-lite|vega)\s*\n(.*?)^```", re.M | re.S)
# Keys whose object/array VALUES are user data (field names, arbitrary rows), not schema names.
DATA_SUBTREES = {"values", "datum", "usermeta", "datasets"}
# Objects whose immediate KEYS are free-form by schema (patternProperties / additionalProperties):
# a Vega `encode` block's set names (enter/update/custom) and a `style` config's style names. Their
# nested values are still real schema objects, so recurse into them but do not check these keys.
FREE_KEY_PARENTS = {"encode", "style"}
# Structural keys valid in a spec that are not JSON-Schema `properties` entries.
ALWAYS_OK_KEYS = {"$schema"}


def load_catalogs(root: Path = ROOT):
    cats = {}
    for lang, path in CATALOGS.items():
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            cats[lang] = {
                "marks": set(data.get("marks", [])),
                "channels": set(data.get("channels", [])),
                "transforms": set(data.get("transforms", [])),
                "scaleTypes": set(data.get("scaleTypes", [])),
                "projectionTypes": set(data.get("projectionTypes", [])),
                # Channels are properties too; union so an encoding key is never a false positive.
                "props": set(data.get("properties", [])) | set(data.get("channels", []))
                | ALWAYS_OK_KEYS,
            }
    return cats


# --- repo-shape checks (skills, workflows) --------------------------------------------------

def check_skills() -> list[str]:
    errors = []
    for skill in sorted((ROOT / "skills").glob("*/SKILL.md")):
        text = skill.read_text(encoding="utf-8")
        match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
        rel = skill.relative_to(ROOT).as_posix()
        if not match:
            errors.append(f"{rel}: missing frontmatter")
            continue
        fields = dict(
            line.split(":", 1) for line in match.group(1).splitlines()
            if ":" in line and not line.startswith(" ")
        )
        name = fields.get("name", "").strip()
        if name != skill.parent.name:
            errors.append(f"{rel}: name '{name}' does not match folder '{skill.parent.name}'")
        if not fields.get("description", "").strip():
            errors.append(f"{rel}: empty description")
    return errors


def check_workflows() -> list[str]:
    errors = []
    for wf in sorted((ROOT / ".github" / "workflows").glob("*.y*ml")):
        text = wf.read_text(encoding="utf-8")
        rel = wf.relative_to(ROOT).as_posix()
        if not re.search(r"^concurrency:", text, re.M):
            errors.append(f"{rel}: no top-level concurrency (R2)")
        jobs = len(re.findall(r"^\s+runs-on:", text, re.M))
        timeouts = len(re.findall(r"^\s+timeout-minutes:", text, re.M))
        if timeouts < jobs:
            errors.append(f"{rel}: {jobs} jobs but {timeouts} timeout-minutes (R3)")
        for runner in re.findall(r"^\s+runs-on:\s*(.+)$", text, re.M):
            if runner.strip() != "ubuntu-latest":
                errors.append(f"{rel}: runs-on {runner.strip()} (R5, no self-hosted on a public repo)")
    return errors


# --- the name check: validate an example spec against its language catalogue ----------------

def validate_spec(spec, lang: str, cat: dict, where: str) -> list[str]:
    """Walk a Vega/Vega-Lite spec and flag any name not in the catalogue. Closed vocabularies
    (marks, channels, transforms, scale types) are checked by context; property keys are checked
    against the catalogue's property set, skipping subtrees that hold user data."""
    errors: list[str] = []

    def mark_type(node):
        if isinstance(node, str):
            return node
        if isinstance(node, dict) and isinstance(node.get("type"), str):
            return node["type"]
        return None

    def walk(node, parent_key=None) -> None:
        if isinstance(node, dict):
            # mark type
            if "mark" in node:
                m = mark_type(node["mark"])
                if m is not None and m not in cat["marks"]:
                    errors.append(f"{where}: mark '{m}' is not in the {lang} schema")
            # a Vega mark object: {"type": "symbol", ...}
            if lang == "vega" and parent_key == "marks-item":
                m = node.get("type")
                if isinstance(m, str) and m not in cat["marks"]:
                    errors.append(f"{where}: mark '{m}' is not in the {lang} schema")
            # encoding channels (Vega-Lite)
            if lang == "vega-lite" and isinstance(node.get("encoding"), dict):
                for ch in node["encoding"]:
                    if ch not in cat["channels"]:
                        errors.append(f"{where}: encoding channel '{ch}' is not in the {lang} schema")
            # transforms
            if isinstance(node.get("transform"), list):
                for t in node["transform"]:
                    if not isinstance(t, dict):
                        continue
                    if lang == "vega-lite":
                        if not (set(t.keys()) & cat["transforms"]):
                            errors.append(
                                f"{where}: transform {sorted(t.keys())} has no known transform "
                                f"keyword in the {lang} schema")
                    else:
                        ty = t.get("type")
                        if isinstance(ty, str) and ty not in cat["transforms"]:
                            errors.append(f"{where}: transform '{ty}' is not in the {lang} schema")
            # scale type
            sc = node.get("scale")
            if isinstance(sc, dict) and isinstance(sc.get("type"), str):
                if sc["type"] not in cat["scaleTypes"]:
                    errors.append(f"{where}: scale type '{sc['type']}' is not in the {lang} schema")
            # projection type (Vega-Lite enumerates these; Vega leaves it a free string)
            pr = node.get("projection")
            if cat["projectionTypes"] and isinstance(pr, dict) and isinstance(pr.get("type"), str):
                if pr["type"] not in cat["projectionTypes"]:
                    errors.append(f"{where}: projection type '{pr['type']}' is not in the {lang} schema")

            # property-key check (skip user-data subtrees and free-key containers)
            free_keys = parent_key in FREE_KEY_PARENTS
            for key, value in node.items():
                if not free_keys and key not in cat["props"]:
                    errors.append(f"{where}: property '{key}' is not in the {lang} schema")
                if key in DATA_SUBTREES:
                    continue  # values / datum / usermeta hold user data, not schema names
                # A Vega top-level "marks" array holds mark objects: tag them so their `type` is
                # checked as a mark name.
                if lang == "vega" and key == "marks":
                    for item in (value if isinstance(value, list) else [value]):
                        walk(item, parent_key="marks-item")
                else:
                    walk(value, parent_key=key)
        elif isinstance(node, list):
            for item in node:
                walk(item, parent_key=parent_key)

    walk(spec)
    return errors


def check_names(root: Path = ROOT) -> list[str]:
    cats = load_catalogs(root)
    errors: list[str] = []

    # Fenced example specs in skills markdown.
    md_files = list((root / "skills").glob("**/*.md"))
    draft_files = list((root / "lab" / "drafting" / "out").glob("**/*.json"))
    if (md_files or draft_files) and not cats:
        return ["example specs to check but no catalogue under exports/ (run extract_catalog.py)"]

    for md in sorted(md_files):
        rel = md.relative_to(root).as_posix()
        text = md.read_text(encoding="utf-8")
        for i, (lang, body) in enumerate(FENCE.findall(text), 1):
            if lang not in cats:
                continue
            try:
                spec = json.loads(body)
            except json.JSONDecodeError as exc:
                errors.append(f"{rel}: {lang} block #{i} is not valid JSON ({exc})")
                continue
            errors += validate_spec(spec, lang, cats[lang], f"{rel} ({lang} block #{i})")

    for draft in sorted(draft_files):
        rel = draft.relative_to(root).as_posix()
        data = json.loads(draft.read_text(encoding="utf-8"))
        for note in data.get("notes", []):
            lang = note.get("lang")
            if lang not in cats:
                errors.append(f"{rel}: note has unknown lang '{lang}'")
                continue
            cat = cats[lang]
            name = note.get("name", "")
            vocab = (cat["marks"] | cat["channels"] | cat["transforms"] | cat["scaleTypes"]
                     | cat["projectionTypes"] | cat["props"])
            if name and name not in vocab:
                errors.append(f"{rel}: name '{name}' is not in the {lang} schema")
            example = note.get("example")
            if isinstance(example, (dict, list)):
                errors += validate_spec(example, lang, cat, f"{rel} (note '{name}')")
    return errors


def main() -> int:
    errors = check_skills() + check_workflows() + check_names()
    for error in errors:
        print(f"FAIL {error}")
    if not errors:
        print("OK repo checks")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

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
- No invented expression function or event stream: every function called in an expression string
  of an example spec (`expr`, `update`, `signal`, `test`, `calculate`, ...) or in a call written as
  inline code in a card (skills/ or reference/) must be in exports/vega-v6.expressions.catalog.json,
  and every event selector string (Vega `events`, Vega-Lite `on` / `clear`) must parse with the
  Vega selector grammar and use the mark and event types of exports/vega-v6.event-streams.catalog.json.

Standard library only, so CI needs no install step. Exit code 1 lists every failure.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import vega_language  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
EXPRESSIONS = Path("exports") / "vega-v6.expressions.catalog.json"
EVENT_STREAMS = Path("exports") / "vega-v6.event-streams.catalog.json"
# Spec keys whose string value is a Vega expression. `filter` counts only as a string: a Vega-Lite
# filter predicate written as an expression, or an event-stream filter.
EXPR_KEYS = {"expr", "update", "signal", "test", "calculate", "init", "filter"}
# Spec keys whose string value is an event selector: Vega `events`, Vega-Lite selection `on`/`clear`.
EVENT_KEYS = {"vega": {"events"}, "vega-lite": {"on", "clear"}}
# Inline code in a card that is a whole call: `name(...)`, optionally indexed (`f()[0]`). Prose
# such as `f(0) === 0` or `test(x) -> true` is not a call on its own and is not checked.
INLINE_CALL = re.compile(r"`([A-Za-z_$][\w$]*\([^`]*\)(?:\[[^`\]]*\])?)`")
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


def load_language(root: Path = ROOT):
    """The expression functions and the event-stream vocabulary, or None if not extracted yet."""
    expr, ev = root / EXPRESSIONS, root / EVENT_STREAMS
    if not (expr.exists() and ev.exists()):
        return None
    e = json.loads(expr.read_text(encoding="utf-8"))
    s = json.loads(ev.read_text(encoding="utf-8"))
    return {
        "functions": {f["name"] for f in e["functions"]},
        "markTypes": s["markTypes"],
        "namedSources": set(s["namedSources"]),
        "markEventTypes": set(s["markEventTypes"]),
        "special": {t["type"]: t.get("source") for t in s["specialEventTypes"]},
    }


def check_expression(expr: str, lang_cat: dict, where: str) -> list[str]:
    return [f"{where}: expression function '{name}' is not in the Vega expression language"
            for name in vega_language.called_functions(expr)
            if name not in lang_cat["functions"]]


def check_selector(selector: str, lang_cat: dict, where: str) -> list[str]:
    """Parse an event selector as Vega does and check its mark, source and event types."""
    try:
        streams = vega_language.parse_selector(selector, mark_types=lang_cat["markTypes"])
    except vega_language.SelectorError as exc:
        return [f"{where}: event selector {selector!r} does not parse ({exc})"]
    errors: list[str] = []

    def walk(st: dict) -> None:
        for sub in st.get("between", []):
            walk(sub)
        if "stream" in st:
            walk(st["stream"])
            return
        source, ev = st.get("source"), st.get("type")
        for f in st.get("filter", []):
            errors.extend(check_expression(f, lang_cat, where))
        on_scenegraph = "marktype" in st or "markname" in st or source in ("view", "scope")
        if ev in lang_cat["special"]:
            # timer: any source. resize: the `container` source, or a DOM source such as window.
            needs = lang_cat["special"][ev]
            if needs and on_scenegraph:
                errors.append(f"{where}: event '{ev}' is not fired by marks or the view; use the "
                              f"'{needs}' source, in {selector!r}")
            return
        if on_scenegraph and ev not in lang_cat["markEventTypes"]:
            errors.append(f"{where}: event type '{ev}' is not a Vega event type for marks or the "
                          f"view, in {selector!r}")
        if not on_scenegraph and source not in lang_cat["namedSources"] \
                and re.fullmatch(r"[A-Za-z]\w*", source or ""):
            errors.append(f"{where}: '{source}' in {selector!r} is not a Vega mark type or source; "
                          f"Vega would read it as a CSS selector")

    for st in streams:
        walk(st)
    return errors


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

def validate_spec(spec, lang: str, cat: dict, where: str, lang_cat: dict | None = None) -> list[str]:
    """Walk a Vega/Vega-Lite spec and flag any name not in the catalogue. Closed vocabularies
    (marks, channels, transforms, scale types) are checked by context; property keys are checked
    against the catalogue's property set, skipping subtrees that hold user data. With `lang_cat`,
    expression strings and event selectors are checked against the Vega language catalogues."""
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

            # expression strings and event selectors
            if lang_cat is not None:
                for key, value in node.items():
                    if key in EXPR_KEYS and isinstance(value, str):
                        errors.extend(check_expression(value, lang_cat, where))
                    if key in EVENT_KEYS[lang] and isinstance(value, str):
                        errors.extend(check_selector(value, lang_cat, where))

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


def card_files(root: Path) -> list[Path]:
    return sorted(list((root / "skills").glob("**/*.md")) + list((root / "reference").glob("**/*.md")))


def check_cards(root: Path = ROOT) -> list[str]:
    """A call written as inline code in a card must call only catalogued expression functions."""
    lang_cat = load_language(root)
    files = card_files(root)
    if not lang_cat:
        return ["cards to check but no expression catalogue under exports/"] if files else []
    errors: list[str] = []
    for md in files:
        rel = md.relative_to(root).as_posix()
        for lineno, line in enumerate(md.read_text(encoding="utf-8").splitlines(), 1):
            for code in INLINE_CALL.findall(line):
                errors.extend(check_expression(code, lang_cat, f"{rel}:{lineno}"))
    return errors


def check_names(root: Path = ROOT) -> list[str]:
    cats = load_catalogs(root)
    lang_cat = load_language(root)
    errors: list[str] = []

    # Fenced example specs in skills and reference markdown.
    md_files = card_files(root)
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
            errors += validate_spec(spec, lang, cats[lang], f"{rel} ({lang} block #{i})", lang_cat)

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
                errors += validate_spec(example, lang, cat, f"{rel} (note '{name}')", lang_cat)
    return errors


def main() -> int:
    errors = check_skills() + check_workflows() + check_names() + check_cards()
    for error in errors:
        print(f"FAIL {error}")
    if not errors:
        print("OK repo checks")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

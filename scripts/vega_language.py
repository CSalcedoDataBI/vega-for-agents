"""Read the Vega expression language and event-stream grammar out of the pinned Vega 6 sources.

The JSON Schema types an expression and an event selector as free strings, so neither vocabulary
can come from it. This module reads them from the vendored Vega files (scripts/vega_sources.py):

- **Which expression functions exist** comes from the code: the built-ins of `vega-expression`
  (functions.js, constants.js), the event functions and the function context of `vega-functions`
  (codegen.js, functions/ease.js, scales.js), and every `expressionFunction(...)` registration.
- **Signature and category** come from the doc page (docs/docs/expressions.md), the category being
  the section the doc lists the function under.
- **The event-stream grammar** comes from the selector parser (`vega-event-selector`) and its doc
  page (docs/docs/event-streams.md).

It also ports the selector parser to Python, so the repo checks can read an `"events"` string the
way Vega does. Standard library only. Nothing here is typed from memory: every list is a regex over
a pinned file, and the extractor fails if a pattern stops matching.
"""

from __future__ import annotations

import json
import re

import vega_sources as vs

DOCS_BASE = "https://vega.github.io/vega/docs/"
EXPR_DOC = "docs/docs/expressions.md"
EVENT_DOC = "docs/docs/event-streams.md"
F_EXPR_FUNCTIONS = "packages/vega-expression/src/functions.js"
F_EXPR_CONSTANTS = "packages/vega-expression/src/constants.js"
F_CODEGEN = "packages/vega-functions/src/codegen.js"
F_EASE = "packages/vega-functions/src/functions/ease.js"
F_SCALES = "packages/vega-functions/src/scales.js"
F_SELECTOR = "packages/vega-event-selector/src/event-selector.js"


class ExtractError(RuntimeError):
    """A pattern no longer matches the pinned source: the extractor must be updated, not guessed."""


def _need(match, what: str, path: str):
    if not match:
        raise ExtractError(f"{path}: could not find {what}")
    return match


def _block(text: str, start: str, end: str, path: str) -> str:
    i = text.find(start)
    _need(i >= 0, repr(start), path)
    j = text.find(end, i + len(start))
    _need(j >= 0, repr(end), path)
    return text[i + len(start):j]


# --- the function registry (code) ------------------------------------------------------------

def registry() -> dict[str, dict]:
    """Every name the expression code generator accepts as a function, with where it is defined."""
    out: dict[str, dict] = {}

    def add(name: str, path: str, kind: str) -> None:
        out.setdefault(name, {"definedIn": path, "kind": kind})

    # vega-expression built-ins: the keys of the object functions(codegen) returns.
    text = vs.read(F_EXPR_FUNCTIONS)
    body = _block(text, "return {", "\n  };", F_EXPR_FUNCTIONS)
    names = re.findall(r"^ {4}(\w+)\s*:", body, re.M)
    _need(names, "built-in function keys", F_EXPR_FUNCTIONS)
    for name in names:
        add(name, F_EXPR_FUNCTIONS, "builtin")

    # vega-functions: event functions, the function context, and expressionFunction registrations.
    text = vs.read(F_CODEGEN)
    ev = _need(re.search(r"eventFunctions\s*=\s*\[([^\]]*)\]", text), "eventFunctions", F_CODEGEN)
    for name in re.findall(r"'(\w+)'", ev.group(1)):
        add(name, F_CODEGEN, "event")
    ctx = _block(text, "export const functionContext = {", "\n};", F_CODEGEN)
    for line in ctx.splitlines():
        spread = re.match(r"^\s+\.\.\.(\w+)", line)
        if spread:
            if spread.group(1) != "easeFunctions":
                raise ExtractError(f"{F_CODEGEN}: unknown spread ...{spread.group(1)}")
            ease = _block(vs.read(F_EASE), "export const easeFunctions = {", "\n};", F_EASE)
            for name in re.findall(r"^\s+(\w+)\s*:", ease, re.M):
                add(name, F_EASE, "context")
            continue
        m = re.match(r"^\s+(\w+)\s*(?:,|\(|:|$)", line)
        if m:
            add(m.group(1), F_CODEGEN, "context")
    regs = re.findall(r"^expressionFunction\('(\w+)'", text, re.M)
    _need(regs, "expressionFunction registrations", F_CODEGEN)
    for name in regs:
        add(name, F_CODEGEN, "registered")

    # Internal scale helpers the mark encoders call; legal to the parser, never documented.
    scales = _block(vs.read(F_SCALES), "return {", "\n  };", F_SCALES)
    for name in re.findall(r"^\s+(_\w+)\s*:", scales, re.M):
        add(name, F_SCALES, "internal")
    return out


def constants() -> dict[str, str]:
    body = _block(vs.read(F_EXPR_CONSTANTS), "export default {", "\n};", F_EXPR_CONSTANTS)
    pairs = re.findall(r"^\s+(\w+)\s*:\s*'([^']*)'", body, re.M)
    _need(pairs, "constants", F_EXPR_CONSTANTS)
    return dict(pairs)


def bound_variables() -> list[str]:
    m = _need(re.search(r"allowed:\s*\[([^\]]*)\]", vs.read(F_CODEGEN)), "allowed", F_CODEGEN)
    return re.findall(r"'(\w+)'", m.group(1))


# --- the doc page (signatures, categories, descriptions) -------------------------------------

def _doc_links(text: str, page: str) -> str:
    """Make the doc's relative links absolute, so a card read outside the Vega site still works."""
    text = re.sub(r"\]\(#([\w-]+)\)", lambda m: f"]({DOCS_BASE}{page}/#{m.group(1)})", text)
    text = re.sub(r"\]\(\.\./([^)]*)\)", lambda m: f"]({DOCS_BASE}{m.group(1)})", text)
    return text


def _plain(html: str) -> str:
    html = re.sub(r"\{%\s*include tag ver=\"[^\"]*\"\s*%\}", "", html)
    html = re.sub(r"\{%[^%]*%\}", "", html)
    html = re.sub(r"</?(?:i|b|code)>", "", html)
    return re.sub(r"\s+", " ", html).strip()


def _markdown(html: str) -> str:
    html = re.sub(r"\{%\s*include tag ver=\"([^\"]*)\"\s*%\}", r"(since Vega \1)", html)
    html = re.sub(r"\{%[^%]*%\}", "", html)
    html = re.sub(r"<i>(.*?)</i>", r"_\1_", html)
    html = re.sub(r"<b>(.*?)</b>", r"**\1**", html)
    html = html.replace("<br/>", "\n").replace("&ndash;", "-")
    return html.strip()


def _signatures(header: str) -> list[str]:
    sigs = []
    for m in re.finditer(r"<b>(\w+)</b>", header):
        i = m.end()
        if i < len(header) and header[i] == "(":
            depth, j = 0, i
            while j < len(header):
                depth += {"(": 1, ")": -1}.get(header[j], 0)
                if depth == 0:
                    break
                j += 1
            sigs.append(m.group(1) + _plain(header[i:j + 1]))
        else:
            sigs.append(m.group(1))
    return sigs


def doc_sections(path: str = EXPR_DOC, page: str = "expressions") -> list[dict]:
    """The doc page as ordered sections, each with its intro and its entries."""
    lines = vs.read(path).split("\n")
    sections: list[dict] = []
    section = None
    i = 0
    while i < len(lines):
        line = lines[i]
        head = re.match(r'^## <a name="([\w-]+)"></a>(.+)$', line)
        if head:
            section = {"id": head.group(1), "title": head.group(2).strip(), "intro": [],
                       "entries": []}
            sections.append(section)
            i += 1
            continue
        anchor = re.match(r'^<a name="([\w-]+)" href="#[\w-]+">#</a>\s*$', line)
        if anchor and section is not None:
            j = i + 1
            header = []
            while j < len(lines) and lines[j].startswith(("<b>", "<i>")):
                header.append(lines[j])
                j += 1
                if "<br/>" in header[-1]:
                    break
            head_text = "\n".join(header)
            rest = ""
            if "<br/>" in head_text:
                head_text, rest = head_text.split("<br/>", 1)
            body = [rest] if rest.strip() else []
            while j < len(lines) and not (lines[j].startswith(("<a name=", "## "))
                                         or lines[j].startswith("[Back to Top]")):
                body.append(lines[j])
                j += 1
            since = re.search(r'include tag ver="([^"]*)"', head_text)
            section["entries"].append({
                "anchor": anchor.group(1),
                "names": [m.group(1) for m in re.finditer(r"<b>(\w+)</b>", head_text)],
                "signatures": _signatures(head_text),
                "since": since.group(1) if since else None,
                "description": _doc_links(_markdown("\n".join(body).strip()), page),
            })
            i = j
            continue
        if section is not None and not section["entries"] and not line.startswith("[Back to Top]"):
            section["intro"].append(line)
        i += 1
    for s in sections:
        s["intro"] = _doc_links(_markdown("\n".join(s["intro"]).strip()), page)
    return sections


def expressions_catalog() -> dict:
    reg = registry()
    consts = constants()
    sections = [s for s in doc_sections() if s["id"] != "reference"]
    documented: dict[str, list] = {}
    categories = []
    doc_constants = set()
    doc_bound = []
    for s in sections:
        if s["id"] == "bound-variables":
            doc_bound = [n for e in s["entries"] for n in e["names"]]
            continue
        if s["id"] == "constants":
            doc_constants = {n for e in s["entries"] for n in e["names"]}
            continue
        names = []
        for e in s["entries"]:
            for name in dict.fromkeys(e["names"]):
                documented.setdefault(name, []).append({
                    "category": s["id"],
                    "anchor": e["anchor"],
                    "signatures": [g for g in e["signatures"] if re.match(r"\w+", g)[0] == name],
                    "since": e["since"],
                    "description": e["description"],
                })
                if name not in names:
                    names.append(name)
        categories.append({"id": s["id"], "title": s["title"], "intro": s["intro"],
                           "functions": names})

    doc_only = sorted(set(documented) - set(reg))
    if doc_only:
        raise ExtractError(f"{EXPR_DOC}: documents functions the code does not register: {doc_only}")
    missing_consts = sorted(doc_constants ^ set(consts))
    if missing_consts:
        raise ExtractError(f"constants differ between {EXPR_DOC} and {F_EXPR_CONSTANTS}: "
                           f"{missing_consts}")

    functions = []
    for name in sorted(reg, key=lambda n: (n.lower(), n)):
        entries = documented.get(name, [])
        functions.append({
            "name": name,
            "documented": bool(entries),
            "categories": sorted({e["category"] for e in entries},
                                 key=[c["id"] for c in categories].index),
            "signatures": list(dict.fromkeys(g for e in entries for g in e["signatures"])),
            "since": next((e["since"] for e in entries if e["since"]), None),
            "kind": reg[name]["kind"],
            "definedIn": reg[name]["definedIn"],
            "docs": [{k: e[k] for k in ("category", "anchor", "signatures", "description")}
                     for e in entries],
        })
    meta = {
        "language": "vega",
        "vocabulary": "expression functions",
        **vs.meta(),
        "files": {p: vs.FILES[p] for p in (EXPR_DOC, F_EXPR_FUNCTIONS, F_EXPR_CONSTANTS,
                                           F_CODEGEN, F_EASE, F_SCALES)},
        "generatedBy": "scripts/extract_catalog.py",
        "notes": [
            "`functions` is every name the Vega expression code generator accepts as a call. "
            "`documented: false` marks names the code registers but the doc page does not list "
            "(internal helpers and Vega-Lite selection plumbing): legal, but undocumented.",
            "`categories` and `signatures` are the sections and signature lines of the doc page; a "
            "function the doc lists twice (array and string `indexof`, for example) has both.",
            "Vega-Lite expressions (`calculate`, `filter`, `expr`, `test`) compile to Vega "
            "expressions, so they use this same function set.",
        ],
    }
    return {
        "meta": meta,
        "boundVariables": bound_variables(),
        "docBoundVariables": doc_bound,
        "constants": [{"name": n, "value": consts[n]} for n in sorted(consts)],
        "categories": categories,
        "functions": functions,
    }


# --- the event-stream grammar ----------------------------------------------------------------

def _selector_constants(text: str) -> dict[str, str]:
    head = _block(text, "const VIEW", ";", F_SELECTOR)
    return dict(re.findall(r"(\w+)\s*=\s*'([^']*)'", "VIEW" + head))


def event_streams_catalog() -> dict:
    src = vs.read(F_SELECTOR)
    tok = _selector_constants(src)
    marks_block = _block(src, "DEFAULT_MARKS = {", "}", F_SELECTOR)
    mark_types = re.findall(r"^\s+'?([\w*]+)'?\s*:", marks_block, re.M)
    _need(mark_types, "DEFAULT_MARKS", F_SELECTOR)
    consume = _need(re.search(r"stream\.type\.slice\(-1\) === '(.)'", src), "consume marker",
                    F_SELECTOR).group(1)
    fields = list(dict.fromkeys(re.findall(r"stream\.(\w+)\s*=", src)))
    fields = ["source"] + [f for f in fields if f != "source"]
    if "between: b" in src and "between" not in fields:
        fields.append("between")
    if "stream: stream" in src:
        fields.append("stream")

    doc = vs.read(EVENT_DOC)
    types_block = _block(doc, '<a name="types"></a>Supported Event Types', "{: .column-list}",
                         EVENT_DOC)
    dom_types = re.findall(r"^- \[`(\w+)`\]", types_block, re.M)
    _need(dom_types, "supported event types", EVENT_DOC)
    timer = _need(re.search(r"Vega supports a `(\w+)` event, which fires", doc), "timer", EVENT_DOC)
    resize = _need(re.search(
        r"supports a `(\w+)` event on the `(\w+)` source.*?include tag ver=\"([^\"]+)\"", doc, re.S),
        "container resize", EVENT_DOC)
    form = _need(re.search(r"^`(\(source:\)\?type.*)`$", doc, re.M), "general form", EVENT_DOC)

    basic = _block(doc, "The _source_ property supports the following options:", "The _type_ ",
                   EVENT_DOC)
    named_sources = []
    for line in basic.splitlines():
        if line.startswith("- The string"):
            named_sources += re.findall(r"`([^`]+)`", line.split(", indicating")[0])
    _need(named_sources, "named sources", EVENT_DOC)

    # Object properties: the rows of every property table between the object and selector sections.
    obj_part = _block(doc, '<a name="object"></a>Event Stream Objects', '<a name="selector"></a>',
                      EVENT_DOC)
    props = []
    for name, typ, desc in re.findall(r"^\|\s*(\w+)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*$", obj_part,
                                      re.M):
        if name == "Property":
            continue
        props.append({
            "name": name,
            "required": "include required" in desc,
            "type": _doc_links(_plain(
                re.sub(r'\{%\s*include (type|array) t="([^"]*)"\s*%\}',
                       lambda m: m.group(2) + ("[]" if m.group(1) == "array" else ""), typ)
                .replace("{% include or %}", " | ")), "event-streams"),
            "description": _doc_links(_markdown(desc.replace("{% include required %}", "")),
                                      "event-streams"),
        })

    refs = re.findall(r"\[(\w+) references\]\(#\w+\)[^`]*`\{\"(\w+)\"", doc)
    examples = []
    ex_block = _block(doc, "Here are some examples of basic event selectors:\n\n```\n", "```",
                      EVENT_DOC)
    for line in ex_block.splitlines():
        m = re.match(r"^(.*?)\s*//\s*(.*)$", line)
        if m:
            examples.append({"selector": m.group(1), "comment": m.group(2),
                             "parsed": parse_selector(m.group(1), mark_types=mark_types)})
    for sel in re.findall(r"^`([^`(]+(?:\[[^`]*\][^`]*)?)`$", _block(
            doc, "### Merge Selectors", '<a name="signal"></a>', EVENT_DOC), re.M):
        if "selector" not in sel:
            examples.append({"selector": sel, "comment": "", "parsed": parse_selector(
                sel, mark_types=mark_types)})

    meta = {
        "language": "vega",
        "vocabulary": "event streams",
        **vs.meta(),
        "files": {p: vs.FILES[p] for p in (EVENT_DOC, F_SELECTOR)},
        "generatedBy": "scripts/extract_catalog.py",
        "notes": [
            "`markTypes` and the selector tokens come from the parser (vega-event-selector); "
            "event types, named sources and object properties come from the doc page.",
            "`markEventTypes` applies only to events on scenegraph items (marks, view, scope). "
            "Other DOM sources (`window`, a CSS selector) accept any event type the browser fires.",
            "Every example's `parsed` is the output of the Python port of the parser in "
            "scripts/vega_language.py.",
        ],
    }
    return {
        "meta": meta,
        "generalForm": form.group(1),
        "defaultSource": tok["VIEW"],
        "namedSources": named_sources,
        "markTypes": mark_types,
        "markEventTypes": dom_types,
        "specialEventTypes": [
            {"type": timer.group(1), "note": "fires every `throttle` milliseconds; source ignored"},
            {"type": resize.group(1), "source": resize.group(2), "since": resize.group(3)},
        ],
        "syntax": {
            "merge": tok["COMMA"],
            "sourceSeparator": tok["COLON"],
            "markname": tok["NAME"],
            "filter": tok["LBRACK"] + "expression" + tok["RBRACK"],
            "between": f"{tok['LBRACK']}start{tok['COMMA']} stop{tok['RBRACK']} {tok['GT']} stream",
            "timing": f"{tok['LBRACE']}throttle{tok['COMMA']}debounce{tok['RBRACE']}",
            "consume": consume,
        },
        "parserFields": fields,
        "objectProperties": props,
        "references": [{"name": name, "key": key} for name, key in refs],
        "examples": examples,
    }


# --- Python port of vega-event-selector (packages/vega-event-selector/src/event-selector.js) --

class SelectorError(ValueError):
    pass


def parse_selector(selector: str, source: str = "view", mark_types=None) -> list[dict]:
    """Parse an event selector string exactly as vega-event-selector does."""
    marks = set(mark_types or [])

    def find(s, i, end, push="", pop=""):
        count = 0
        while i < len(s):
            c = s[i]
            if not count and c == end:
                return i
            if pop and c in pop:
                count -= 1
            elif push and c in push:
                count += 1
            i += 1
        return i

    def merge(s):
        out, start, i = [], 0, 0
        while i < len(s):
            i = find(s, i, ",", "[{", "]}")
            out.append(s[start:i].strip())
            i += 1
            start = i
        if not out:
            raise SelectorError(f"Empty event selector: {s}")
        return out

    def sel(s):
        return between(s) if s[:1] == "[" else stream(s)

    def between(s):
        i = find(s, 1, "]", "[", "]")
        if i == len(s):
            raise SelectorError(f"Empty between selector: {s}")
        b = merge(s[1:i])
        if len(b) != 2:
            raise SelectorError(f"Between selector must have two elements: {s}")
        s = s[i + 1:].strip()
        if s[:1] != ">":
            raise SelectorError(f"Expected '>' after between selector: {s}")
        b = [sel(x) for x in b]
        st = sel(s[1:].strip())
        if "between" in st:
            return {"between": b, "stream": st}
        st["between"] = b
        return st

    def stream(s):
        st = {"source": source}
        parts = []
        throttle = [0, 0]
        markname = False
        n = len(s)
        i = 0
        filt = None
        if n and s[-1] == "}":
            i = s.rfind("{")
            if i < 0:
                raise SelectorError(f"Unmatched right brace: {s}")
            body = s[i + 1:n - 1]
            a = body.split(",")
            try:
                if not body or len(a) > 2:
                    raise ValueError
                throttle = [float(x) for x in a]
            except ValueError:
                raise SelectorError(f"Invalid throttle specification: {s}") from None
            s = s[:i].strip()
            n = len(s)
            i = 0
        if not n:
            raise SelectorError(f"Invalid event selector: {s!r}")
        if s[0] == "@":
            markname = True
            i = 1
        start = 0
        j = find(s, i, ":")
        if j < n:
            parts.append(s[start:j].strip())
            j += 1
            start = i = j
        i = find(s, i, "[")
        if i == n:
            parts.append(s[start:n].strip())
        else:
            parts.append(s[start:i].strip())
            filt = []
            i += 1
            start = i
            if start == n:
                raise SelectorError(f"Unmatched left bracket: {s}")
        while i < n:
            i = find(s, i, "]")
            if i == n:
                raise SelectorError(f"Unmatched left bracket: {s}")
            filt.append(s[start:i].strip())
            if i < n - 1:
                i += 1
                if s[i] != "[":
                    raise SelectorError(f"Expected left bracket: {s}")
            i += 1
            start = i
        if not parts or re.search(r"[\[\]{}]", parts[-1]):
            raise SelectorError(f"Invalid event selector: {s}")
        if len(parts) > 1:
            st["type"] = parts[1]
            if markname:
                st["markname"] = parts[0][1:]
            elif parts[0] in marks:
                st["marktype"] = parts[0]
            else:
                st["source"] = parts[0]
        else:
            st["type"] = parts[0]
        if st["type"].endswith("!"):
            st["consume"] = True
            st["type"] = st["type"][:-1]
        if filt is not None:
            st["filter"] = filt
        if throttle[0]:
            st["throttle"] = _num(throttle[0])
        if len(throttle) > 1 and throttle[1]:
            st["debounce"] = _num(throttle[1])
        return st

    return [sel(x) for x in merge(selector.strip())]


def _num(x: float):
    return int(x) if float(x).is_integer() else x


# --- expression call scanning (used by the repo checks) --------------------------------------

_STRING = re.compile(r"'(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\"|/(?:\\.|[^/\\\n])+/[gimsuy]*(?=\s*[,)])")
_CALL = re.compile(r"(?<![\w$.])([A-Za-z_$][\w$]*)\s*\(")


def called_functions(expr: str) -> list[str]:
    """Names called as functions in a Vega expression, ignoring string and regexp literals."""
    return _CALL.findall(_STRING.sub('""', expr))


if __name__ == "__main__":
    print(json.dumps({k: len(v) for k, v in expressions_catalog().items() if isinstance(v, list)}))
    print(json.dumps({k: len(v) if isinstance(v, list) else v
                      for k, v in event_streams_catalog().items() if k != "meta"}, indent=1)[:3000])

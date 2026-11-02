---
name: vega-feedback
description: "Use when this plugin proves wrong or incomplete while working in any project: a catalogued name or a card the engine contradicts, a missing property, an example that does not reproduce, a gap you had to measure or guess, or the user says \"report this to vega-for-agents\" / \"la ficha está mal\". Files one sanitized issue on its public repo, after showing it to the user."
---

# Report a finding back to vega-for-agents

The plugin is fixed in its own repository, never from the project you are in: not the installed
copy, not a local patch to a catalogue or a card. The way back is one issue on
`CSalcedoDataBI/vega-for-agents`, and the project carries on with its own workaround.

**That repository is public.** The issue is published the moment it is created and deleting it
does not unpublish it. Steps 3 and 5 are not optional.

## 1. Is it the plugin?

File only what is about the plugin's text or scripts: a name the catalogues list or omit, a card
under `reference/vega/`, an example, a skill step that was wrong or missing. A bug in the user's
spec, in Vega or Vega-Lite itself, in the Vega editor, in `vega-embed` or in Deneb is not a finding
for this repository.

## 2. Gather the evidence

- **The minimal standalone spec**: complete JSON, inline `values` data, no external files, URLs or
  signals from the user's project. Cut it down until it still reproduces the finding. A spec that
  needs the user's data is not evidence anyone else can rerun.
- **The renderer and version**: the Vega editor, the `vega-embed` version, or the Deneb version.
  Add the browser only when it matters.
- **What the plugin says**: find the claim in the installed plugin folder and give its path inside
  the plugin plus the plugin version (`version` in `.claude-plugin/plugin.json`). For a missing
  name, give the catalogue file and the key where it should be, and say what you expected.
- **What the engine did instead**: the exact error text, the console message, or a short
  description or image of the wrong render.

No spec because it is a gap or a wrong skill step? Say what you had to measure or guess.

## 3. Sanitize

Rewrite, do not redact with `***`:

- Field names and values become generic: `field1`, `category`, small made-up numbers. That
  includes names that only hint at the client or the business.
- Spec titles, descriptions, `usermeta`, file names, dataset names and signal names become generic
  too.
- No project, client or company names, no real values, no paths, hosts, ports, emails, tenant or
  workspace ids.

Then search the body file with your Grep tool for what slips through: `[A-Za-z]:\\`, `/Users/`,
`/home/`, `localhost:\d+`, `@[\w-]+\.\w+`, GUIDs (`[0-9a-f]{8}-[0-9a-f]{4}-`), and every name
seen in this session. Any hit: rewrite and search again.

## 4. Look for a duplicate

```bash
gh issue list -R CSalcedoDataBI/vega-for-agents --state all --search "<name, card or error text>"
```

Search again with the most specific term (an error text, a property name) when the first term is
common, like `mark` or `transform`. Then read the candidate with `gh issue view <n>`:

- **Same finding, new evidence** (another renderer version, another case it missed): a comment,
  `gh issue comment <n> -R CSalcedoDataBI/vega-for-agents --body-file <file>`, shown and approved
  exactly like an issue in step 5.
- **Same finding, nothing new:** post nothing. Give the user the link and stop.

## 5. Show it, then file it

Write the body to a temporary file with three sections — **What happens** (the claim, the minimal
spec, the engine result), **Why it matters** (what an agent would get wrong), **Done when** (a
checklist). Write it in the user's language; the maintainer reads English and Spanish.

Show the user the title and the full body, say it will be **public**, and wait for a yes. Then,
with the user's own GitHub CLI login:

```bash
gh issue create -R CSalcedoDataBI/vega-for-agents --title "<language>: <name or card>: <what is wrong, short>" --label bug --label documentation --body-file <file>
```

Labels: `bug` + `documentation` when a name, card or example says something the engine contradicts,
`documentation` alone when something is missing or unclear, `enhancement` for a new capability. No
`gh` or no login: give the user the title and body and the link
`https://github.com/CSalcedoDataBI/vega-for-agents/issues/new`.

## 6. Close

Give the user the issue link and the workaround the project is using meanwhile. Delete the
temporary body file.

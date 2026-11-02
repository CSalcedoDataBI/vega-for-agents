# Privacy policy — vega-for-agents

*Effective 2026-11-02. Maintainer: Cristóbal Salcedo — contacto@csalcedodatabi.com*

This policy covers the **vega-for-agents** plugin for Claude. The website
[csalcedodatabi.com](https://csalcedodatabi.com) has [its own policy](https://csalcedodatabi.com/privacidad).

## What the plugin collects

**Nothing.** The plugin is text: skills, reference pages and the generated catalogues. It ships
no hooks, no MCP server, no telemetry, no analytics and no background process. It has no
server of its own, so nothing you do with it reaches the maintainer — except an issue you
read and approve through `vega-feedback`, which is filed in public under your own GitHub account.

## What it reads and sends

| When | What happens | Where it goes |
|---|---|---|
| Any skill is used | Claude reads Markdown and JSON from the installed plugin folder | Nowhere: local reads only |
| You ask `vega-feedback` to report a wrong or missing name | Claude drafts an issue, rewrites anything from your spec or project into generic names, shows you the full text, and only after you say yes runs `gh issue create` with **your own** GitHub CLI login | `api.github.com`, a **public** issue on `CSalcedoDataBI/vega-for-agents`, under your GitHub account. It carries only the text you approved |

That issue is the plugin's only outbound action.

Your specs, data and conversations stay between you, Claude and the tools you already use.
The plugin keeps no copy of them and retains no data.

Maintainer scripts in this repository (for example the catalogue extractor under `scripts/`)
are **not** run by the plugin; they run only when a maintainer starts them by hand.

## Children

The plugin is a developer tool and is not directed at anyone under 18.

## Changes and contact

Changes to this policy are made in this file and recorded in the repository history.
Questions: contacto@csalcedodatabi.com.

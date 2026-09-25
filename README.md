# Design System Agent

A config-driven agent skill for generating and auditing UI designs. The skills hold fixed *process* (how to reason from a ticket to a layout, when to ask, when to reuse, when to audit); every project-specific value (colors, type, spacing, components) comes from a per-project design-system manifest.

## Folder structure

- **skills/** — the fixed logic (SKILL.md-style files): principles, the generation process, the audit rubric, and the mandatory human-facing report template.
- **schemas/** — the JSON Schemas defining every data contract that passes between steps.
- **tools/** — `export_claude_design.py`, which turns the manifest into a Claude Design System's `tokens.json` and checks it.
- **templates/** — `CLAUDE.md`, the required project file, with `{{…}}` placeholders the skill fills from your manifest.
- **examples/** — filled, working examples of every schema, all following one continuous scenario (ticket `DES-512`, a dashboard KPI summary) so you can trace one request through the whole pipeline.

## Platforms: Claude Code and Claude Design

The same manifest, skills and rubric run on both. `platform.targets` in the manifest says which; **`skills/platform-adapters.md`** maps every step to each platform.

| | Claude Code | Claude Design |
|---|---|---|
| Always-loaded context | `CLAUDE.md` | The default Design System's README (same template) |
| Tokens | Manifest values | Design System `tokens.json`, exported by `tools/export_claude_design.py` |
| Design drawn as | Code/markup | Design canvas artboards and clickable prototypes |
| Records (briefs, reports, index) | Repo files | A connected repo (recommended), or the design index as a Design System section |

To use Claude Design, set `platform.targets` to include `claude-design` and fill `color.resolved` with real color values, then export:

```
pip install pyyaml
python3 tools/export_claude_design.py design-system-manifest.yaml build/claude-design
```

It writes `project/tokens.json` in the Design System's format and checks roles without values, duplicate names, text below the legibility floor, and failing contrast pairs. See `examples/claude-design/project/tokens.json` for the Acme export.

## Required first: a project `CLAUDE.md`

Before the agent runs in your app repo, that repo needs a `CLAUDE.md` holding your design system's **tokens, brand rules, and critique criteria**. Claude Code loads it into every session, so every interaction follows the design system, even a one-line edit or a design question that never invokes the skill.

- **Template:** `templates/CLAUDE.md`. The skill fills it from your manifest. See `examples/CLAUDE.example.md` for the Acme version.
- **Version stamp:** its first line records the manifest version it was built from. The skill halts if the file is missing or the stamp doesn't match, and offers to generate or regenerate it.
- **Source of truth:** the manifest stays the full data; `CLAUDE.md` is the short, always-loaded summary. When the manifest changes, bump its version and regenerate `CLAUDE.md` in the same change.

## Pipeline order

1. **`schemas/ticket-brief.schema.json`** — structured extraction from a Jira ticket or PRD, including the `scopeTerms` and `surfaces` it touches. See `examples/ticket-brief.example.yaml` (ticket) and `examples/ticket-brief-prd.example.yaml` (PRD).
   - **Scope placement check** — before any design starts, the brief is compared against every project in the **`schemas/design-index.schema.json`** (example included) by shared terms, shared surfaces and shared priorities. Each required element is routed individually: to this project, as a revision of an existing design that already owns that surface, or here but reusing a related design's approved pattern. The result is a **`schemas/scope-overlap-report.schema.json`** — see `examples/scope-overlap-report.example.yaml`, where a PRD that looks like one new project turns out to be two revisions of existing designs.
2. **`schemas/design-system-manifest.schema.json`** — the project's design system as data (tokens, components, thresholds, policies). See `examples/design-system-manifest.example.yaml`. This is what makes the rest of the system generalizable to any design system — swap this file, same skills work elsewhere.
3. **`skills/design-principles.md`** — the fixed philosophy (simplicity, hierarchy, consistency, alignment, whitespace, mobile-first, motion, structural rationale) that generation and audit both answer to, plus two checkable sets of criteria: the **3-3-3 rule** (understood in 3 seconds, reached in 3 clicks, done in 3 minutes — walked for every core task and recorded as `glanceTest` / `taskPaths` in the design output) and **Wickens' 13 principles of display design** (perception, mental models, attention, memory).
4. **`skills/design-generation-skill.md`** — reads the brief + manifest, runs the reuse/similarity check against the component registry, files gap reports for anything missing, shapes layout/typography/color/motion from manifest tokens, and follows the Decision Protocol on consequential choices. Produces a `design-output` (schema + example included).
   - Along the way it may file a **`schemas/component-gap-report.schema.json`** (example included) for anything not in the registry, and — before that gap report's component can be approved for reuse — a **`schemas/component-verification-report.schema.json`** (two examples included: `StatTile` and `Button/icon-only`) confirming the new component is operational (every state implemented, accessible, token-compliant) and documenting *why* it was built that way.
5. **`skills/design-audit-rubric.md`** — runs automatically after every generation. 13 categories (including scope & cross-artifact integrity, the 3-3-3 usability rule, and Wickens' 13 display-design principles), `pass`/`minor-issues`/`major-issues`/`blocker` verdicts. `blocker` halts for a human; `major-issues` auto-revises and re-audits up to a configurable cap before escalating. Produces an **`schemas/audit-report.schema.json`** (example included).
6. **`skills/audit-presentation-template.md`** — the exact, fixed format audit findings are rendered in for a human (Phase 1 Critical / Phase 2 Refinement / Phase 3 Polish / Design System Updates Required / Implementation Notes). See `examples/audit-report-rendered.example.md` for what this looks like filled in.

7. **Design index update** (generation Step 12) — every artifact is registered with the exact versions it was built from. When one changes, its direct dependents are flagged `needs-review` (and projects sharing a pattern are flagged too); nothing is silently regenerated. See the flagged artifacts in `examples/design-index.example.yaml`.

## Still open

Jira ingestion (fetching a ticket automatically into a `ticket-brief`, e.g. via an Atlassian MCP connector) hasn't been built yet — right now a brief is assumed to already be structured, or extracted manually from raw ticket text per Step 1 of `design-generation-skill.md`.

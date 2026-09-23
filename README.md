# Design System Agent

A config-driven agent skill for generating and auditing UI designs. The skills hold fixed *process* (how to reason from a ticket to a layout, when to ask, when to reuse, when to audit); every project-specific value (colors, type, spacing, components) comes from a per-project design-system manifest.

## Folder structure

- **skills/** — the fixed logic (SKILL.md-style files): principles, the generation process, the audit rubric, and the mandatory human-facing report template.
- **schemas/** — the JSON Schemas defining every data contract that passes between steps.
- **examples/** — filled, working examples of every schema, all following one continuous scenario (ticket `DES-512`, a dashboard KPI summary) so you can trace one request through the whole pipeline.

## Pipeline order

1. **`schemas/ticket-brief.schema.json`** — structured extraction from a Jira ticket. See `examples/ticket-brief.example.yaml`.
2. **`schemas/design-system-manifest.schema.json`** — the project's design system as data (tokens, components, thresholds, policies). See `examples/design-system-manifest.example.yaml`. This is what makes the rest of the system generalizable to any design system — swap this file, same skills work elsewhere.
3. **`skills/design-principles.md`** — the fixed philosophy (simplicity, hierarchy, consistency, alignment, whitespace, mobile-first, motion, structural rationale) that generation and audit both answer to.
4. **`skills/design-generation-skill.md`** — reads the brief + manifest, runs the reuse/similarity check against the component registry, files gap reports for anything missing, shapes layout/typography/color/motion from manifest tokens, and follows the Decision Protocol on consequential choices. Produces a `design-output` (schema + example included).
   - Along the way it may file a **`schemas/component-gap-report.schema.json`** (example included) for anything not in the registry, and — before that gap report's component can be approved for reuse — a **`schemas/component-verification-report.schema.json`** (two examples included: `StatTile` and `Button/icon-only`) confirming the new component is operational (every state implemented, accessible, token-compliant) and documenting *why* it was built that way.
5. **`skills/design-audit-rubric.md`** — runs automatically after every generation. 10 categories, `pass`/`minor-issues`/`major-issues`/`blocker` verdicts. `blocker` halts for a human; `major-issues` auto-revises and re-audits up to a configurable cap before escalating. Produces an **`schemas/audit-report.schema.json`** (example included).
6. **`skills/audit-presentation-template.md`** — the exact, fixed format audit findings are rendered in for a human (Phase 1 Critical / Phase 2 Refinement / Phase 3 Polish / Design System Updates Required / Implementation Notes). See `examples/audit-report-rendered.example.md` for what this looks like filled in.

## Still open

Jira ingestion (fetching a ticket automatically into a `ticket-brief`, e.g. via an Atlassian MCP connector) hasn't been built yet — right now a brief is assumed to already be structured, or extracted manually from raw ticket text per Step 1 of `design-generation-skill.md`.

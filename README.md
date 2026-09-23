# Design System Agent

A config-driven agent skill for generating and auditing UI designs. The skill holds fixed *process* (how to reason from a ticket to a layout, when to ask, when to reuse, when to audit); every project-specific value (colors, type, spacing, components) comes from a per-project design-system manifest.

## Files

| File | Purpose |
|---|---|
| `design-generation-skill.md` | The generation skill: an 11-step process from ticket brief to design, ending in an automatic audit handoff. |
| `design-audit-rubric.md` | 10-category audit rubric with blocker / major / minor checks and the verdict-to-automation routing table. |
| `design-system-manifest.schema.json` | JSON Schema for a project's `design-system-manifest.yaml`: tokens, component registry, registry/similarity policy, automation and heuristic thresholds. |
| `component-verification-report.schema.json` | JSON Schema for the report that gates a proposed component moving to `approved`. |
| `component-verification-report.example.yaml` | Worked example: verifying a new `StatTile` component. |

## Pipeline

1. **Brief** – structure the ticket into ranked priorities, required elements and open questions; ask if anything is ambiguous.
2. **Manifest** – load and validate the project manifest; halt if none exists.
3. **Reuse check** – score each required element against approved components; reuse, extend with a variant, or file a gap report.
4. **Design** – information architecture, layout (mobile-first, on-grid), typography, color, motion and navigation, all from manifest tokens.
5. **Audit** – run the rubric automatically. `pass`/`minor-issues` go to human sign-off; `major-issues` auto-revise up to a cap; `blocker` stops and routes to a human.
6. **Registry growth** – new components need a verification report with `verdict: ready-for-implementation` before they become `approved` and reusable.

## Referenced but not yet included

The skill and rubric refer to these files, which aren't in the repo yet: `design-principles.md`, `ticket-brief.schema.json`, `audit-report.schema.json`, `audit-presentation-template.md`, `component-recommendation-principles.md`, plus schemas for `component-gap-report` and `design-output`.

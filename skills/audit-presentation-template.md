---
name: audit-presentation-template
description: Fixed rendering format for audit findings shown to a human. Populated from audit-report.schema.json data. The template structure below is exact — no deviations. What's fixed logic here is the mapping from our existing categories/severities to Phase 1/2/3; the template text itself is verbatim as specified.
---

# Audit Presentation Template

This governs *how audit results are shown to a human*. It does not change the underlying `overallVerdict` / auto-revise / blocker-escalation logic in `design-audit-rubric.md` — that machinery still runs exactly as before. This is the render step that happens whenever an audit report is surfaced to a person, whether that's a `pass`/`minor-issues` design going to final sign-off, or a `blocker` being routed for human review.

---

## The template (exact, no deviations)

```
DESIGN AUDIT RESULTS

Overall Assessment: [1–2 sentences on the current state of the design]

────────────────────────────────────────────

PHASE 1 — Critical (Visual hierarchy, usability, responsiveness, or consistency issues that actively hurt UX)

- [Screen/Component]: [What's wrong] → [What it should be] → [Why this matters]
- [Screen/Component]: [What's wrong] → [What it should be] → [Why this matters]

Review: [Why these are highest priority]

────────────────────────────────────────────

PHASE 2 — Refinement (Spacing, typography, color, alignment, iconography that elevate the experience)

- [Screen/Component]: [What's wrong] → [What it should be] → [Why this matters]
- [Screen/Component]: [What's wrong] → [What it should be] → [Why this matters]

Review: [Why this sequencing]

────────────────────────────────────────────

PHASE 3 — Polish (Micro-interactions, transitions, empty/loading/error states, dark mode, subtle details)

- [Screen/Component]: [What's wrong] → [What it should be] → [Why this matters]
- [Screen/Component]: [What's wrong] → [What it should be] → [Why this matters]

Review: [Why these are Phase 3 and expected cumulative impact]

────────────────────────────────────────────

DESIGN_SYSTEM UPDATES REQUIRED

- [New tokens, colors, spacing values, typography changes, or component additions needed]
- These must be approved and added to DESIGN_SYSTEM before implementation begins

────────────────────────────────────────────

IMPLEMENTATION NOTES FOR BUILD AGENT

- [Exact file, exact component, exact property, exact old value → exact new value]
- Written so a build agent can execute without design interpretation
- No ambiguity

BAD:  "Make the cards feel softer"
GOOD: "CardComponent border-radius: 8px → 12px per updated DESIGN_SYSTEM token border-radius-lg"

BAD:  "Improve the spacing"
GOOD: "DashboardHeader margin-bottom: 16px → 24px (DESIGN_SYSTEM spacing-lg)"

BAD:  "The button needs more contrast"
GOOD: "PrimaryButton background: #6B7280 → #2563EB (DESIGN_SYSTEM color-brand-primary).
       Contrast ratio with white text improves from 3.8:1 → 8.6:1 (WCAG AAA)"
```

---

## Populating it from `audit-report.schema.json`

Every finding in the machine report has `severity` (blocker/major/minor) and `category` — these drive the *automation* logic and stay unchanged. This template needs one more piece of information per finding that the automation logic doesn't need: **which phase it renders in.** That's a separate axis, computed by the mapping below rather than 1:1 with severity — a `minor` finding can still be Phase 1 if it's a usability issue, and a `major` finding can be Phase 3 if it's about a missing loading state.

### Category → Phase mapping (default)

| Category | Default phase | Reasoning |
|---|---|---|
| `accessibility` | **1** | Always usability-critical by definition. |
| `composition-and-density` | **1** | Unpaginated lists, overloaded input rows — directly hurts usability. |
| `layout-and-spatial-consistency` (major severity) | **1** | Broken responsiveness / inconsistent placement. |
| `layout-and-spatial-consistency` (minor severity) | **2** | Ad hoc grid usage that isn't broken, just imprecise. |
| `reuse-and-component-discipline` | **1** | Consistency issue by definition — also *always* additionally populates the `DESIGN_SYSTEM UPDATES REQUIRED` section (see below), regardless of phase. |
| `token-and-scale-consistency` | **2** | Matches Phase 2's own description (spacing/typography/color) almost exactly. |
| `navigation-color-and-motion-feedback` — navigation ties, hover/focus contrast | **1** | Discoverability and wayfinding are usability, not decoration. |
| `navigation-color-and-motion-feedback` — two-key-color discipline | **2** | Refines the experience; doesn't block task completion. |
| `simplicity-and-necessity` | **1** | Cognitive load and ticket-fit are usability concerns. |
| `interaction-behavior` | **3** | Matches Phase 3's own description (loading/error states, motion, micro-interactions) almost exactly. |
| `scope-and-artifact-integrity` | **1** | Parallel or drifting designs are a consistency failure across the whole product, not one screen. Stale-dependency findings name the upstream artifact that changed. |
| `three-three-three-usability` | **1** | If users can't understand, reach, or finish the task, nothing else matters. |
| `display-design-wickens` — principles 1–5, 8, 9, 11, 13 | **1** | Perception, attention, and memory failures make the screen hard to use, not just less polished. |
| `display-design-wickens` — principles 6, 7 | **2** | Graphics and motion that fight the user's model — refinement once the screen works. |
| `display-design-wickens` — principles 10, 12 | **3** | Extra channels and previews — polish that reduces errors at the margins. |
| `decision-protocol-compliance` | *(excluded from phases)* | This is a process finding about the agent's own behavior, not a visual/UX defect in the design itself. Surface it as a caveat in `Overall Assessment` instead of forcing it into a phase it doesn't belong in. |

A finding's own `severity` still determines ordering *within* a phase (blockers/majors listed before minors) and still drives whether the pipeline auto-revises or halts — the phase mapping only affects how it's grouped for human reading.

### `DESIGN_SYSTEM UPDATES REQUIRED` section

Populated directly from any `component-gap-report` entries tied to this audit (via `relatedGapReportId` on `reuse-and-component-discipline` findings), plus any `token-and-scale-consistency` finding whose fix requires a genuinely new token rather than correct use of an existing one. Each line names the new token/component and states it needs approval before implementation — this section is never silently pre-approved.

### `IMPLEMENTATION NOTES FOR BUILD AGENT` section

Requires the finding to carry enough structured detail to write the exact old→new line — see the `implementationNote` object added to the finding schema. **A finding without a populated `implementationNote` cannot be rendered into this section as-is** — if the audit step doesn't have an exact property/value, it must go back and get one before presenting to the human, rather than rendering a vague instruction like "make the cards feel softer."

---
name: design-audit-rubric
description: Fixed-logic audit principles the agent applies to any generated or existing design. Categories are universal (apply regardless of design system); pass/fail thresholds pull from the project's design-system-manifest.yaml where noted.
---

# Design Audit Rubric

Audits are run in one of two modes:
- **Post-generation** — immediately after the agent drafts a design from a ticket, before presenting it for approval.
- **Standalone** — against an existing design (pasted, screenshotted, or linked) that the agent did not create.

Each category below produces a `pass` / `minor-issues` / `major-issues` / `blocker` verdict (schema in `audit-report.schema.json`). A single `blocker` in any category fails the whole audit regardless of other scores.

---

## 1. Reuse & Component Discipline

*New category — this is the one renaissance-architecture doesn't cover, since it predates the manifest/registry system. It's the most important check for your stated goal of accumulating reusable components instead of one-offs.*

- [ ] **Blocker:** Design uses a component/variant with `status: proposed` or invents a new one WITHOUT an accompanying `component-gap-report` entry.
- [ ] **Blocker:** A `create-new` recommendation was made where the similarity engine (per `registryPolicy.similarityCheck`) found a candidate scoring ≥ `reuseThreshold` — i.e. the agent ignored its own reuse signal.
- [ ] **Major:** Design re-implements styling (colors, spacing, radii) inline instead of referencing an approved component that already encodes it.
- [ ] **Major:** `registryPolicy.onMissingComponent` / `onMissingVariant` policy was not respected (e.g. `propose-and-wait` configured but agent proceeded without pausing).
- [ ] **Minor:** A `reuse-nearest-approved` recommendation was made but the design doesn't actually show how the approved component is reconfigured to fit (no adaptation notes).
- [ ] **Blocker:** Two existing approved instances of the same component are already inconsistent with each other, and the design resolves this by introducing a third variation instead of flagging the inconsistency for review. *(Core design principle 3: flag it, don't invent a third variation.)*
- [ ] **Blocker:** A component/variant with a `create-new` or `extend-existing-variant` gap report has no linked `component-verification-report` with `verdict: ready-for-implementation`, when `registryPolicy.requireOperationalVerification` is true — a gap report alone does not authorize approval or safe reuse.

**Evidence required:** every non-approved component/variant used must cite a gap report ID.

---

## 2. Accessibility

*Directly from the manifest's `accessibility` block — thresholds are project-specific, the check itself is universal.*

- [ ] **Blocker:** Text/background contrast falls below `color.contrastStandard` (AA = 4.5:1 body text / 3:1 large text; AAA = 7:1 / 4.5:1).
- [ ] **Blocker:** Interactive targets smaller than `accessibility.minTouchTargetPx`.
- [ ] **Major:** No visible focus state on an interactive element, if `requireVisibleFocusStates` is true.
- [ ] **Major:** Non-semantic markup used where a semantic element exists (div-as-button, etc.), if `requireSemanticHtml` is true.
- [ ] **Minor:** Color is the only signal for a state (error/success) with no icon or text backup.

---

## 3. Token & Scale Consistency

*Checks the design actually used the manifest's data rather than approximating it.*

- [ ] **Blocker:** A spacing value appears that isn't in `spacing.scale` (or a documented multiple of `spacing.baseUnitPx`). *(Escalated from major — "no hardcoded values, ever" per core design principle 3.)*
- [ ] **Blocker:** A font size appears that isn't one of `typography.scale.steps`. *(Escalated from major, same reason.)*
- [ ] **Blocker:** A color appears that isn't a `color.neutrals` / `color.accents` role. *(Escalated from major, same reason.)*
- [ ] **Minor:** More than `typography.weights.length` distinct font weights used.
- [ ] **Minor:** A third typeface introduced beyond `typography.typefaces` (display/body/ui).
- [ ] **Major:** Heading and its readable subtext use the same font, weight, and size step — no visual hierarchy between them (violates `typography.roles.heading` vs `typography.roles.readableSubtext`).
- [ ] **Minor:** A field's label (something the user must fill in) is styled identically to nearby explanatory/readable text — the two must be distinguishable at a glance (violates `typography.roles.formLabel` vs `readableSubtext`).

---

## 4. Layout & Spatial Consistency

*Adapted from renaissance-architecture's "Spatial Consistency" and "Human-Legible Systems" principles, generalized from software architecture to layout structure.*

- [ ] **Major:** Layout breaks or reflows unpredictably between `layout.breakpoints` steps (no defined behavior at intermediate widths).
- [ ] **Major:** Component placement is inconsistent with itself across the same design (e.g. primary action bottom-right on one screen, top-left on another with no stated reason).
- [ ] **Minor:** Grid column usage doesn't reference `layout.gridColumns` — ad hoc widths instead of grid fractions.
- [ ] **Minor:** No stated behavior for what's bookmarkable/deep-linkable, for designs with navigable state (adapted from renaissance's "Predictable navigation").
- [ ] **Major:** Design shows evidence of being conceived desktop-first and scaled down, rather than mobile-first — e.g. touch targets or primary interactions not verified at the smallest `layout.breakpoints` step, or a hover-dependent interaction with no touch equivalent. *(Core design principle 6: mobile is the starting point, not an enhancement target.)*
- [ ] **Blocker:** An element's position deviates from the grid by more than `layout.alignmentTolerancePx` (default 0 — exact). *(Core design principle 4: "off by 1-2px is wrong," no exceptions — treated as a blocker, not a cosmetic minor.)*

---

## 5. Decision Protocol Compliance

*Directly from the bencium-controlled-ux-designer skill's core rule — this is what makes it "controlled" rather than autonomous.*

- [ ] **Blocker:** A consequential decision (color direction, layout paradigm, typography pairing) was applied without presenting alternatives, when `meta.decisionProtocol` is `always-ask`.
- [ ] **Major:** Alternatives were presented without trade-offs stated (just options, no "this costs X, gains Y").
- [ ] **Minor:** More than 3 alternatives presented for one decision (choice paralysis instead of a curated set).
- [ ] **Major:** A recommended or applied change has no stated structural rationale — hierarchy, consistency, contrast ratio, or a named token — and instead reads as a bare preference (e.g. "make this blue," "feels cleaner"). *(Core design principle 8: every change needs a design reason, not a preference. This is also what `implementationNote` in `audit-report.schema.json` exists to enforce.)*

---

## 6. Anti-Pattern Check

*Universal defaults plus project-specific bans from `meta.brandExclusions`.*

- [ ] **Major:** Design matches any entry in `meta.brandExclusions` verbatim or in obvious spirit (e.g. exclusion lists "glass morphism," design uses backdrop-blur cards).
- [ ] **Major:** Generic/templated pattern used where the ticket implied something distinctive was needed (adapted from renaissance's "Derivative Thinking" — "X but for Y" without asking if Y needs X).
- [ ] **Minor:** Feature/element added because "competitors have it" or "the pattern is common," with no stated reason tied to this ticket's actual need (renaissance's "Cargo Cult" check, applied to UI rather than architecture).

---

## 7. Simplicity & Necessity Check

*Pulled near-verbatim from renaissance-architecture's "First-Principles Check" and "Simplicity Check" — these principles are genuinely design-system-agnostic and apply as well to a layout as to a codebase.*

- [ ] **Major:** Complexity (extra states, nested interactions, nonstandard patterns) isn't tied to a measurable requirement in the ticket — "assumed" complexity rather than "earned" complexity.
- [ ] **Major:** A new team member / unfamiliar user couldn't understand the screen's purpose and primary action within a few seconds.
- [ ] **Minor:** The design could accomplish the ticket's actual goal with fewer components or screens than proposed.

**Ask directly, per renaissance-architecture:** *"What's the simplest version that solves the core problem?"* — flag if the design isn't that version without a documented reason.

---

## 8. Interaction Behavior Check

*Generalized from renaissance-architecture's UI/UX Philosophy section (Immediate Feedback, Visible State, Undo & Recovery, Respect Attention) — these are behavioral principles independent of any visual design system.*

- [ ] **Major:** No loading/pending state defined for an action that involves latency (network call, computation).
- [ ] **Major:** A destructive action (delete, irreversible change) has no confirmation or undo/recovery path.
- [ ] **Major:** System state (saving, syncing, errors) isn't visible to the user without digging.
- [ ] **Minor:** A modal/interruption is system-initiated rather than user-initiated, with no clear justification.
- [ ] **Minor:** Motion doesn't respect `motion.respectReducedMotion` when that flag is true.

---

## 9. Composition & Density

*Unifies several related heuristics under one principle: don't show more than a person can scan at once — chunk, paginate, or nest the rest. All thresholds pull from `compositionHeuristics`.*

- [ ] **Major:** A list longer than `compositionHeuristics.listPaginationThreshold` renders unpaginated (no pagination, chunking, or virtualized scroll with clear position feedback).
- [ ] **Major:** A form/input row exceeds `compositionHeuristics.maxInlineInputs` fields with no grouping, summarization, or deferral evaluated — and no documented reason all fields are needed at once.
- [ ] **Major:** A primary/landing screen exposes individual item specs/details inline rather than title + main options, when `requireProgressiveDisclosure` is true — details belong on a drill-down.
- [ ] **Blocker:** A major layout or content decision has no traceable link back to a stated priority in the source ticket, when `requireTicketPriorityTraceability` is true — i.e. the design solved a problem the ticket didn't ask about, or missed the one it did.
- [ ] **Minor:** Progressive disclosure was applied somewhere but inconsistently (e.g. one list paginates, a structurally identical list elsewhere doesn't).

---

## 10. Navigation, Color Discipline & Motion Feedback

*Covers how the design signals relationships and interactivity — three related but distinct behaviors bundled here since they're all about the user always knowing "where am I, what's active, what's connected."*

**Navigational ties** (`navigationHeuristics`)
- [ ] **Major:** A drill-down/detail view has no back button, breadcrumb, or shortcut back to its parent, when `requireNavigationalTies` is true.
- [ ] **Minor:** Navigation depth exceeds `breadcrumbThresholdDepth` with only a back button and no breadcrumb trail — fine at shallow depth, insufficient deeper in.

**Interactive state contrast** (`color.interactionStates`)
- [ ] **Major:** A hoverable/interactive element doesn't change color (not just opacity/shadow) on hover, relative to both its own resting state and the surrounding page.
- [ ] **Major:** No visible focus color defined or applied for keyboard navigation, independent of hover.

**Two-key-color discipline** (`color.usagePolicy`)
- [ ] **Major:** The secondary accent color appears more than `maxSimultaneousSecondaryAccents` times on screen at once — dilutes it from "the other choice" into decoration.
- [ ] **Minor:** Primary and secondary accent roles are used inconsistently across the design (e.g. secondary accent means "danger" on one screen, "alternate action" on another).
- [ ] **Blocker:** More than `color.usagePolicy.maxPrimaryActionsPerScreen` (default 1) elements are styled with primary-accent weight on one screen — competing primary actions instead of one unmissable action and supporting secondaries. *(Core design principle 2: if everything is bold, nothing is bold.)*

**Motion for wait states & visualization** (`motionUsagePolicy`)
- [ ] **Major:** An async wait has no loading animation, when `requireLoadingAnimation` is true (this overlaps with, and reinforces, category 8's loading-state check).
- [ ] **Minor:** A chart/visualization appears instantly with no entrance animation, when `requireDataVizAnimation` is true and `motion.respectReducedMotion` allows it.

---

## 11. Scope & Cross-Artifact Integrity

*The design-level counterpart of category 1: category 1 stops duplicate components, this stops duplicate or drifting designs. Thresholds and policy from `scopePolicy`; data from the design index and the scope-overlap-report.*

- [ ] **Blocker:** No `scope-overlap-report` exists for the brief, when `scopePolicy.requireScopeCheck` is true — the design was started without checking whether another project already owns the work.
- [ ] **Blocker:** The design builds, as new, an element the scope report routed to `existing-project` (or a whole brief classified `belongs-to-existing`) with no recorded `humanDecision` overriding it — a parallel design of work another project owns.
- [ ] **Major:** `scopePolicy.onOverlap` was not respected (e.g. `ask` configured but the agent designed before the human accepted or overrode the recommendation).
- [ ] **Major:** A decision listed in `reusedDecisions` was re-decided differently without a Decision Protocol entry explaining why, and without the sharing project being flagged — two designs that share a pattern now drift apart.
- [ ] **Major:** The design output depends on an upstream artifact (brief, scope report, verification report) whose current version is newer than the one recorded in `dependsOn` — it was built from stale input.
- [ ] **Minor:** Candidate scores in the scope report have no `evidence`, or the brief's `scopeTerms` are generic ("page", "button", "user") enough to make the overlap check meaningless.
- [ ] **Minor:** The design index wasn't updated after the run (new artifacts unregistered, or relationships from the scope report recorded on only one side).

**Evidence required:** the `scopeOverlapReportRef` on the design output, and for every `existing-project` route, either the element's absence from this design or a `humanDecision` override.

---

## Scoring & Verdict

| Verdict | Condition | Automation behavior |
|---|---|---|
| `pass` | Zero blockers, zero majors, ≤2 minors total | Proceeds to human sign-off (decision protocol step) |
| `minor-issues` | Zero blockers, zero majors, 3+ minors | Proceeds to human sign-off; minors logged as non-blocking notes |
| `major-issues` | Zero blockers, 1+ majors | **Hard stop on forward progress.** Auto-loops back to generation with the cited findings, up to `automation.maxAutoReviseAttempts`. Re-audited each attempt. If still `major-issues` after the cap, escalates to `blocker` and routes to a human. |
| `blocker` | Any blocker in any category | **Hard stop, immediate human routing — never auto-retried.** These are cases (e.g. an invented component bypassing the gap-report process, a decision-protocol violation) where letting the agent try to self-correct risks compounding the problem rather than fixing it. |

This audit runs **automatically immediately after every generation**, before a design is ever surfaced for the human decision-protocol approval described in category 5 — approval only happens on a `pass` or `minor-issues` verdict.

---

## Quick Reference

| Category | Source | Manifest-dependent? |
|---|---|---|
| Reuse & Component Discipline | New (registry system) | Yes — `components[]`, `registryPolicy` |
| Accessibility | bencium skill + WCAG | Yes — `accessibility` |
| Token & Scale Consistency | bencium skill | Yes — `color`, `typography`, `spacing` |
| Layout & Spatial Consistency | renaissance-architecture | Yes — `layout` |
| Decision Protocol Compliance | bencium skill | Yes — `meta.decisionProtocol` |
| Anti-Pattern Check | Both, generalized | Partially — `meta.brandExclusions` |
| Simplicity & Necessity | renaissance-architecture | No — universal |
| Interaction Behavior | renaissance-architecture | Partially — `motion.respectReducedMotion` |
| Composition & Density | New | Yes — `compositionHeuristics` |
| Navigation, Color Discipline & Motion Feedback | New | Yes — `navigationHeuristics`, `color.interactionStates`, `color.usagePolicy`, `motionUsagePolicy` |
| Scope & Cross-Artifact Integrity | New (design index) | Yes — `scopePolicy`, design index |

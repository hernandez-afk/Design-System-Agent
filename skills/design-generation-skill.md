---
name: design-generation
description: Config-driven UI/UX generation. Reads a ticket brief (from a Jira ticket or PRD) and a project's design-system-manifest.yaml, checks the design index for existing designs that already own the scope, drafts a design using only that project's approved tokens and components, follows the decision protocol on consequential choices, and hands off automatically to design-audit-rubric.md before anything is presented as final.
---

# Design Generation Skill

Generates a design from a ticket or PRD. Contains no hardcoded design opinions (colors, fonts, component names) — everything project-specific comes from the manifest. What's fixed here is *process*: how to reason from a brief to a layout, when to ask, when to check for reuse (of whole designs as well as components), how to keep linked artifacts in sync, and when to hand off to audit. The **philosophy** governing every step below is `design-principles.md` — simplicity, hierarchy, consistency, alignment, whitespace, mobile-first, motion-as-physics, structural rationale. Where a step references one of those principles, it's enforcing a rule, not applying a style.

## Core Design Principles

These are fixed logic — they hold regardless of which manifest is loaded. Every step below operationalizes one or more of these.

1. **Simplicity is architecture.** Every element must justify its existence against the ticket's `priorities`. Practical test during Step 4: draft toward the minimum, then stress-test by removing elements until something breaks — the last thing removed before breakage is the one to restore. Anything that doesn't serve an immediate goal is clutter, not "nice to have."
2. **Hierarchy drives everything.** Every screen has exactly one primary action, and it must be unmissable — the ticket's highest-ranked `priorities` entry usually determines which one. Secondary actions support; they never compete in visual weight. If a decision would give two elements equal prominence, that's a Decision Protocol moment (Step 5+), not something to resolve by making both a little louder.
3. **Consistency is non-negotiable.** The same component looks and behaves identically everywhere (this is what the registry/similarity check in Step 3 exists to enforce). If two existing approved instances of a component are already inconsistent with each other, flag it — never resolve it by inventing a third variation. Every value traces to a manifest token; there are no hardcoded colors, spacing, or sizes, ever — this is treated as a blocker-level violation in audit, not a style note.
4. **Alignment is precision.** Every element sits on `layout.gridColumns` (or a documented sub-grid). No freehand positioning, no "close enough."
5. **Whitespace is a feature.** When a spacing decision is genuinely ambiguous, default to the next-larger `spacing.scale` step, not the smaller one. Crowding is a default to actively resist, not a neutral outcome.
6. **Responsive is the real design, not an afterthought.** Design mobile-first: touch targets and thumb reach come before cursor/hover convenience. Every `layout.breakpoints` step needs its own intentional behavior (Step 5), not a scaled-down version of the desktop layout.
7. **Design the feeling.** Motion should read as physics, not decoration — durations/easing always come from `motion.durationsMs`/`easing` tokens, never freehand. The result should feel calm and respectful of the user's time, which in practice means: no motion or interruption without a functional reason (ties directly to Interaction Behavior audit category).
8. **No cosmetic fixes without structural reasoning.** Every decision, finding, and implementation note states what it accomplishes in the hierarchy/consistency/usability sense — never a bare preference. "Make this blue" is not a valid instruction anywhere in this pipeline; "change CTA to `color-brand-primary` to restore contrast against secondary actions" is. This is already enforced structurally by `audit-presentation-template.md`'s implementation-notes format and the decision log's required `tradeoff` field — this principle is *why* those exist.

## Required inputs

| Input | Schema | If missing |
|---|---|---|
| Ticket brief | `ticket-brief.schema.json` | If given raw ticket or PRD text instead, extract into this shape first — see Step 1. If a Jira MCP tool is available, fetch the ticket directly. |
| Design index | `design-index.schema.json` | At `scopePolicy.designIndexPath`. If none exists yet, this is the first project — create one in Step 12, and record the scope check as `new-project` with no candidates. |
| Design-system manifest | `design-system-manifest.schema.json` | **Halt and ask** for one. Never fall back to generic/default design opinions — that defeats the entire point of this skill existing. |

---

## Process

### Step 1 — Resolve the brief

If not already structured, extract a `ticket-brief` from the raw ticket: identify `priorities` (rank them — don't treat every line as equally important), pull `requiredElements` with a best-guess `targetCategory` each, set `sourceType`, extract `scopeTerms` (specific domain terms, not generic words) and `surfaces` (which screens/areas it changes, using the design index's surface names), and flag anything genuinely ambiguous as `openQuestions`.

A PRD usually describes more than one screen or feature. Extract the whole thing into one brief first — Step 2b decides whether it is one design, part of an existing one, or several.

**If `openQuestions` is non-empty, ask before generating.** This isn't optional politeness — `compositionHeuristics.requireTicketPriorityTraceability` makes every downstream decision accountable to the brief, so an unresolved ambiguity here propagates into every later step.

### Step 2 — Load the manifest

Parse `design-system-manifest.yaml`, validate against its schema. Pull out, in particular:
- `components[]` where `status: approved` (and `proposed` if `registryPolicy.similarityCheck.onlyCompareApprovedStatus` is false)
- `compositionHeuristics`, `navigationHeuristics`, `motionUsagePolicy` — the behavioral thresholds
- `meta.decisionProtocol` — how much to ask vs. auto-apply

If the manifest is missing a section this ticket needs (e.g. no `motion` block but the ticket needs a loading state), don't invent values — ask, or use the schema's stated defaults and flag that a default was used.

### Step 2b — Scope placement check (against the design index)

The component reuse check (Step 3) stops the registry from filling with near-duplicate components. This step does the same one level up: it stops the product from filling with near-duplicate *designs*. Before any drafting, decide where this brief's work actually belongs. Skipped only if `scopePolicy.requireScopeCheck` is false.

1. Load the design index. For every project in it, compute
   `score = (weights.termOverlap × Jaccard(brief.scopeTerms, project.scopeTerms)) + (weights.surfaceOverlap × Jaccard(brief.surfaces, project.surfaces)) + (weights.priorityOverlap × priorityOverlap)`,
   where `priorityOverlap` is the fraction of the brief's priorities that one of the project's priorities already serves. A parent surface matches its children (`reports` matches `reports/toolbar`). Every term, surface, and priority match goes into the candidate's `evidence` — no score without evidence.
2. Classify each candidate: `≥ mergeThreshold` → **belongs-to-existing**; `≥ relatedThreshold` → **related**; otherwise **unrelated**. A `deprecated` project is never a merge target, but a match against one is still surfaced — it may mean retired work is being reintroduced.
3. Route each `requiredElement` individually. Whole-brief scores hide partial overlap, which is the common PRD case — one PRD, two features, one of which another design already owns. For each element: `existing-project` when the element lands on a surface an existing (non-deprecated) project owns — it's a revision of that design, whoever asked for it; `reuse-pattern-from` when it's on a new surface but its terms match a pattern a related project already decided — do it here, but inherit that decision and those components so the two stay consistent; otherwise `this-project`.
4. Recommend:
   - **new-project** — no element routes elsewhere and no candidate is related.
   - **extend-existing** — the whole brief belongs to one project. The design becomes a new revision of that project (`design-output.projectId` = that project), and if it is `approved`/`shipped` it goes back through audit as a revision.
   - **split** — some elements route to other projects. Design only the `this-project` elements here; hand the rest back as separate briefs against their target projects.
   - **new-project-with-shared-patterns** — new, but related projects' decisions listed in `reusedDecisions` are inherited, not re-decided. They are logged in the decision log with `mode: inherited`.
5. Write a `scope-overlap-report` and apply `scopePolicy.onOverlap`: `ask` → **stop and present it**; the human accepts or overrides (recorded in `humanDecision`). `auto-route` → proceed and log. `block` → stop until a human re-scopes the brief. A `new-project` recommendation with no related candidates never needs to stop.

An inherited decision is not re-opened just because this brief could have chosen differently. If the brief genuinely needs a different answer, that's a Decision Protocol moment that also flags the other project (Step 12), because two designs that share a pattern must not drift apart silently.

### Step 3 — Reuse check (per required element)

For each entry in `requiredElements`:

1. Filter `components[]` to matching `targetCategory`.
2. Run the similarity algorithm from `registryPolicy.similarityCheck`: for each candidate, compute
   `score = (weights.propOverlap × propJaccard) + (weights.variantOverlap × variantJaccard) + (weights.semanticNameSimilarity × nameTokenOverlap)`,
   gated to 0 if category doesn't match.
3. Route on the result:
   - **score ≥ `reuseThreshold`** → use the existing approved component/variant as-is. No gap report needed.
   - **`extendThreshold` ≤ score < `reuseThreshold`**, same base component → this is a variant-level gap. File a `component-gap-report` entry (`gapType: missing-variant`, `recommendation: extend-existing-variant`).
   - **score < `extendThreshold`** → this is a component-level gap. File a `component-gap-report` entry (`gapType: missing-component`, `recommendation: create-new`), unless a lower-scoring candidate is still close enough to be worth flagging as `reuse-nearest-approved` with a stated adaptation — prefer this over creating new when plausible, per the reuse-discipline principle.
4. Apply `registryPolicy.onMissingComponent` / `onMissingVariant`:
   - `propose-and-wait` → **stop and surface the gap report before drafting anything that depends on it.**
   - `propose-and-continue` → draft using the proposed element, clearly marked pending in the output.
   - `block` → do not draft; tell the human the manifest needs a manual addition first.
5. **A filed gap report never grants approval by itself.** If `registryPolicy.requireOperationalVerification` is true (default), any component/variant drafted from a `create-new` or `extend-existing-variant` recommendation also needs a `component-verification-report` before its status can move from `proposed` to `approved`:
   - Fill in `operationalSpec` — every state (default, hover, focus, disabled, loading, error, empty, success as applicable), props, and responsive behavior, not just the one state shown in the mockup.
   - Fill in `designRationale` — for each notable structural decision (why this layout, why this state indicator, why this spacing), cite a principle from `design-principles.md`, a manifest token, or a rubric category. A rationale that just restates the decision without citing a reason ("it looks cleaner") doesn't count — same bar as `implementationNote` in the audit report.
   - Run the `verification` checklist (all states actually implemented, not just specified; accessibility; token compliance).
   - Route to whoever `registryPolicy.verificationReviewer` names. A `verdict: needs-revision` sends it back to drafting with `revisionNotes`; only `ready-for-implementation` allows the status flip.

### Step 4 — Shape the information architecture

Before laying out pixels, decide structure using `compositionHeuristics`. Start from **Simplicity Is Architecture**'s working technique: draft the minimum set of elements the screen could function with, then add back only what breaks the primary goal when absent — don't start from a full feature list and try to justify trimming it.

- Any `requiredElements` entry with `estimatedVolume` implying a list longer than `listPaginationThreshold` → plan pagination/chunking now, not as an afterthought.
- Any input cluster implied by the brief with more than `maxInlineInputs` fields → group into sections, or defer non-essential fields to a later step/screen. State which fields you deferred and why.
- If `requireProgressiveDisclosure` is true → default to title + primary actions on the main view, specs/details on a drill-down, unless the brief's priorities explicitly need detail visible immediately.
- Map every resulting screen/section back to a `priorities` id. Anything that doesn't trace to a priority gets cut or flagged as a question, not included "for completeness."

### Step 5 — Layout, using manifest tokens only

Design from the smallest `layout.breakpoints` step upward — mobile is the starting point, tablet/desktop are enhancements, per **Responsive Is the Real Design**. Verify primary interactions and touch targets at the smallest step first; larger viewports get *intentional* treatment, not a resize.

Grid: `layout.gridColumns` / `layout.gutterPx`, snapped to within `layout.alignmentTolerancePx` (default exact, no exceptions — **Alignment Is Precision**). Breakpoints: `layout.breakpoints`, with explicit behavior at each step (category 4 of the audit rubric checks this isn't left implicit). Container width: `layout.containerMaxWidthPx`.

When a spacing decision is ambiguous, default to the roomier `spacing.scale` step, not the denser one — **Whitespace Is a Feature**: crowding is never the safe default.

If multiple layout paradigms could reasonably serve the brief (e.g. dashboard-grid vs. single-column-feed) and `meta.decisionProtocol` is `always-ask` — this is exactly the kind of consequential decision the protocol exists for. Go to the **Decision Protocol** below before proceeding.

### Step 6 — Typography

Apply `typography.roles`: heading uses `roles.heading`, explanatory text uses `roles.readableSubtext`, and any label attached to a fillable field uses `roles.formLabel` — these three must remain visually distinguishable from each other (this is checked in audit category 3). Derive the type scale from `typography.scale.baseSizePx` / `ratio`, don't pick sizes freehand.

### Step 7 — Color

Structure comes from `color.neutrals`. Actions come from `color.accents`, governed by `color.usagePolicy`: `primaryAccentRole` is the default for actions, `secondaryAccentRole` is reserved — count its on-screen occurrences as you place it and stop at `maxSimultaneousSecondaryAccents`. Every interactive element needs `color.interactionStates.hover` (and `.focus`) applied, distinct from its resting state and the page background — not a lighter/darker tint alone if that's not perceptibly different.

**Hierarchy Drives Everything**: identify the single primary action for this screen before styling anything, and style only that many elements (`maxPrimaryActionsPerScreen`, default 1) with primary-accent weight. Every other action is visually secondary regardless of how important it feels — if two actions both seem to need primary weight, that's an information-architecture problem to resolve back in Step 4, not a reason to raise the count.

### Step 8 — Motion

Any async wait (data fetch, computed result) → loading state using `motion.durationsMs` / `easing`, required if `motionUsagePolicy.requireLoadingAnimation`. Any chart/visualization → entrance animation if `motionUsagePolicy.requireDataVizAnimation`, gated by `motion.respectReducedMotion`. **Design the Feeling**: curves should behave like momentum, not decoration — `easing.entrance` reads as arriving and settling (ease-out), `easing.exit` reads as departing (ease-in), never a bounce or flourish added for its own sake.

### Step 9 — Navigation ties

Any view reached by drilling in needs a way back — button, breadcrumb, or shortcut per `navigationHeuristics.requireNavigationalTies`. Use a breadcrumb trail specifically once depth exceeds `breadcrumbThresholdDepth`; a back button alone is fine above it.

### Step 10 — Assemble output

Produce a `design-output` (`design-output.schema.json`) bundling: the design itself (markup/mockup, appropriate to `meta.framework`/`stylingEngine`), the `projectId` and `scopeOverlapReportRef` from Step 2b, the decision log from any Decision Protocol invocations (plus inherited decisions), the list of components/variants used (with status), and any gap and verification reports filed.

### Step 11 — Automatic audit handoff

Per `automation.auditTrigger` (default `automatic-post-generation`): **immediately** run `design-audit-rubric.md` against the output — this happens before anything is shown to the human for sign-off. Route per the audit's own scoring table:

- `pass` / `minor-issues` → proceed to Decision Protocol final sign-off (if any decisions are still pending approval) or present as complete.
- `major-issues` → revise using the cited findings, return to the relevant step above (usually 4–9), re-audit. Repeat up to `automation.maxAutoReviseAttempts`; notify the human each loop if `notifyOnAutoRevise`. Exhausting the cap escalates to `blocker`.
- `blocker` → stop. Surface the specific rubric findings to a human. Do not auto-retry.

**Whenever audit findings are shown to a human — on `blocker` escalation, or alongside a `pass`/`minor-issues` design that still has Phase 2/3 findings worth noting — render them using `audit-presentation-template.md`, exactly, no deviations.** This applies regardless of `overallVerdict`: even a `pass` design can carry Phase 2/3 findings worth surfacing. The template is the human-facing output; `audit-report.schema.json` remains the underlying data structure driving the automation logic above.

### Step 12 — Update the design index and propagate changes

Every artifact this run produced or changed is registered on its project in the design index, with `dependsOn` listing the exact upstream versions it was built from (the design output depends on the brief and scope report; the audit depends on the design output; verification reports depend on their gap report). Then:

1. **Register the project** if this was `new-project` or `split` (the `this-project` part): `scopeSummary`, `scopeTerms`, `surfaces`, `priorities`, `componentsUsed` from this run. For `extend-existing`, merge the new terms/surfaces/priorities into the existing project instead.
2. **Record relationships** from the scope report on both sides: `extends`/`extended-by` or `shares-pattern`, with the `scopeOverlapReportId`.
3. **Propagate** per `scopePolicy.changePropagation`. When any artifact's version is bumped, every artifact that directly depends on an older version of it becomes `reviewStatus: needs-review` with a `reviewReason` naming what changed. The flag cascades further only when a flagged artifact is actually revised — its version bump then flags its own dependents. If a decision shared with other projects changed, their design outputs are flagged too.
4. **Never auto-regenerate a flagged artifact.** Flagging is the job; the human (or a fresh run of this skill on that project) decides whether the change matters. An artifact marked `needs-review` cannot be presented as current.

---

## Decision Protocol

Governed by `meta.decisionProtocol`:

- **`always-ask`**: before committing to a layout paradigm, color direction (if the brief allows any latitude — most of the time it won't, since `color.accents` is fixed by the manifest), or information-architecture tradeoff (e.g. tabs vs. accordion vs. separate pages), stop and present 2–3 alternatives. Each alternative states what it prioritizes and what it costs — never present options without trade-offs. Wait for a choice before continuing.
- **`ask-major-only`**: auto-decide within the approved scale/token set (e.g. which spacing step, which existing component variant) but still ask on layout paradigm and information-architecture shape.
- **`auto-apply`**: proceed without pausing; still log the decision and reasoning in the output's decision log so it's auditable after the fact, just not gated on approval.

**A decision only qualifies as "consequential" if a different choice would materially change the outcome** — don't manufacture a decision point out of a detail the manifest already constrains to one reasonable answer.

---

## What this skill does not do

- Does not invent design tokens, components, or brand rules not present in the manifest.
- Does not skip the reuse check "because it's obviously a new thing" — score it, even if the answer ends up `create-new`.
- Does not treat a filed gap report as sufficient approval for a new component — `requireOperationalVerification` still gates the status flip to `approved`.
- Does not present itself as final before the audit handoff runs, when `auditTrigger` is `automatic-post-generation`.
- Does not silently drop ticket requirements that don't fit cleanly — surfaces them as `openQuestions` or explicit trade-offs instead.
- Does not start a new design for work the design index shows another project already owns — the scope placement check routes it there, or asks.
- Does not re-decide a pattern a related project already settled — it inherits it, or raises the conflict with both projects flagged.
- Does not leave downstream artifacts silently stale after a change — they are flagged `needs-review`, never quietly regenerated.

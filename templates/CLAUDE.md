<!-- design-system-manifest: {{meta.name}} v{{meta.version}} -->
<!-- Generated from design-system-manifest.yaml by the design-generation skill.
     Regenerate it whenever the manifest's version changes; the skill refuses to run while the versions differ.
     The manifest is the source of truth. This file is the always-loaded summary.
     In Claude Design, this same content is the Design System's project/README.md (see skills/platform-adapters.md). -->

# Design system: {{meta.name}}

Every UI change in this repo follows these rules, including quick edits that don't run the full design agent. The full data (every token, component, variant and threshold) is in `{{manifestPath}}`. For new screens or features, use the **design-generation** skill.

## Tokens

Use only these values. Never hard-code a color, spacing, size, radius or duration.

**Color roles**
- Neutrals: background `{{color.neutrals.background}}`, surface `{{color.neutrals.surface}}`, border `{{color.neutrals.border}}`, text `{{color.neutrals.textPrimary}}`, muted text `{{color.neutrals.textSecondary}}`
- Accents: primary `{{color.accents.primary}}` (text on it: `{{color.accents.onPrimary}}`), secondary `{{color.accents.secondary}}` (at most {{color.usagePolicy.maxSimultaneousSecondaryAccents}} on screen at once)
- Status: success `{{color.accents.success}}`, warning `{{color.accents.warning}}`, error `{{color.accents.error}}`, info `{{color.accents.info}}`
- Interaction: hover `{{color.interactionStates.hover}}`, active `{{color.interactionStates.active}}`, focus `{{color.interactionStates.focus}}`
- Contrast: {{color.contrastStandard}}

**Typography**
- Display `{{typography.typefaces.display}}`, body `{{typography.typefaces.body}}`, UI `{{typography.typefaces.ui}}`; weights {{typography.weights}}
- Scale: base {{typography.scale.baseSizePx}}px × {{typography.scale.ratio}}, steps {{typography.scale.steps}}; line height {{typography.lineHeightRatio}}
- Roles: {{typography.roles — one line each: heading, readable subtext, form label, and how they differ}}

**Spacing & layout**
- Spacing scale (px): {{spacing.scale}}; base unit {{spacing.baseUnitPx}}px
- Radius: {{radius.tokens — name px (usage), one per item}}
- Grid: {{layout.gridColumns}} columns, {{layout.gutterPx}}px gutter, max width {{layout.containerMaxWidthPx}}px, alignment tolerance {{layout.alignmentTolerancePx}}px
- Breakpoints (design mobile first): {{layout.breakpoints}}

**Motion**
- Durations: micro {{motion.durationsMs.micro}}ms, state {{motion.durationsMs.state}}ms, page {{motion.durationsMs.page}}ms
- Easing: entrance `{{motion.easing.entrance}}`, exit `{{motion.easing.exit}}`, transition `{{motion.easing.transition}}`; respect reduced motion: {{motion.respectReducedMotion}}

**Components.** Reuse these before building anything new:
{{one line per approved component: Name (import path): approved variants; list proposed variants separately as "pending review — don't reuse"}}

## Brand rules

- Never: {{meta.brandExclusions, one per line}}
- Icons: {{icons.library}} only
- Decisions: `{{meta.decisionProtocol}}`. {{one line on what that means: always-ask = offer 2–3 options with trade-offs before any layout, color or structure decision}}
- One primary action per screen. Secondary actions never get primary-accent styling.
- New components or variants go through a gap report and a verification report. Never invent one inline.

## The design harness

Every design goes through the same loop, with a gate at each stage: brief → scope → flow → design → audit → approval → build → verify (`HARNESS.md`). `python3 .claude/design-agent/tools/harness.py status` shows where each design is; `next --project <ID>` says what to do.

## New pages

Start from a page brief (`templates/page-brief.md`): purpose, ranked goals, tasks with where they start, content with amounts, states, and testable acceptance criteria. Check it with `python3 .claude/design-agent/tools/brief_lint.py <brief>`. The design agent optimizes it to fit this design system, and shows every change for approval before designing. It then maps the user flow: how users get to the page and where they go next. A new link on another design's page is that design's change: it's proposed to its owner, never edited in quietly.

## Working on existing UI

- **Before changing UI code, know which design owns it.** Run `python3 .claude/design-agent/tools/design_context.py <file>`, or rely on the hook, which shows it on the first edit. Follow that design's decisions and components.
- **Changing a decision is a design change, not a code change.** If your edit would contradict a decision (a different filter pattern, a new layout), stop and raise it. Don't just edit.
- **Designs that share a pattern stay the same.** If the design context says it shares a pattern with another design, change both or neither.
- **UI that no design owns needs a scope check before it ships.** It may belong to an existing design.
- **Off-token values get sent back.** The token lint runs after every edit. Replace the value with a token; don't add it to the allow-list to get past the check.

## Critique criteria

Use these whenever you review, critique or change a design, not only in formal audits.

**Principles** (full text in `design-principles.md`): simplicity is architecture · hierarchy drives everything · consistency is non-negotiable · alignment is precision · whitespace is a feature · responsive is the real design · design the feeling · no cosmetic fixes without structural reasoning.

**3-3-3 rule**, for every core task:
- understood in {{usabilityHeuristics.threeThreeThree.glanceSeconds}} s at `{{usabilityHeuristics.threeThreeThree.glanceBreakpoint}}`
- reached in ≤ {{usabilityHeuristics.threeThreeThree.maxClicksToCoreTask}} clicks
- finished in ≤ {{usabilityHeuristics.threeThreeThree.maxCoreTaskMinutes}} min

Never meet the click limit by cramming.

**Wickens' 13 display principles:**
- Perception: legible (≥ {{usabilityHeuristics.displayDesign.minReadableTextPx}}px) · no more than {{usabilityHeuristics.displayDesign.maxAbsoluteJudgmentLevels}} unlabeled levels · follow convention · two cues for critical states · similar-looking means similar
- Mental model: pictorial realism · the moving part
- Attention: low access cost · related info close together · multiple channels
- Memory: show, don't make people remember · preview consequences · consistency

**Mobile at all times:**
- Design the phone first and verify at {{mobile.minViewportPx}}px: no sideways scrolling.
- Everything still works with text at {{mobile.maxTextScalePercent}}%.
- Touch first: targets ≥ {{accessibility.minTouchTargetPx}}px and ≥ {{mobile.minTargetSpacingPx}}px apart; nothing is hover-only.
- On phones, the primary action is within thumb reach.
- Respect safe areas and the on-screen keyboard.

**Every component is dynamic:**
- Fluid: sized by its container and content, with min/max limits. No fixed size above {{mobile.maxFixedSizePx}}px.
- Works in any container width, with short, long (+{{mobile.textExpansionPercent}}% translated), empty or overflowing content, by touch, pointer and keyboard.
- Content comes in through props, never hard-coded.

**Accessibility:** {{accessibility.level}}; touch targets ≥ {{accessibility.minTouchTargetPx}}px; visible focus; semantic HTML.

**Density:** paginate lists over {{compositionHeuristics.listPaginationThreshold}} items; group forms over {{compositionHeuristics.maxInlineInputs}} fields; details go on a drill-down view.

**Severity:**
- **Blocker:** off-token value, invented component, more than one primary action, skipped decision or scope check, contrast or touch-target failure
- **Major:** hurts usability or consistency
- **Minor:** polish

**How to write a critique.** Every point uses the form `[Screen/Component]: [what's wrong] → [what it should be] → [why it matters]`, citing a token, principle or rubric category. Implementation notes give the exact component, property, old value → new value. Never write a bare preference like "make it pop" or "feels cleaner".

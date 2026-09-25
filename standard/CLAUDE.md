<!-- design-system-manifest: Baseline v1.0.0 -->
<!-- Generated from design-system-manifest.yaml by the design-generation skill.
     Regenerate it whenever the manifest's version changes; the skill refuses to run while the versions differ.
     The manifest is the source of truth. This file is the always-loaded summary.
     In Claude Design, this same content is the Design System's project/README.md (see skills/platform-adapters.md). -->

# Design system: Baseline

Every UI change in this repo follows these rules, including quick edits that don't run the full design agent. The full data (every token, component, variant and threshold) is in `design-system-manifest.yaml`. For new screens or features, use the **design-generation** skill.

## Tokens

Use only these values. Never hard-code a color, spacing, size, radius or duration.

**Color roles**
- Neutrals: background `#fafafa`, surface `#ffffff`, border `#d4d4d8`, text `#18181b`, muted text `#52525b`
- Accents: primary `#1d4ed8` (text on it: `#ffffff`), secondary `#7c3aed` (at most 1 on screen at once)
- Status: success `#15803d`, warning `#b45309`, error `#b91c1c`, info `#0369a1`. Each passes 4.5:1 as text on the surface, and each is always paired with an icon or text.
- Interaction: hover `#1e40af`, active `#1e3a8a`, focus `#1d4ed8`
- Contrast: WCAG-AA

**Typography**
- Display `Source Serif 4`, body `Source Sans 3`, UI `Source Sans 3`; weights 400 / 600 / 700
- Scale: base 16px × 1.2, steps sm 13 · base 16 · lg 19 · xl 23 · 2xl 28 · 3xl 33 · 4xl 40 (px); line height 1.5. No step is below the 12px legibility floor.
- Roles:
  - Heading: Source Serif 4, 700
  - Readable subtext: Source Sans 3, 400, in `#52525b`
  - Form label: Source Sans 3, 600, in `#18181b`. It must never look like readable subtext.

**Spacing & layout**
- Spacing scale (px): 4, 8, 12, 16, 24, 32, 48, 64; base unit 4px
- Radius: `radius-sm` 4px (inputs, chips, small buttons) · `radius-md` 8px (buttons, cards) · `radius-lg` 12px (dialogs, panels)
- Grid: 12 columns, 24px gutter, max width 1200px, alignment tolerance 0px (exact)
- Breakpoints (design mobile first): sm 640 · md 768 · lg 1024 · xl 1280

**Motion**
- Durations: micro 150ms, state 300ms, page 500ms
- Easing: entrance `ease-out`, exit `ease-in`, transition `ease-in-out`; always respect reduced motion

**Components.** Reuse these before building anything new:
- Button (`@/components/ui/button`): primary, secondary, ghost, destructive
- Input (`@/components/ui/input`): default, error
- Switch (`@/components/ui/switch`): default, on/off that takes effect immediately
- Checkbox (`@/components/ui/checkbox`): default, choices applied on submit
- RadioGroup (`@/components/ui/radio-group`): default, one of up to 5 visible options
- Select (`@/components/ui/select`): default, one of 6 or more options (native picker on phones)
- Card (`@/components/ui/card`): default, outlined (border + surface, no shadow)
- InlineAlert (`@/components/ui/inline-alert`): info, success, warning, error (icon + text + color)
- Toast (`@/components/ui/toast`): default
- Skeleton (`@/components/ui/skeleton`): default, used for every loading state
- EmptyState (`@/components/ui/empty-state`): default
- Dialog (`@/components/ui/dialog`): default, confirm-destructive
- Breadcrumb (`@/components/ui/breadcrumb`): default
- Pagination (`@/components/ui/pagination`): default
- Tabs (`@/components/ui/tabs`): default

## Brand rules

- Never:
  - glass morphism
  - gradient washes as backgrounds
  - drop shadows for depth (use border + surface color)
  - emoji as icons
  - color as the only signal for a state
- Icons: `lucide-react` only
- Decisions: `always-ask`. Before any layout, color or structure decision, offer 2–3 options with trade-offs and wait.
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
- understood in 3 s at `sm`
- reached in ≤ 3 clicks
- finished in ≤ 3 min

Never meet the click limit by cramming.

**Wickens' 13 display principles:**
- Perception: legible (≥ 12px) · no more than 5 unlabeled levels · follow convention · two cues for critical states · similar-looking means similar
- Mental model: pictorial realism · the moving part
- Attention: low access cost · related info close together · multiple channels
- Memory: show, don't make people remember · preview consequences · consistency

**Mobile at all times:**
- Design the phone first and verify at 320px: no sideways scrolling.
- Everything still works with text at 200%.
- Touch first: targets ≥ 44px and ≥ 8px apart; nothing is hover-only.
- On phones, the primary action is within thumb reach.
- Respect safe areas and the on-screen keyboard.

**Every component is dynamic:**
- Fluid: sized by its container and content, with min/max limits. No fixed size above 64px.
- Works in any container width, with short, long (+40% translated), empty or overflowing content, by touch, pointer and keyboard.
- Content comes in through props, never hard-coded.

**Accessibility:** AA; touch targets ≥ 44px; visible focus; semantic HTML.

**Density:** paginate lists over 10 items; group forms over 7 fields; details go on a drill-down view.

**Severity:**
- **Blocker:** off-token value, invented component, more than one primary action, skipped decision or scope check, contrast or touch-target failure
- **Major:** hurts usability or consistency
- **Minor:** polish

**How to write a critique.** Every point uses the form `[Screen/Component]: [what's wrong] → [what it should be] → [why it matters]`, citing a token, principle or rubric category. Implementation notes give the exact component, property, old value → new value. Never write a bare preference like "make it pop" or "feels cleaner".

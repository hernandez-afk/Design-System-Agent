<!-- design-system-manifest: Acme Product UI v1.0.0 -->
<!-- Generated from design-system-manifest.yaml by the design-generation skill.
     Regenerate it whenever the manifest's version changes; the skill refuses to run while the versions differ.
     The manifest is the source of truth. This file is the always-loaded summary.
     In Claude Design, this same content is the Design System's project/README.md (see skills/platform-adapters.md). -->

# Design system: Acme Product UI

Every UI change in this repo follows these rules, including quick edits that don't run the full design agent. The full data (every token, component, variant and threshold) is in `design-system-manifest.yaml`. For new screens or features, use the **design-generation** skill.

## Tokens

Use only these values. Never hard-code a color, spacing, size, radius or duration.

**Color roles** (Tailwind names)
- Neutrals (cool): background `slate-50`, surface `white`, border `slate-200`, text `slate-900`, muted text `slate-600`
- Accents: primary `teal-500` (text on it: `slate-900`; white fails AA), secondary `amber-500` (at most 1 on screen at once)
- Status: success `green-500`, warning `amber-500`, error `red-500`, info `sky-500`
- Interaction: hover `teal-600`, active `teal-700`, focus `teal-600`
- Contrast: WCAG-AA

**Typography**
- Display `Fraunces`, body `Inter`, UI `Inter`; weights 400 / 500 / 700
- Scale: base 16px × 1.25, steps xs · sm · base · lg · xl · 2xl · 3xl · 4xl · 5xl; line height 1.5. `xs` (10px) is below the 12px legibility floor: never use it for text.
- Roles:
  - Heading: Fraunces 700
  - Readable subtext: Inter 400 in `slate-600`
  - Form label: Inter 500, uppercase, in `slate-900`. It must never look like readable subtext.

**Spacing & layout**
- Spacing scale (px): 4, 8, 16, 24, 32, 48; base unit 4px
- Radius: `radius-sm` 4px (inputs, chips, small buttons) · `radius-md` 8px (buttons, cards) · `radius-lg` 12px (panels, dialogs)
- Grid: 12 columns, 24px gutter, max width 1200px, alignment tolerance 0px (exact)
- Breakpoints (design mobile first): sm 640 · md 768 · lg 1024 · xl 1280

**Motion**
- Durations: micro 150ms, state 300ms, page 500ms
- Easing: entrance `ease-out`, exit `ease-in`, transition `ease-in-out`; always respect reduced motion

**Components.** Reuse these before building anything new:
- Button (`@/components/ui/button`): primary, secondary, ghost, destructive
- Card (`@/components/ui/card`): default, outlined (border + background, no shadow)
- Input (`@/components/ui/input`): default, error
- Toast (`sonner`): default
- Skeleton (`@/components/ui/skeleton`): default, used for every loading state
- Tabs (`@/components/ui/tabs`): default
- Pending review, don't reuse yet: Button/icon-only (DES-481)

## Brand rules

- Never:
  - `#3B82F6` default SaaS blue
  - glass morphism
  - drop shadows for depth
  - Inter, Roboto or Space Grotesk as the display font
- Icons: `@phosphor-icons/react` only
- Decisions: `always-ask`. Before any layout, color or structure decision, offer 2–3 options with trade-offs and wait.
- One primary action per screen. Secondary actions never get `teal-500` fill.
- New components or variants go through a gap report and a verification report. Never invent one inline.

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

**Accessibility:** AA; touch targets ≥ 44px; visible focus; semantic HTML.

**Density:** paginate lists over 10 items; group forms over 7 fields; details go on a drill-down view.

**Severity:**
- **Blocker:** off-token value, invented component, more than one primary action, skipped decision or scope check, contrast or touch-target failure
- **Major:** hurts usability or consistency
- **Minor:** polish

**How to write a critique.** Every point uses the form `[Screen/Component]: [what's wrong] → [what it should be] → [why it matters]`, citing a token, principle or rubric category. Implementation notes give the exact component, property, old value → new value. For example:
- Bad: "Improve the spacing"
- Good: "DashboardSummaryRow gap: 20px → 24px (spacing.scale)"

Never write a bare preference like "make it pop" or "feels cleaner".

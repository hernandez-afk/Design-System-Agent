<!-- design-system-manifest: Acme Product UI v1.0.0 -->
<!-- Generated from the manifest; regenerate when its version changes. Loaded every turn, so keep it short: detail stays in the manifest, which the tools read. In Claude Design, this is the Design System's README. -->

# Design system: Acme Product UI

All UI follows this, even quick edits. New pages and features: use the **design-agent** skill.

**Color (Tailwind):** background `slate-50` · surface `white` · border `slate-200` · text `slate-900` / `slate-600` · primary `teal-500` (text on it `slate-900`; white fails AA) · secondary `amber-500` (max 1) · success/warning/error/info `green-500`/`amber-500`/`red-500`/`sky-500` · hover/focus `teal-600`/`teal-600`

**Type:** Fraunces (display), Inter (body/UI, required by the Acme guidelines), and no other family. Styles: page-title 3xl/700 · section-heading xl/700 · subheading lg/500 · body base/400 · label sm/500 (uppercase). `xs` (10px) is never for text.

**Spacing:** scale 4 8 16 24 32 48. Roles: card-padding 16 (Card, StatTile) · control 16×8 (Button, Input) · stack-related 8 · stack-group 24 · section 48. Radius 4/8/12.

**Layout:** 12 cols, gutter 24px; breakpoints 640/768/1024/1280; phone first, verified at 320px and 200% text.

**Components:** Button (primary, secondary, ghost, destructive; icon-only pending, don't reuse) · Card (default, outlined) · Input (default, error) · Toast · Skeleton · Tabs

**Never:** `#3B82F6` default SaaS blue · glass morphism · drop shadows for depth · Inter, Roboto or Space Grotesk as the display font. Icons: @phosphor-icons/react only.

**Rules:**
- Only these tokens, roles, styles and components. The same kind of element looks the same everywhere.
- One primary action per screen.
- Say each thing once: no sentence, figure or status appears twice on a screen. If it matters that much, make it one stronger element.
- Brand: Acme (`brand/acme-brand.example.yaml`). Anything that uses that name or logo follows those guidelines, and the tools warn when it doesn't match.
- Touch targets ≥ 44px, text ≥ 12px, WCAG-AA contrast, and never color alone for a state.
- Every core task is understood in 3 s, reached in ≤ 3 taps, and done in ≤ 3 min.
- Before editing UI, `python3 .claude/design-agent/tools/design_context.py <file>` shows the design that owns it, and the hook shows it on the first edit. Contradicting that design's decision is a design change: raise it, don't just edit.
- Critiques are `where: what → fix (rule)`, never a bare preference.

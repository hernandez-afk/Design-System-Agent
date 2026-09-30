<!-- design-system-manifest: Baseline v1.0.0 -->
<!-- Generated from the manifest; regenerate when its version changes. Loaded every turn, so keep it short: detail stays in the manifest, which the tools read. In Claude Design, this is the Design System's README. -->

# Design system: Baseline

All UI follows this, even quick edits. New pages and features: use the **design-agent** skill.

**Color:** background `#fafafa` · surface `#ffffff` · border `#d4d4d8` · text `#18181b` / `#52525b` · primary `#1d4ed8` (text on it `#ffffff`) · secondary `#7c3aed` (max 1) · success/warning/error/info `#15803d`/`#b45309`/`#b91c1c`/`#0369a1` · hover/focus `#1e40af`/`#1d4ed8`

**Type:** Source Serif 4 (display), Source Sans 3 (body/UI), and no other family. Styles: page-title 33/700 · section-heading 23/600 · subheading 19/600 · body 16/400 · label 13/600 · caption 13/400

**Spacing:** scale 4 8 12 16 24 32 48 64. Roles: card-padding 16 (Card, Dialog, InlineAlert) · control 16×12 (Button, Input, Select) · stack-related 8 · stack-group 24 · section 48 · page-gutter 16. Radius 4/8/12.

**Layout:** 12 cols, gutter 24px; breakpoints 640/768/1024/1280; phone first, verified at 320px and 200% text.

**Components:** Button (primary, secondary, ghost, destructive) · Input (default, error) · Switch · Checkbox · RadioGroup · Select · Card (default, outlined) · InlineAlert (info, success, warning, error) · Toast · Skeleton · EmptyState · Dialog (default, confirm-destructive) · Breadcrumb · Pagination · Tabs

**Never:** glass morphism · gradient washes as backgrounds · drop shadows for depth · emoji as icons · color as the only signal for a state. Icons: lucide-react only.

**Rules:**
- Only these tokens, roles, styles and components. The same kind of element looks the same everywhere.
- One primary action per screen.
- Every page has one purpose, and everything on it serves it; what doesn't goes elsewhere. Say little: a text block is ≤ 30 words, an intro ≤ 20, and the first screen at 320px ≤ 60 words, with the title and primary action in view. Numbers are stats, change over time a chart, steps a stepper, a state a badge, help the control's label.
- Say each thing once: no sentence, figure or status appears twice on a screen. If it matters that much, make it one stronger element.
- Brand guidelines: Atari's are a reference, not this project's system. Use them only when a brief, design or page asks to follow the Atari brand guidelines (`brandGuidelines: ["Atari"]`): then design with `brand/atari/CLAUDE.md` instead of this file's tokens and type. A page that only mentions Atari still uses this system. An Atari logo always follows the logo rules.
- Touch targets ≥ 44px, text ≥ 12px, WCAG-AA contrast, and never color alone for a state.
- Every core task is understood in 3 s, reached in ≤ 3 taps, and done in ≤ 3 min.
- Before editing UI, `python3 .claude/design-agent/tools/design_context.py <file>` shows the design that owns it, and the hook shows it on the first edit. Contradicting that design's decision is a design change: raise it, don't just edit.
- Critiques are `where: what → fix (rule)`, never a bare preference.

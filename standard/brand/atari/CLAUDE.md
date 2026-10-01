<!-- design-system-manifest: Atari v1.0.0 -->
<!-- The Atari reference design system, from ATARI Brand Guidelines V1.1. Used instead of the project's design system only for work that declares brandGuidelines: ["Atari"]. -->

# Design system: Atari (reference)

Use this only when the brief, design or page follows the Atari brand guidelines. Everything else uses the project's design system.

**Color (exact palette values only, nothing else):** background `#FFFFFF` · surface `#F5F5F5` · border `#E0E0E0` · text `#171717` / `#616161` · primary Atari Red `#E01E2B` (text on it `#FFFFFF`) · secondary `#A4009F` (max 1) · success/warning/error/info `#4D6A31`/`#AD582A`/`#BD1E56`/`#0065B9` · hover/active/focus `#C14340`/`#6C302E`/`#0065B9`. Any other color must come exactly from `../atari.yaml`.

**Type:** Atari 1972 Regular for h1 and h2, in capitals; Poppins Medium (500) for everything else. No other family. Styles: page-title 39/400 · section-heading 25/400 · subheading 20/500 · body 16/500 · label 13/500 · caption 13/500

**Spacing:** scale 4 8 12 16 24 32 48 64. Roles: card-padding 16 (Card, Dialog, InlineAlert) · control 16×12 (Button, Input, Select) · stack-related 8 · stack-group 24 · section 48 · page-gutter 16. Radius 4/8/12.

**Layout:** 12 cols, gutter 24px; breakpoints 640/768/1024/1280; phone first, verified at 320px and 200% text.

**Components:** Button (primary, secondary, ghost, destructive) · Input (default, error) · Switch · Checkbox · RadioGroup · Select · Card (default, outlined) · InlineAlert (info, success, warning, error) · Toast · Skeleton · EmptyState · Dialog (default, confirm-destructive) · Breadcrumb · Pagination · Tabs

**Logos:** Atari Red, or black or white when red can't work; never palette colors, two colors, gradients, outlines, rotation or distortion; never retyped. Mark each one `data-brand-asset="atari-fuji"` (or `-wordmark`, `-stacked`, `-box`, `-horizontal`, `-vertical`). Minimum widths: Fuji 50px, wordmark 60px. Clear space: 25% of the logo's height (Stacked, Box), 50% (Horizontal). The Box is always Atari Red.

**Never:** glass morphism · gradient washes as backgrounds · drop shadows for depth · emoji as icons · color as the only signal for a state · Comfortaa (Google Slides only). Icons: lucide-react only.

**Rules:**
- Only these tokens, roles, styles and components. The same kind of element looks the same everywhere.
- One primary action per screen.
- Show as little as possible at a time. The top bar and sidebars hold only the logo, title, navigation and controls; a role ("Admin"), plan or environment goes in the account menu, and only the actions it changes are marked.
- Cards and boxes show at most 5 pieces of information, and at most 3 buttons on a card repeated on screen (5 on a single box); the rest go in a "⋯" menu or the detail view. Navigation keeps the most-used options at the top (≤ 7 a level), every option within 2 clicks, a search past 15 options, and less-used controls nested behind one labelled control (≤ 12 controls on the first screen at 320px).
- Every page has one purpose, and everything on it serves it; what doesn't goes elsewhere. Say little: a text block is ≤ 30 words, an intro ≤ 20, and the first screen at 320px ≤ 60 words, with the title and primary action in view. Numbers are stats, change over time a chart, steps a stepper, a state a badge, help the control's label.
- Say each thing once: no sentence, figure or status appears twice on a screen. If it matters that much, make it one stronger element.
- The name is "Atari", or "ATARI" in capitals; never "atari".
- Touch targets ≥ 44px, text ≥ 12px, WCAG-AA contrast, and never color alone for a state.
- Every core task is understood in 3 s, reached in ≤ 3 taps, and done in ≤ 3 min.
- Critiques are `where: what → fix (rule)`, never a bare preference.

<!-- design-system-manifest: {{meta.name}} v{{meta.version}} -->
<!-- Generated from the manifest; regenerate when its version changes. Loaded every turn, so keep it short: detail stays in the manifest, which the tools read. In Claude Design, this is the Design System's README. -->

# Design system: {{meta.name}}

All UI follows this, even quick edits. New pages and features: use the **design-agent** skill.

**Color:** background `{{color.neutrals.background}}` · surface `{{color.neutrals.surface}}` · border `{{color.neutrals.border}}` · text `{{color.neutrals.textPrimary}}` / `{{color.neutrals.textSecondary}}` · primary `{{color.accents.primary}}` (text on it `{{color.accents.onPrimary}}`) · secondary `{{color.accents.secondary}}` (max {{color.usagePolicy.maxSimultaneousSecondaryAccents}}) · success/warning/error/info `{{color.accents.success}}`/`{{color.accents.warning}}`/`{{color.accents.error}}`/`{{color.accents.info}}` · hover/focus `{{color.interactionStates.hover}}`/`{{color.interactionStates.focus}}`

**Type:** {{typography.typefaces.display}} (display), {{typography.typefaces.body}} (body/UI), and no other family. Styles: {{typography.styles — name step/weight, one per item}}

**Spacing:** scale {{spacing.scale}}. Roles: {{spacing.roles — name px (applies to), one per item}}. Radius {{radius.tokens — name px}}.

**Layout:** {{layout.gridColumns}} cols, gutter {{layout.gutterPx}}px; breakpoints {{layout.breakpoints}}; phone first, verified at {{mobile.minViewportPx}}px and {{mobile.maxTextScalePercent}}% text.

**Components:** {{approved components with variants, one line; pending ones marked "pending, don't reuse"}}

**Never:** {{meta.brandExclusions}}. Icons: {{icons.library}} only.

**Rules:**
- Only these tokens, roles, styles and components. The same kind of element looks the same everywhere.
- One primary action per screen.
- Show as little as possible at a time. The top bar and sidebars hold only the logo, title, navigation and controls; a role ("Admin"), plan or environment goes in the account menu, and only the actions it changes are marked.
- Cards show at most 5 pieces of information. Navigation keeps the most-used options at the top (≤ 7 a level), every option within 2 clicks, a search past 15 options, and less-used controls nested behind one labelled control (≤ 12 controls on the first screen at 320px).
- Every page has one purpose, and everything on it serves it; what doesn't goes elsewhere. Say little: a text block is ≤ {{contentPolicy.maxWordsPerBlock}} words, an intro ≤ {{contentPolicy.maxIntroWords}}, and the first screen at {{mobile.minViewportPx}}px ≤ {{contentPolicy.maxWordsFirstScreen}} words, with the title and primary action in view. Numbers are stats, change over time a chart, steps a stepper, a state a badge, help the control's label.
- Say each thing once: no sentence, figure or status appears twice on a screen. If it matters that much, make it one stronger element.
- Brand guidelines: {{brandGuidelines — for each profile: name (path), and whether it is this product's own (applies: always) or a reference used only when declared (brandGuidelines: ["<name>"] in the brief or page), with its reference system's CLAUDE.md}}. The tools warn when declared work doesn't match.
- Touch targets ≥ {{accessibility.minTouchTargetPx}}px, text ≥ {{usabilityHeuristics.displayDesign.minReadableTextPx}}px, {{color.contrastStandard}} contrast, and never color alone for a state.
- Every core task is understood in 3 s, reached in ≤ 3 taps, and done in ≤ 3 min.
- Before editing UI, `python3 .claude/design-agent/tools/design_context.py <file>` shows the design that owns it, and the hook shows it on the first edit. Contradicting that design's decision is a design change: raise it, don't just edit.
- Critiques are `where: what → fix (rule)`, never a bare preference.

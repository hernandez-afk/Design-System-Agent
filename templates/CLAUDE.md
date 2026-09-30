<!-- design-system-manifest: {{meta.name}} v{{meta.version}} -->
<!-- Generated from the manifest; regenerate when its version changes. Loaded every turn, so keep it short: detail stays in the manifest, which the tools read. In Claude Design, this is the Design System's README. -->

# Design system: {{meta.name}}

All UI follows this, even quick edits. New pages and features: use the **design-agent** skill.

**Color:** background `{{color.neutrals.background}}` · surface `{{color.neutrals.surface}}` · border `{{color.neutrals.border}}` · text `{{color.neutrals.textPrimary}}` / `{{color.neutrals.textSecondary}}` · primary `{{color.accents.primary}}` (text on it `{{color.accents.onPrimary}}`) · secondary `{{color.accents.secondary}}` (max {{color.usagePolicy.maxSimultaneousSecondaryAccents}}) · success/warning/error/info `{{color.accents.success}}`/`{{color.accents.warning}}`/`{{color.accents.error}}`/`{{color.accents.info}}` · hover/focus `{{color.interactionStates.hover}}`/`{{color.interactionStates.focus}}`

**Type:** {{typography.typefaces.display}} (display), {{typography.typefaces.body}} (body/UI). Styles: {{typography.styles — name step/weight, one per item}}

**Spacing:** scale {{spacing.scale}}. Roles: {{spacing.roles — name px (applies to), one per item}}. Radius {{radius.tokens — name px}}.

**Layout:** {{layout.gridColumns}} cols, gutter {{layout.gutterPx}}px; breakpoints {{layout.breakpoints}}; phone first, verified at {{mobile.minViewportPx}}px and {{mobile.maxTextScalePercent}}% text.

**Components:** {{approved components with variants, one line; pending ones marked "pending, don't reuse"}}

**Never:** {{meta.brandExclusions}}. Icons: {{icons.library}} only.

**Rules:**
- Only these tokens, roles, styles and components. The same kind of element looks the same everywhere.
- One primary action per screen.
- Touch targets ≥ {{accessibility.minTouchTargetPx}}px, text ≥ {{usabilityHeuristics.displayDesign.minReadableTextPx}}px, {{color.contrastStandard}} contrast, and never color alone for a state.
- Every core task is understood in 3 s, reached in ≤ 3 taps, and done in ≤ 3 min.
- Before editing UI, `python3 .claude/design-agent/tools/design_context.py <file>` shows the design that owns it, and the hook shows it on the first edit. Contradicting that design's decision is a design change: raise it, don't just edit.
- Critiques are `where: what → fix (rule)`, never a bare preference.

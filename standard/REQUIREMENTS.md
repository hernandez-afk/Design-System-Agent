# Design system requirements

What a design system needs to work with this agent. **Baseline** (`standard/design-system-manifest.yaml`) meets all of it and is the reference: copy it to start a new design system and replace the values.

Check any design system:

```
python3 tools/check_compatibility.py path/to/design-system-manifest.yaml
```

| Level | Means | Checker exit |
|---|---|---|
| **Not compatible** | The agent halts before designing anything. | 2 |
| **Minimum** | The agent runs, but fills some settings with its own defaults, or can't satisfy some rubric checks without inventing components. | 1 |
| **Optimal** | Every setting is explicit, every value passes the agent's own checks, and the baseline components exist. Consistency is enforced, not assumed. | 0 |

---

## Level 1: Minimum (the agent runs)

| Requirement | Why the agent needs it | If missing |
|---|---|---|
| A manifest that validates against `schemas/design-system-manifest.schema.json` | Every step reads it. It's the single source of truth. | Halts |
| `meta.name`, `meta.version` | The version stamp that keeps `CLAUDE.md` and exports in sync | Halts |
| Color roles: `neutrals.background`, `surface`, `border`, `textPrimary`, and `accents.primary` | Structure and the primary action | Halts |
| Typography: `typefaces`, `scale.baseSizePx`, `scale.ratio` | The type scale every size comes from | Halts |
| Spacing: `baseUnitPx`, `scale` | Every gap and padding value | Halts |
| `layout`, `accessibility.level` | Grid, breakpoints and contrast targets | Halts |
| At least one entry in `components` | The reuse check needs a registry to compare against | Halts |
| **Project context** with a matching version stamp: `CLAUDE.md` (Claude Code) or the Design System README (Claude Design) | Keeps every session on-system, including ones that never run the agent | Halts, and offers to generate it |
| **Claude Design only:** `color.resolved`, with real values for every role | A Design System needs real colors, and contrast can only be computed from them | Halts (schema) |

## Level 2: Optimal (consistency is enforced)

### Every setting explicit

The agent has a default for everything below. Leaving one out works, but the agent then decides it for you, and the audit can't hold the design to a rule nobody set.

- **Governance:** `meta.decisionProtocol`, `meta.brandExclusions`, `meta.claudeMd`, `platform.targets`
- **Color:** `contrastStandard`, `textSecondary`, `onPrimary`, all four status colors, `interactionStates` (hover, active, focus), `usagePolicy` (secondary-accent limit, one primary action per screen)
- **Type:** `weights`, `scale.steps`, `lineHeightRatio`, `roles` (heading, readable subtext and form label must look different)
- **Layout:** `gridColumns`, `gutterPx`, `breakpoints`, `containerMaxWidthPx`, `alignmentTolerancePx`
- **Tokens:** `motion`, `radius`, `icons.library`
- **Accessibility:** `minTouchTargetPx`, `requireVisibleFocusStates`, `requireSemanticHtml`
- **Registry:** `registryPolicy` in full, including `similarityCheck`, `requireOperationalVerification` and `verificationReviewer`
- **Behavior:** `automation`, `compositionHeuristics`, `navigationHeuristics`, `motionUsagePolicy`, `usabilityHeuristics`, `scopePolicy`
- **Mobile:** `mobile` in full (narrowest width, text scale, target spacing, largest fixed size, text expansion, thumb zone, orientations)

### Values that pass the agent's own checks

| Rule | Why | Baseline |
|---|---|---|
| Text colors pass the contrast standard on both background and surface | Rubric category 2 blocks designs that fail it, so the tokens must not fail it first | `#18181b` and `#52525b`: at least 17.0:1 and 7.4:1 |
| `onPrimary` passes on `primary` | Every primary button's label | White on `#1d4ed8`: 6.7:1 |
| Status colors pass 4.5:1 as text on the surface | They're used as alert text, not only as fills | The 700 shades, all ≥ 5:1 |
| Focus color passes 3:1 against the background | A focus ring you can't see fails rubric category 10 | `#1d4ed8`: 6.4:1 |
| Secondary accent differs from every status color | Otherwise "the other choice" reads as a warning or error | Violet `#7c3aed` |
| No type step below `minReadableTextPx` | Wickens 1: a step that can't be used for text is a trap | Smallest step 13px |
| At most 3 weights | Rubric category 3 | 400 / 600 / 700 |
| Spacing steps are multiples of `baseUnitPx`, in ascending order, and the gutter is one of them | Alignment is exact (`alignmentTolerancePx: 0`) | 4–64 on a 4px unit, 24px gutter |
| Breakpoints ascending; touch targets ≥ 44px | Mobile-first layout; rubric category 2 | 640 / 768 / 1024 / 1280; 44px |
| Designs verified at 360px or narrower; text scale ≥ 200%; target spacing ≥ 8px; a breakpoint at or below 640px | Mobile at all times (rubric category 14) | 320px, 200%, 8px, sm 640 |
| Similarity and overlap weights each sum to 1, with reuse > extend and merge > related | Otherwise the reuse and scope checks route work wrongly | Defaults |

### Dynamic components

Every component, baseline or new, must be **dynamic**: fluid (no fixed size above `mobile.maxFixedSizePx`), container-aware, content-proof, able to scale with text, touch-first, data-driven and token-driven (`skills/design-principles.md`). The standard enforces this in three places:

- **Approval:** a verification report needs a `dynamicBehavior` section and `dynamicPass: true` before a component can be approved.
- **Every design:** each design output carries a `mobileCheck`, and rubric category 14 audits it.
- **Code:** the token lint flags fixed widths and heights above the limit.

### Baseline components

Each exists because a rubric check assumes it. Without it, the agent must file a gap report on every design that needs it. All must be `approved` and list their `props`, because the similarity check scores components by their props and variants.

| Component | Category | Required variants | Rubric check it serves |
|---|---|---|---|
| Button | action | primary, secondary, ghost, destructive | One primary action per screen (cat. 10); destructive actions (cat. 8) |
| Input | input | default, error | Form labels distinct from subtext (cat. 3); errors with more than color (Wickens 4) |
| Card | display | default | Containers built from border + surface, not shadows |
| InlineAlert | feedback | info, success, warning, error | Critical states with two cues (Wickens 4); visible system state (cat. 8) |
| Skeleton | feedback | default | Loading states for every async wait (cat. 8, `motionUsagePolicy`) |
| Dialog | overlay | confirm-destructive | Confirmation before destructive actions (cat. 8) |
| Breadcrumb | navigation | default | Navigational ties past `breadcrumbThresholdDepth` (cat. 10) |
| Pagination | navigation | default | Lists over `listPaginationThreshold` (cat. 9) |

**Recommended:** Toast (non-blocking confirmations), EmptyState (the empty state every verification report asks about), Tabs (peer views), and the choice controls Switch, Checkbox, RadioGroup and Select, which almost every form needs. Without them, a brief's settings or choices produce a gap report on the first page that has them.

### Per platform

- **Claude Code:** `development.uiPaths` set and `tokenLint` not off, so the token lint and design context reach day-to-day coding. Every approved or shipped design in the index has `codePaths`.
- **Claude Design:** `color.resolved` for every role, exported with `tools/export_claude_design.py`, and the Design System marked as the default.

---

## Adopting the standard

1. Copy `standard/` into your product repo: the manifest, `CLAUDE.md` and the empty design index.
2. Replace the values with your brand's: name, colors (in both the roles and `color.resolved`), typefaces, components and their import paths. Keep the structure and the baseline components.
3. Bump `meta.version`, and regenerate `CLAUDE.md` so its stamp matches.
4. Run `tools/check_compatibility.py` until it reports **Optimal**.
5. For Claude Design, run `tools/export_claude_design.py`. For Claude Code, install the hooks (see the README, "Setting up the development side").

---
name: platform-adapters
description: How the design pipeline runs on each platform — Claude Code (a repo with CLAUDE.md and files) and Claude Design (a Design System artifact and Design canvases on claude.ai). The process, principles and rubric are identical; only where context is loaded from, where components live, where the design is drawn, and where records are kept change.
---

# Platform Adapters

The skills never change per platform. What changes is **where things live**. Read `platform.targets` in the manifest, detect which platform this run is on, and use that column below for every step.

**Detecting the platform.** A repository working directory with the manifest in it means **Claude Code**. A claude.ai conversation where you can list Design System artifacts means **Claude Design**. If both are available (a repo is connected in a claude.ai session, or Claude Code can publish artifacts), and `targets` lists both, use the repo for records and the canvas for drawing. That's the recommended setup.

## The map

| Pipeline part | Claude Code | Claude Design |
|---|---|---|
| **Source of truth** | `design-system-manifest.yaml` in the repo | The same manifest. Keep it in a repo, or in a Claude Project's files. The Design System artifact is *exported from* it, never edited by hand into a second truth. |
| **Always-loaded context** | `CLAUDE.md` at the repo root (`templates/CLAUDE.md`) | The default Design System's `project/README.md`. Every Design canvas reads it before drawing, and `platform.claudeDesign.markAsDefault` keeps it applied to every design. Same content as `CLAUDE.md`, from the same template. |
| **Version stamp** | First line of `CLAUDE.md`: `<!-- design-system-manifest: <name> v<version> -->` | First line of the Design System README, same stamp. The skill reads the README and compares, exactly as it does for `CLAUDE.md`. |
| **Tokens** | Manifest values used directly (e.g. Tailwind class names) | The Design System's `project/tokens.json`, built by `tools/export_claude_design.py` from `color.resolved`, the type scale, `spacing.scale` and `radius`. Never typed by hand. |
| **Components** | `components[]` with `importPath` | Design System components (`components/<Name>/README.md` + preview, in its bundle). **Only `approved` components go in the bundle.** A `proposed` one is drawn as artboard markup on the canvas, labeled pending review, until its verification report passes. |
| **Brief, scope check, design index** | Files in the repo | `recordStore: repo` (recommended): the same files, in a connected repo. `recordStore: design-system-section`: the design index is kept as a `design-index.md` section of the Design System; per-run reports are given in the conversation and not stored, so scope checks and change tracking only see what the index records. |
| **Drawing the design (Steps 5–9)** | Code or markup per `meta.framework` (`html`, `react-jsx`, …) | A **Design canvas** (`artifact.format: claude-design-canvas`), one artboard per screen × breakpoint from `platform.claudeDesign.canvasBoards`, starting at the phone size. The phone board is required on every canvas and is drawn first. Components on it are the Design System's dynamic components, sized by the board, not fixed. Core tasks for the 3-3-3 walk-through get an interactive prototype board whose links follow the task path. |
| **User flow (Step 2c)** | `user-flow` file, checked with `tools/flow_check.py`; `--mermaid` draws it | The same file, drawn on the canvas as linked artboards: prototype links follow each flow's steps. Existing pages that need an integration change get a board showing the proposed change, labeled pending until their owner accepts it. |
| **Decision Protocol alternatives** | Described in the reply, or drafted as separate files | Drafted as side-by-side artboards on the same canvas, one per alternative, with the trade-offs in the reply, never written on the artboards. |
| **Audit (Step 11)** | `audit-report` file + rendered template | The same report and rendered template, given in the reply. Findings never go on the artboards; the canvas stays a clean design. |
| **Design context while coding** | Hooks (`templates/claude-settings.json`): session start lists every design and the code it owns, and warns if `CLAUDE.md` is stale. The first edit to a design's files in a session shows that design's decisions. Every edit is token-linted. | No code editing happens on the canvas. The default Design System keeps every new design on-system. Code-side context needs the repo (`targets` both). |
| **Enforcement between runs** | `CLAUDE.md` loads every session; hooks (optional) | The default Design System applies to every new canvas; there are no hooks. The version-stamp check at the start of each run is the safety net. |

## Exporting the manifest to a Design System

Whenever the manifest's `meta.version` changes and `targets` includes `claude-design`:

1. Run `python3 tools/export_claude_design.py <manifest> <out-dir>`. It writes `project/tokens.json` in the Design System's list shape and reports any role without a resolved value, any duplicate token name, and any text-on-fill pair that fails `contrastStandard` in any theme. Fix every error before exporting. Fix contrast warnings, or keep them only with a note saying why.
2. Fill `templates/CLAUDE.md` from the manifest and save it as `project/README.md`, stamp included. It's the design system's brand book: tokens and how to use them, brand rules, critique criteria.
3. For each **approved** component, write `components/<Name>/README.md` (first sentence: what it's for; then variants, props, when not to use it). If the manifest records a verification report for it, cite it.
4. Publish to `platform.claudeDesign.designSystemUrl`, or create the Design System on first export and record its link there. Do this by following the Design System type's own instructions. Then bump nothing else: the export reflects the manifest; it doesn't change it.

## What only one platform can do

- **Claude Code only:** hooks, direct file edits in the product's codebase, and git history for every record.
- **Claude Design only:** live artboards people can comment on, clickable prototypes, and a default design system that applies to every new design, including ones started without this skill.

When `targets` lists both, you get both: records and enforcement in the repo, and designs on the canvas.

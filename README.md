# Design System Agent

A design agent whose first job is **consistency**: it keeps a product consistent as it's built, by keeping design context present wherever the product is worked on, in design and in development. It generates and audits UI designs from config. The skills hold fixed *process* (how to reason from a ticket to a layout, when to ask, when to reuse, when to audit); every project-specific value (colors, type, spacing, components) comes from a per-project design-system manifest.


## The core guarantee: consistency, with design context everywhere

The most important thing this system does is keep a product consistent while it's being built, by making sure **design context is always present in development**, not only when a design is being made. These are the guarantees, and what enforces each:

| Guarantee | While designing | While developing (Claude Code) |
|---|---|---|
| Every session knows the design system | Skill halts on a missing or stale `CLAUDE.md` / Design System README | `CLAUDE.md` loads every session. The session-start hook warns if it's stale. |
| Every piece of work knows the design that owns it | Scope check against the design index (Step 2b) | Code is linked to designs by `codePaths`. The first edit to a design's files shows its context. |
| Decisions are made once and reused | Inherited decisions, shared patterns | The design context lists the owning design's decisions. Contradicting one is raised as a design change. |
| Every design works on a phone; every component is dynamic | Mobile pass (`mobileCheck`) on every design; `dynamicBehavior` required to approve a component; rubric category 14 | The token lint flags fixed sizes that break on narrow screens |
| Every value is a token | Rubric category 3 | `token_lint.py` runs after every edit and sends off-token values back to fix |
| Every component comes from the registry | Reuse check, gap + verification reports | The design context lists the components to use |
| Nothing drifts silently | Version stamps, change propagation, `needs-review` flags | Session start lists every design with open review flags |
| The work is checked by someone who didn't make it | Independent critic persona | — |

### Setting up the development side (Claude Code)

In your app repo:

1. Copy `tools/` to `.claude/design-agent/tools/`, and put `design-system-manifest.yaml` and your design index at the repo root.
2. Merge `templates/claude-settings.json` into `.claude/settings.json`.
3. Run `pip install pyyaml`, and add `.claude/.design-context-seen/` to `.gitignore`.
4. In the manifest, set `development.uiPaths` (which files are UI) and give every design in the index its `codePaths`.

To try the tools on this repo's examples:

```
python3 tools/design_context.py examples/app/src/app/dashboard/DashboardSummaryRow.tsx --root examples/app --index ../design-index.example.yaml --manifest ../design-system-manifest.example.yaml
python3 tools/token_lint.py examples/app/src/app/dashboard/DashboardSummaryRow.tsx --root examples/app --manifest ../design-system-manifest.example.yaml
```

The first shows DES-512's decisions, components and review flags. The second catches the `gap-5` (20px) spacing bug and an off-brand blue.

## Starting a new page: the page brief

Describe a new page in plain language using **`templates/page-brief.md`**: purpose, ranked goals, what users need to do, content, states, constraints and acceptance criteria. You don't need to know the design system.

The brief is then optimized in a standard way (**`skills/brief-optimization.md`**, generation Step 1) so it fits the design system and the output can be checked against it:

- **Lint:** `python3 tools/brief_lint.py brief.md` catches missing sections, placeholders, vague words, solution-first wording, lists with no amounts, missing states and untestable criteria.
- **Fit to the design system:**
  - vague words become rules ("pop" → the one primary action; "easy" → the 3-3-3 limits)
  - solutions become needs ("a dropdown" → "choose one of 3 frequencies"), so the reuse check picks the component
  - conflicts with the design system are listed for you to accept, never resolved silently
  - acceptance criteria are made testable, using the manifest's thresholds
- **Report and approve:** a `brief-optimization-report` shows every change, conflict and question. Nothing is designed until you approve it.
- **Checked in the output:** the design output lists each acceptance criterion as met or not, with evidence, and the audit blocks a design that fails one.

Your team's own terms can be added to the vocabulary in the manifest (`briefPolicy.vocabulary`). See `examples/page-brief.example.md` → `examples/brief-optimization-report.example.yaml` → `examples/ticket-brief-page.example.yaml`.

## The standard: minimum requirements and a reference design system

**`standard/`** holds **Baseline**, a neutral design system that meets every requirement, and **`standard/REQUIREMENTS.md`**, which says what's required and why:

- **Minimum:** the agent runs. A valid manifest, core color, type and spacing tokens, a component registry, and project context with a matching version stamp.
- **Optimal:**
  - every setting explicit, nothing left to the agent's defaults
  - every value passes the agent's own checks (contrast, the legibility floor, the spacing unit)
  - the eight baseline components the rubric relies on (Button, Input, Card, InlineAlert, Skeleton, Dialog, Breadcrumb, Pagination)

Check where any design system stands:

```
python3 tools/check_compatibility.py path/to/design-system-manifest.yaml
```

Baseline reports **Optimal**. The Acme example reports **Minimum**, listing its gaps, which is what the checker is for. To start a new design system, copy `standard/`, replace the values, and run the checker until it reports Optimal.

## Folder structure

- **skills/** — the fixed logic (SKILL.md-style files): principles, the generation process, the audit rubric, and the mandatory human-facing report template.
- **schemas/** — the JSON Schemas defining every data contract that passes between steps.
- **personas/** — the Designer and Critic personas: Claude Code subagents, and claude.ai Project instructions.
- **standard/** — Baseline, the reference design system, and REQUIREMENTS.md.
- **tools/** — `brief_lint.py` (is a page brief ready?), `check_compatibility.py` (Not compatible / Minimum / Optimal, with the gaps), `design_context.py` (which design owns a file, and what it decided), `token_lint.py` (off-token values in UI code), `hooks.py` (runs both inside Claude Code), and `export_claude_design.py` (manifest → Claude Design System tokens).
- **templates/** — `page-brief.md`, the document you write for a new page; `claude-settings.json`, the hook config for your app repo, and `CLAUDE.md`, the required project file, with `{{…}}` placeholders the skill fills from your manifest.
- **examples/** — filled, working examples of every schema, all following one continuous scenario (ticket `DES-512`, a dashboard KPI summary) so you can trace one request through the whole pipeline.

## Platforms: Claude Code and Claude Design

The same manifest, skills and rubric run on both. `platform.targets` in the manifest says which; **`skills/platform-adapters.md`** maps every step to each platform.

| | Claude Code | Claude Design |
|---|---|---|
| Always-loaded context | `CLAUDE.md` | The default Design System's README (same template) |
| Tokens | Manifest values | Design System `tokens.json`, exported by `tools/export_claude_design.py` |
| Design drawn as | Code/markup | Design canvas artboards and clickable prototypes |
| Records (briefs, reports, index) | Repo files | A connected repo (recommended), or the design index as a Design System section |

To use Claude Design, set `platform.targets` to include `claude-design` and fill `color.resolved` with real color values, then export:

```
pip install pyyaml
python3 tools/export_claude_design.py design-system-manifest.yaml build/claude-design
```

It writes `project/tokens.json` in the Design System's format and checks roles without values, duplicate names, text below the legibility floor, and failing contrast pairs. See `examples/claude-design/project/tokens.json` for the Acme export.

## Personas: a Designer and an independent Critic

The agent can run as two personas, so the design isn't graded by the one who drew it:

- **`personas/claude-code/design-lead.md`**: runs the generation skill and hands every draft to the critic. It passes only file paths, never its own reasoning.
- **`personas/claude-code/design-critic.md`**: applies the audit rubric and returns the audit report. It has read-only tools, so it can't quietly fix what it's grading.
- **`personas/claude-ai/project-instructions.md`**: the same two roles for a claude.ai Project, as a Designer pass then an explicit Critic pass that re-reads everything from scratch.

To install in Claude Code, copy both files into your app repo's `.claude/agents/`, then ask for work as usual ("design PRD-031") or name one ("have the design-critic review this screen").

The personas set voice and hand-off only. Every rule still comes from the skills and the manifest.

## Required first: a project `CLAUDE.md`

Before the agent runs in your app repo, that repo needs a `CLAUDE.md` holding your design system's **tokens, brand rules, and critique criteria**. Claude Code loads it into every session, so every interaction follows the design system, even a one-line edit or a design question that never invokes the skill.

- **Template:** `templates/CLAUDE.md`. The skill fills it from your manifest. See `examples/CLAUDE.example.md` for the Acme version.
- **Version stamp:** its first line records the manifest version it was built from. The skill halts if the file is missing or the stamp doesn't match, and offers to generate or regenerate it.
- **Source of truth:** the manifest stays the full data; `CLAUDE.md` is the short, always-loaded summary. When the manifest changes, bump its version and regenerate `CLAUDE.md` in the same change.

## Pipeline order

1. **`schemas/ticket-brief.schema.json`** — structured extraction from a Jira ticket or PRD, including the `scopeTerms` and `surfaces` it touches. See `examples/ticket-brief.example.yaml` (ticket) and `examples/ticket-brief-prd.example.yaml` (PRD).
   - **Scope placement check** — before any design starts, the brief is compared against every project in the **`schemas/design-index.schema.json`** (example included) by shared terms, shared surfaces and shared priorities. Each required element is routed individually: to this project, as a revision of an existing design that already owns that surface, or here but reusing a related design's approved pattern. The result is a **`schemas/scope-overlap-report.schema.json`** — see `examples/scope-overlap-report.example.yaml`, where a PRD that looks like one new project turns out to be two revisions of existing designs.
2. **`schemas/design-system-manifest.schema.json`** — the project's design system as data (tokens, components, thresholds, policies). See `examples/design-system-manifest.example.yaml`. This is what makes the rest of the system generalizable to any design system — swap this file, same skills work elsewhere.
3. **`skills/design-principles.md`** — the fixed philosophy (simplicity, hierarchy, consistency, alignment, whitespace, mobile-first, motion, structural rationale) that generation and audit both answer to, plus two checkable sets of criteria: the **3-3-3 rule** (understood in 3 seconds, reached in 3 clicks, done in 3 minutes — walked for every core task and recorded as `glanceTest` / `taskPaths` in the design output) and **Wickens' 13 principles of display design** (perception, mental models, attention, memory).
4. **`skills/design-generation-skill.md`** — reads the brief + manifest, runs the reuse/similarity check against the component registry, files gap reports for anything missing, shapes layout/typography/color/motion from manifest tokens, and follows the Decision Protocol on consequential choices. Produces a `design-output` (schema + example included).
   - Along the way it may file a **`schemas/component-gap-report.schema.json`** (example included) for anything not in the registry, and — before that gap report's component can be approved for reuse — a **`schemas/component-verification-report.schema.json`** (two examples included: `StatTile` and `Button/icon-only`) confirming the new component is operational (every state implemented, accessible, token-compliant) and documenting *why* it was built that way.
5. **`skills/design-audit-rubric.md`** — runs automatically after every generation. 14 categories (including scope & cross-artifact integrity, the 3-3-3 usability rule, Wickens' 13 display-design principles, and mobile & dynamic components), `pass`/`minor-issues`/`major-issues`/`blocker` verdicts. `blocker` halts for a human; `major-issues` auto-revises and re-audits up to a configurable cap before escalating. Produces an **`schemas/audit-report.schema.json`** (example included).
6. **`skills/audit-presentation-template.md`** — the exact, fixed format audit findings are rendered in for a human (Phase 1 Critical / Phase 2 Refinement / Phase 3 Polish / Design System Updates Required / Implementation Notes). See `examples/audit-report-rendered.example.md` for what this looks like filled in.

7. **Design index update** (generation Step 12) — every artifact is registered with the exact versions it was built from. When one changes, its direct dependents are flagged `needs-review` (and projects sharing a pattern are flagged too); nothing is silently regenerated. See the flagged artifacts in `examples/design-index.example.yaml`.

## Still open

Jira ingestion (fetching a ticket automatically into a `ticket-brief`, e.g. via an Atlassian MCP connector) hasn't been built yet — right now a brief is assumed to already be structured, or extracted manually from raw ticket text per Step 1 of `design-generation-skill.md`.

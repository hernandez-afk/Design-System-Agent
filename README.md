# Design System Agent

**A harness for iterative, holistic design when developing with AI.** Every design, whether a person or an agent starts it, runs through the same loop: brief → scope → flow → design → audit → approval → build → verify. Each stage has a gate that can't be skipped, and all of it shares one memory of the product: the design-system manifest and the design index. People decide at the points that matter, and a feedback loop turns recurring findings into improvements to the design system itself. **See [HARNESS.md](HARNESS.md) for the operating model.**

## Install and cost

```
./install.sh /path/to/your-app --with-baseline   # skill, tools, agents, hooks; Baseline as a starting design system
```

It runs in **lite mode** by default (`harness.mode` in the manifest), built to keep credits low:
- **Tools do the checking.** `harness.py check --project ID --page page.html` runs every mechanical check in one call and prints only the failures, in about 250 tokens.
- **The model reads little.** It loads a ~1,000-token core skill (`skills/design-agent/SKILL.md`) and a ~600-token critic checklist. The long references are opened only when a step is unclear.
- **`CLAUDE.md` is about 400 tokens,** because it's loaded every turn.
- **Records come from short skeletons** (`harness.py new …`), and `harness.py record` keeps the design index. The model never reads the schemas.
- **One human stop per stage,** one critic pass, and at most one revision.

| Loaded per run | Before | Lite |
|---|---|---|
| Instructions | ~30,600 tokens | ~2,500 tokens |
| Schemas | ~16,600 | 0 (skeletons ~600) |
| `CLAUDE.md`, every turn | ~1,800 | ~400 |
| Mechanical checking | done by the model | ~250-token tool summary |

**Full mode** (`harness.mode: full`) runs everything: every record, the 14-category rubric and the presentation template. Use it for flagship work.

Its first job is **consistency**: the product stays consistent as it's built, because design context is present wherever it's worked on, in design and in development.

```
python3 tools/harness.py status              # every design's stage, gates and blockers
python3 tools/harness.py next --project ID   # what to do next
python3 tools/harness.py learn               # recurring findings → proposed system changes
```

## The core guarantee: consistency, with design context everywhere

The most important thing this system does is keep a product consistent while it's being built, by making sure **design context is always present in development**, not only when a design is being made. These are the guarantees, and what enforces each:

| Guarantee | While designing | While developing (Claude Code) |
|---|---|---|
| Every session knows the design system | Skill halts on a missing or stale `CLAUDE.md` / Design System README | `CLAUDE.md` loads every session. The session-start hook warns if it's stale. |
| Every piece of work knows the design that owns it | Scope check against the design index (Step 2b) | Code is linked to designs by `codePaths`. The first edit to a design's files shows its context. |
| Decisions are made once and reused | Inherited decisions, shared patterns | The design context lists the owning design's decisions. Contradicting one is raised as a design change. |
| Every design works on a phone; every component is dynamic | Mobile pass (`mobileCheck`) on every design; `dynamicBehavior` required to approve a component; rubric category 14 | The token lint flags fixed sizes that break on narrow screens |
| Every value is a token | Rubric category 3 | `token_lint.py` runs after every edit and sends off-token values back to fix |
| The same kind of element looks the same everywhere | Spacing roles and text styles; a consistency inventory in every critique | `consistency_check.py` compares each edit with the rest of its design, and gates the build |
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

The brief is then optimized in a standard way (**`skills/design-agent/reference/brief-optimization.md`**, generation Step 1) so it fits the design system and the output can be checked against it:

- **Lint:** `python3 tools/brief_lint.py brief.md` catches missing sections, placeholders, vague words, solution-first wording, lists with no amounts, missing states and untestable criteria.
- **Fit to the design system:**
  - vague words become rules ("pop" → the one primary action; "easy" → the 3-3-3 limits)
  - solutions become needs ("a dropdown" → "choose one of 3 frequencies"), so the reuse check picks the component
  - conflicts with the design system are listed for you to accept, never resolved silently
  - acceptance criteria are made testable, using the manifest's thresholds
- **Report and approve:** a `brief-optimization-report` shows every change, conflict and question. Nothing is designed until you approve it.
- **Checked in the output:** the design output lists each acceptance criterion as met or not, with evidence, and the audit blocks a design that fails one.

Your team's own terms can be added to the vocabulary in the manifest (`briefPolicy.vocabulary`). See `examples/page-brief.example.md` → `examples/brief-optimization-report.example.yaml` → `examples/ticket-brief-page.example.yaml`.

## Screenshots: reading them, and taking them

The agent reads screenshots (`skills/design-agent/reference/screenshot-review.md`): existing pages to audit, the current product for context in a brief, or a design system that only exists as images. A screenshot shows what something looks like, not what it's made of, so values read off an image are marked as estimates and are never blockers on their own.

It also takes its own. `python3 tools/screenshots.py page.html --out shots/` renders a page at the narrowest width, the phone, each breakpoint and desktop, plus 200% text, and **measures** what a picture can only estimate:
- sideways scrolling, and which element causes it
- touch targets that are too small
- text that's too small, clipped, or doesn't grow with text size
- the real padding and type of every component, checked against its spacing role and text style

The critic reads the screenshots and the measurements together. See `examples/rendered/`: a dashboard prototype with five planted problems. The tool finds all of them, plus an `h1` that doesn't match its text style. Its 320px screenshot looks fine but is really 546px wide, which only the measurement shows.

`--provided <images…>` records screenshots someone gives you, with their pixel sizes, and leaves the unknown context (viewport, pixel density, text size, state) as questions.

## Anti-AI design: say it once, choose the type, match the brand

Three things AI-made designs get wrong, each checked by a tool so it costs no extra reading:

- **Information said once.** The renderer flags any sentence or figure that appears twice on one screen, like "1,248 votes cast" in a card and "so far 1,248 people have voted" below it. If something matters enough to repeat, it becomes one stronger element. The same button on every card of a list, and one heading across states drawn side by side (`data-screen`, `data-artboard`, `data-state`), don't count. The critic catches the same thing said in different words (check 16).
- **As little as possible at a time.** Whatever stays on every screen (the top bar, sidebars, anything sticky) holds only the logo, the page title, navigation and controls. The renderer flags anything else there, like an "Admin" badge, a plan, "Production", or "Signed in as…". Those belong in the account menu. Where a role changes what someone can do, only that action is marked ("Admin only"). It also flags notices that restate who you are ("You are an admin, so…"). A real exception, like a live countdown during an event, is marked `data-essential`. `examples/rendered/chrome-test.html` has six planted cases, all caught.
- **Chosen type, not defaults.** Inter, Roboto, Arial, Poppins, DM Sans, Space Grotesk and system fonts are flagged in the manifest (`check_compatibility.py`) and on the page. The renderer also flags a font that doesn't load and quietly falls back. A new design system chooses a pair for the product's character from `skills/design-agent/reference/type-pairing.md`. A brand's required fonts are always allowed.
- **Brand guidelines, as a reference.** The project's own design system is always the default. Atari's guidelines are a reference system (`standard/brand/atari/`), used only for work that asks for them:
  - a brief that says to follow the Atari brand guidelines (`brandGuidelines: ["Atari"]` in the brief and the design index)
  - a page with `<meta name="brand-guidelines" content="Atari">`
  - a file with a `brand-guidelines: Atari` comment

  That work is designed, linted and checked against the Atari system instead of the project's. A page that only mentions Atari stays on the project's system. The one exception is an Atari logo, which follows the logo rules on any page.

  The **Atari system** is built from *ATARI Brand Guidelines V1.1* (June 2023):
  - Atari Red for primary actions, and exact palette colors only, since the palette is strict
  - Atari 1972 for headlines, Poppins Medium for everything else
  - the Baseline's spacing, components and behavior, which the guidelines don't cover

  It checks Optimal. The **profile** (`standard/brand/atari.yaml`) holds the checkable rules: the full palette, the type roles, the name ("Atari" or "ATARI"), and each logo's minimum size, clear space and colors. Mark each logo with `data-brand-asset="atari-fuji"` (or `-wordmark`, `-stacked`, `-box`, `-horizontal`, `-vertical`). Where the PDF contradicts itself, the profile says which reading it took (`CONFIRM` comments).

  Test pages: `examples/rendered/atari-brand-test.html` declares the guidelines and has nine planted mistakes, all caught. `examples/rendered/atari-mention-test.html` only mentions Atari, so it's checked against the Baseline; only its undersized logo is flagged. `examples/brand/acme-brand.example.yaml` shows a brand that is the product's own (`applies: always`).

## Purpose, fewer words, 3-3-3, cards and navigation, measured

- **Is it a page?** Every brief states its `purpose`: what's true once the user leaves. `tools/purpose_check.py`, run by the brief gate, flags a page that has no task and only shows information. That's usually better as a section of the page it's reached from, a panel, a tooltip or a notification, unless a `pageJustification` says why it's a page. It also flags anything that serves no ranked priority.
- **The right form for each piece of information.** Each required element gets an `infoType` and a `form`. A mismatch comes with the forms that fit: one number as a stat, change over time as a line, a state as a badge, steps as a stepper. See `skills/design-agent/reference/content-forms.md`.
- **Fewer words.** `contentPolicy` sets the limits: ≤ 30 words and 2 sentences per text block, ≤ 20 for the line under a title, ≤ 60 words before the first scroll at 320px, ≤ 250 per screen. The renderer measures them and flags information written as prose that has a better form:
  - figures in a sentence
  - "first… then… finally" steps
  - "click the blue button" instructions
  - a list written as a sentence
  - a table with one row

  Articles and legal text go in `[data-longform]` and are exempt.
- **3-3-3, measured where it can be:**
  - **3 seconds:** at 320px, the page title and the primary action must be on the first screen, with little to read before the first scroll, and only one primary action.
  - **3 taps:** counted from the user flow (`flow_check.py`).
  - **3 minutes:** estimated per screen from its words, fields and choices.

- **Cards and navigation.**
  - A front-facing card shows at most 5 pieces of information; the rest goes in its detail view.
  - Navigation keeps the most-used options at the top, at most 7 a level.
  - Every option is within 2 clicks.
  - Past 15 options, there must be a search.
  - Hidden options always sit behind a labelled control.
  - At most 12 controls appear on the first screen at 320px, with the rest nested behind one labelled control.

  The renderer measures all of these. The critic judges the order of the options, and whether settings and filters sit where they're used, show the current choice, and reset in one tap.

`examples/rendered/content-test.html` has ten planted text and 3-3-3 problems, and `examples/rendered/structure-test.html` six card and navigation problems. The renderer catches all of them.

## Edge cases, caught at the brief

Most edge cases are found in testing. The **edge-case sweep** (`skills/design-agent/reference/edge-case-sweep.md`) catches the obvious ones before anything is designed, the same way every time:

- **What the page depends on.** Every thing the page shows or acts on gets an owner for each part of its life: who creates it, where its data comes from, who changes it, what ends it. This is where the most expensive gaps hide. A voting page with no admin side to create the hackathon and import the games fails here.
- **Twelve lenses:** ecosystem, roles, setup, time, concurrency, integrity, scale, failure, ending, communication, privacy and access, plus your product's own (`briefPolicy.edgeCaseLenses`).
- **Every case decided:** handled here (it becomes an acceptance criterion, element, state or flow path), a **new brief** for a part of the product nobody briefed, out of scope with a reason, or a question.

`python3 tools/edge_case_check.py brief.yaml --index design-index.yaml` is the gate: the harness's brief stage doesn't pass until the sweep is complete with no open questions. See `examples/page-brief-voting.example.md` → `examples/ticket-brief-voting.example.yaml`: a voting brief that covered only the voter's side, and the two new briefs the sweep found (the hackathon admin, and results).

## The user flow: how a page connects to the product

Before any screen is laid out, the agent maps the **user flow** (generation Step 2c, `schemas/user-flow.schema.json`):

- **Entry points:** every way in (another page, an email link, a notification), what each link carries, and what happens when the user is signed out
- **One flow per core task:** every step and wait, how the user knows it's done, and the error, cancel, empty, not-found and permission paths
- **The way back and the way on:** no dead ends, including from deep links with no history
- **Integration changes:** anything an existing page needs to link to the new one. Changes to another design's page are proposed to that design's owner, never made quietly, and the design can't ship until they're accepted.

`python3 tools/flow_check.py flow.yaml --index design-index.yaml --brief brief.yaml` checks all of this, and `--mermaid` draws the flow. The design index keeps a **navigation map** of every link between pages, updated as each design ships. See `examples/user-flow.example.yaml`: the Notification preferences page, entered from an email link and from the Settings page (DES-420), which needs a new row.

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
- **standard/** — Baseline, the reference design system, REQUIREMENTS.md, and `brand/` (brand guidelines profiles, starting with Atari's).
- **tools/** — `harness.py` (stages, gates, next steps, learning), `screenshots.py` + `render/capture.js` (render, screenshot and measure a page; record provided screenshots), `consistency_check.py` (same element, same spacing and type, across files), `edge_case_check.py` (is the edge-case sweep complete?), `brief_lint.py` (is a page brief ready?), `flow_check.py` (user flow: dead ends, entry points, integration changes; `--mermaid`), `check_compatibility.py` (Not compatible / Minimum / Optimal, with the gaps), `brand_check.py` (warns when something meant to follow brand guidelines doesn't), `purpose_check.py` (is it a page, does everything serve its purpose, is each thing in the right form), `design_context.py` (which design owns a file, and what it decided), `token_lint.py` (off-token values in UI code), `hooks.py` (runs both inside Claude Code), and `export_claude_design.py` (manifest → Claude Design System tokens).
- **templates/** — `page-brief.md`, the document you write for a new page; `claude-settings.json`, the hook config for your app repo, and `CLAUDE.md`, the required project file, with `{{…}}` placeholders the skill fills from your manifest.
- **examples/** — filled, working examples of every schema, all following one continuous scenario (ticket `DES-512`, a dashboard KPI summary) so you can trace one request through the whole pipeline.

## Platforms: Claude Code and Claude Design

The same manifest, skills and rubric run on both. `platform.targets` in the manifest says which; **`skills/design-agent/reference/platform-adapters.md`** maps every step to each platform.

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
3. **`skills/design-agent/reference/design-principles.md`** — the fixed philosophy (simplicity, hierarchy, consistency, alignment, whitespace, mobile-first, motion, structural rationale) that generation and audit both answer to, plus two checkable sets of criteria: the **3-3-3 rule** (understood in 3 seconds, reached in 3 clicks, done in 3 minutes — walked for every core task and recorded as `glanceTest` / `taskPaths` in the design output) and **Wickens' 13 principles of display design** (perception, mental models, attention, memory).
4. **`skills/design-agent/reference/design-generation-skill.md`** — reads the brief + manifest, runs the reuse/similarity check against the component registry, files gap reports for anything missing, shapes layout/typography/color/motion from manifest tokens, and follows the Decision Protocol on consequential choices. Produces a `design-output` (schema + example included).
   - Along the way it may file a **`schemas/component-gap-report.schema.json`** (example included) for anything not in the registry, and — before that gap report's component can be approved for reuse — a **`schemas/component-verification-report.schema.json`** (two examples included: `StatTile` and `Button/icon-only`) confirming the new component is operational (every state implemented, accessible, token-compliant) and documenting *why* it was built that way.
5. **`skills/design-agent/reference/design-audit-rubric.md`** — runs automatically after every generation. 17 categories (including scope & cross-artifact integrity, the 3-3-3 usability rule, Wickens' 13 display-design principles, mobile & dynamic components, anti-AI design, brand guidelines, and content & purpose), `pass`/`minor-issues`/`major-issues`/`blocker` verdicts. `blocker` halts for a human; `major-issues` auto-revises and re-audits up to a configurable cap before escalating. Produces an **`schemas/audit-report.schema.json`** (example included).
6. **`skills/design-agent/reference/audit-presentation-template.md`** — the exact, fixed format audit findings are rendered in for a human (Phase 1 Critical / Phase 2 Refinement / Phase 3 Polish / Design System Updates Required / Implementation Notes). See `examples/audit-report-rendered.example.md` for what this looks like filled in.

7. **Design index update** (generation Step 12) — every artifact is registered with the exact versions it was built from. When one changes, its direct dependents are flagged `needs-review` (and projects sharing a pattern are flagged too); nothing is silently regenerated. See the flagged artifacts in `examples/design-index.example.yaml`.

## Still open

Jira ingestion (fetching a ticket automatically into a `ticket-brief`, e.g. via an Atlassian MCP connector) hasn't been built yet — right now a brief is assumed to already be structured, or extracted manually from raw ticket text per Step 1 of `design-generation-skill.md`.

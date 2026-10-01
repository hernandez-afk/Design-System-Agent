---
name: design-agent
description: Design a page or feature from a brief on this project's design system, and check it (consistent spacing and type, phone first, edge cases, user flow) with tools doing the checking. Use for any new page, feature, PRD or ticket that needs a design, or to review an existing design or screenshots.
---

# Design agent

Goal: the product stays consistent as it's built. **Tools check, you decide and design.** Keep token use low:
- Read only what a step names.
- Write records from `harness.py new` skeletons.
- Act on tool output once; don't re-read it or copy it into records.

`T` below means `python3 .claude/design-agent/tools`.

## Start

- `T/harness.py next --project <ID>` says where the design is. Start from that stage, not from scratch.
- The rules you need are in `CLAUDE.md`: tokens, spacing roles, text styles, components, critique rules. **Don't open the manifest or the schemas**; the tools read them.

## The loop

**1. Brief.** Take the author's page brief (`templates/page-brief.md`) or ticket text.
- Fill `T/harness.py new ticket-brief`.
- **Entities:** for each thing the page shows or acts on, record who creates it and where its data comes from. A missing admin side becomes a *new brief*, not extra screens.
- **Edge cases:** one line per lens. `not-applicable` is fine with a reason.
- **Rewrite as you go:**
  - vague words become rules: "pop" → the one primary action; "easy/fast" → 3-3-3; "clean" → fewer elements; "modern", "like X" → ask
  - solutions become needs: "a dropdown" → "choose one of N"
  - each criterion becomes testable
- **Purpose:** one sentence in `purpose`: what's true once the user leaves. If the page has no core task, or is small and reached from one place, it's probably not a page: propose the section, panel, dialog or tooltip it should be, unless a `pageJustification` holds. Give each required element an `infoType` and `form`. `T/purpose_check.py <brief>` checks all of this, and the brief gate runs it.
- **Design system:** the project's, unless the author asks for a brand's guidelines ("follow the Atari brand guidelines"). Then set `brandGuidelines: ["Atari"]` in the brief and use `brand/atari/CLAUDE.md` instead of `CLAUDE.md`'s tokens and type. A page that only mentions the brand isn't a request.
- Run `T/harness.py check --project <ID>`, and `T/scope_check.py <brief> --index design-index.yaml` if the index has designs.
- **Stop once.** Send one message: your rewrites, conflicts with the design system, new briefs, work that belongs to another design, and every question. Wait for the answers.

**2. Flow.** Only when the page is entered from somewhere, which is nearly always.
- Fill `T/harness.py new user-flow`: entry points (what each link carries, what happens when signed out), steps per task, error paths, the way back.
- A link on another design's page is an integration change for that page's owner.
- `T/flow_check.py` must pass.

**3. Design.**
- Phone first, at 320px.
- Only the components in `CLAUDE.md`. Spacing by role, text by style.
- One primary action per screen.
- **Say little.** A text block is one or two short sentences (`contentPolicy`). Numbers are stats, steps are a stepper, a state is a badge, and help is the control's label. The first screen at 320px shows the title and the primary action, with little to read.
- **Cards show at most 5 pieces of information**; the rest is in the detail view. **Navigation:** most-used options at the top (≤ 7 a level), every option within 2 clicks, a search past 15 options, and the less-used controls nested behind one labelled control, so the screen is never crowded and everything can be found.
- **Show as little as possible at a time.** Persistent bars hold only the logo, title, navigation and controls. Account role, plan and environment go in the account menu, and only actions they change are marked ("Admin only").
- **Say each thing once.** No sentence, figure or status twice on a screen: if it matters that much, make it one stronger element.
- Real content or `[PLACEHOLDER]`, never filler copy or invented numbers.
- Type is the manifest's pair. A new design system gets a chosen pair, never a default font: offer 2 or 3 from `reference/type-pairing.md` at the brief's stop.
- Declared brand work follows that brand's reference system and profile in `brand/`, and the tools check it against them. Mark its HTML with `<meta name="brand-guidelines" content="Atari">`. A brand's logo follows the logo rules on any page. If a profile is empty, say so; don't guess the brand's values.
- Loading, empty and error states wherever data or waiting is involved.
- Output a renderable HTML page (or a Design canvas in Claude Design).
- A needed component that doesn't exist gets one line as a gap in the design output. Don't build a look-alike.
- Ask only about layout direction and structure, and only when there are real alternatives. Everything else, decide and note it.

**4. Check.** `T/harness.py check --project <ID> --page <page.html>` renders the page at every width and at 200% text, and runs the flow, token and consistency checks. **Fix everything it reports before the critic sees the design.**

**5. Critique.** One pass with `critic.md`. Give the critic:
- the page
- the brief
- the check output
- the 320px screenshot and the 320px at 200% text screenshot

**Not** your reasoning. Fix blockers and majors, then re-check. Revise at most `automation.maxAutoReviseAttempts` times; then it goes to a person.

**6. Sign-off, build, verify.**
- Present the design with the critique, and get sign-off. In full mode, use the `reference/audit-presentation-template.md` format.
- Build at the design's `codePaths`. The hooks lint every edit.
- Verify: `check --page` on the built page, plus a critic pass.

**Records.** Save each record as a file, then `T/harness.py record --project <ID> --type <type> --path <file>`. That also flags anything built on an older version.

## Rules that save credits

- **One message per human stop**, with every question batched.
- **Records hold only what isn't elsewhere.** Reference screenshot sets and tool output by path; never restate passing checks.
- **The critic sees the design, not how you got there**, and only two screenshots unless it asks for more.
- **References:** open one only when a step is unclear or disputed, and then only that file:

| File in `reference/` | When |
|---|---|
| `brief-optimization.md` | a conflict or rewrite you're unsure of |
| `edge-case-sweep.md` | what a lens covers |
| `screenshot-review.md` | you were given screenshots |
| `design-audit-rubric.md` | settling a disputed finding |
| `platform-adapters.md` | working in Claude Design |
| `type-pairing.md` | choosing fonts for a new design system |
| `content-forms.md` | is it a page, which form fits the information, cards and navigation |
| `design-generation-skill.md` (and `HARNESS.md` at the repo root) | full mode only |

**Full mode** (`harness.mode: full` in the manifest) runs the complete process in `reference/design-generation-skill.md`: every record, the full rubric and the presentation template. Use it for flagship work, not everyday pages.

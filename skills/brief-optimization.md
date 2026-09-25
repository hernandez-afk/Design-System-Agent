---
name: brief-optimization
description: The standard way to turn a page brief (templates/page-brief.md), a PRD or a ticket into design-ready instructions — fitted to this project's design system, testable, and free of vague or solution-first wording. Runs as generation Step 1, before anything is designed; every change is shown to a person before it's used.
---

# Brief Optimization

A brief written in plain language is the right input: the person writing it shouldn't need to know the design system. But plain language is also where designs go wrong. "Make it pop" gets read as a new color, "add a dropdown" skips the reuse check, "intuitive" can't be checked, and a missing empty state becomes a blank screen. This skill turns the brief into instructions that **fit the design system and can be verified in the output**, and shows every change so nothing is quietly reinterpreted.

It never adds scope. Every optimized line traces to something in the original brief, or it's a question back to the author.

## Inputs

- The brief: a page brief (`templates/page-brief.md`), a PRD, or ticket text.
- The manifest, including `briefPolicy`.
- The design index, to spot related designs early. The full scope check is still Step 2b.

## The process

### 1. Lint

Run `python3 tools/brief_lint.py <brief>` if the brief is a page brief. It catches the mechanical problems: missing sections, template placeholders, vague words, solution-first wording, unbounded amounts, missing states, and untestable acceptance criteria. Fix what it reports in the optimized brief, not by editing the author's document.

### 2. Extract into the ticket-brief shape

Map the brief onto `schemas/ticket-brief.schema.json` (`sourceType: page-brief` for a page brief):

| Page brief section | Becomes |
|---|---|
| Purpose, Goals (ranked) | `priorities`, in the author's rank order, with `source: explicit` |
| What users need to do | `coreTasks`, each with its `entryPoint` |
| Content and data | `requiredElements` (with `targetCategory` and `estimatedVolume`) |
| States | `requiredElements` states, and the loading/empty/error needs they imply |
| Constraints | `constraints` |
| Acceptance criteria | `acceptanceCriteria`, each linked to a priority or task |
| Out of scope | `outOfScope` |
| Related pages and designs | `scopeTerms` and `surfaces` hints for the scope check |
| Open questions | `openQuestions` |

Anything you inferred rather than read gets `source: inferred` and is listed in the report, so the author can confirm it.

### 3. Fit it to the design system

This is the optimization itself. Each rule turns plain language into something the design system already has a way to express.

1. **Translate vague words into rules.** Replace each one with the rule or token it actually means, using the vocabulary map below plus the manifest's `briefPolicy.vocabulary`. If a word maps to nothing, like "modern" or "sleek", ask what outcome the author wants. Never guess a style.
2. **Turn solutions into needs.** "A dropdown to pick frequency" becomes "choose one of 3 frequencies." The reuse check (Step 3) then finds the right approved component instead of building the one that was named. Keep the author's suggestion in the report as a note.
3. **Name the components that already fit.** For each required element, list the approved components likely to cover it. This is a hint for Step 3's scoring, not a decision.
4. **Surface conflicts with the design system, don't resolve them silently.** Two "main buttons" conflict with `maxPrimaryActionsPerScreen`. A banned style conflicts with `brandExclusions`. A requested color isn't in the palette. List each as a conflict with the rule it breaks, and a proposed resolution for the author to accept.
5. **Make every acceptance criterion testable.** Each needs a subject, an action and a measurable result, tied to a manifest threshold where one exists ("in 3 taps or fewer", "at 320px", "at 200% text"). Rewrite vague ones, and keep the author's meaning.
6. **Fill the gaps the design system requires.** If the brief doesn't say, add a question or an inferred item for:
   - loading, empty, error and success states
   - amounts for lists (pagination at `listPaginationThreshold`)
   - where each task starts
   - which goal is #1, when two read as equal

   Mobile and accessibility are always required, so don't ask whether they're wanted. Note the specific phone considerations instead.
7. **Point at related designs early.** If the brief's terms or surfaces match design-index projects, name them. Step 2b decides; this just avoids surprises.

### 4. Report, and wait

Write a `brief-optimization-report` (`schemas/brief-optimization-report.schema.json`). It includes:
- every change, from the original wording to the optimized wording, and why
- every conflict, with its proposed resolution
- every inferred item
- every open question
- a readiness verdict

Then apply `briefPolicy.approvalBeforeGeneration`. If it's true (the default), show the report and **wait for the author to accept, edit or answer**. Only the accepted, optimized ticket brief goes to Step 2.

| Readiness | Meaning | What happens |
|---|---|---|
| `ready` | Nothing open. Every criterion is testable and every conflict has an accepted resolution. | Continue once the author approves |
| `needs-answers` | Open questions or unconfirmed conflicts | Ask. Don't design yet. |
| `not-ready` | No purpose or goals, or template placeholders still in it | Return it to the author with the lint output |

## Vocabulary map

The built-in translations. Extend it for your product in `briefPolicy.vocabulary`: for example `"hero": "Card/feature"`, or a term your team uses for a pattern.

| The brief says | It means, in this system |
|---|---|
| pop, stand out, eye-catching, prominent | Hierarchy: this is the one primary action (`maxPrimaryActionsPerScreen`), with contrast from `accents.primary`. Not a new color. |
| clean, minimal, simple, uncluttered | Simplicity Is Architecture + Whitespace Is a Feature: the minimum elements, roomier spacing steps |
| intuitive, easy, user-friendly, obvious | 3-3-3: understood in `glanceSeconds`, reached in `maxClicksToCoreTask`, done in `maxCoreTaskMinutes` |
| fast, quick, instant | 3-3-3 time limit, plus a loading state (`motionUsagePolicy.requireLoadingAnimation`) |
| brand color, on-brand, our colors | `accents.primary` / `accents.secondary`, used per `color.usagePolicy` |
| big, bold, large (text) | A named type-scale step and weight from `typography` |
| mobile-friendly, responsive | Already required (Mobile at All Times). Note the phone-specific needs instead. |
| accessible | Already required (`accessibility.level`). Note anything beyond it. |
| modern, sleek, fresh, premium | No rule. Ask what outcome it should produce. |
| like [another product] | No rule. Ask what about it matters (rubric category 6: derivative thinking). |
| etc., and so on, various | Unbounded. Ask for the full list or a count. |

## What this skill never does

- Adds features, goals or content the brief didn't ask for. Gaps become questions or clearly marked inferred items.
- Resolves a conflict with the design system on its own. The author accepts the resolution.
- Keeps a solution-first instruction as a requirement. It becomes a need, with the suggestion noted.
- Starts the design before the author approves the optimized brief, when `approvalBeforeGeneration` is true.

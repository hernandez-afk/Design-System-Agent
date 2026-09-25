# The design harness

This repository is a **harness for iterative, holistic design when developing with AI**. Every design, whether a person or an AI agent starts it, runs through the same loop:
- the same stages, with gates that can't be skipped
- one shared memory of the product (the manifest and the design index)
- people deciding at the points that matter
- a feedback loop that makes the design system better each time round

The goal is the one the whole system serves: **the product stays consistent as it's built, because design context is present wherever it's being worked on.**

```
          ┌────────────────────────── learn: recurring findings → proposed system changes ──────────────────────────┐
          ▼                                                                                                          │
  manifest + design index  ──►  brief ─► scope ─► flow ─► design ─► audit ─► approval ─► build ─► verify ─► live ──┘
  (the shared memory)             ▲        ▲       ▲        ▲         │                     ▲
                                  └────────┴───────┴────────┴─────────┘                     │
                                   a changed record sends the design back to that stage     └── token lint + design context on every edit
```

## Stages and gates

A design's stage is **worked out from its records**, never typed in: it's the first stage whose gate doesn't pass. `python3 tools/harness.py status` shows every design's stage, gates and blockers. `python3 tools/harness.py next --project ID` says what to do next.

| Stage | What happens | Gate: what must be true to move on | Who decides | Tools |
|---|---|---|---|---|
| **brief** | A page brief, PRD or ticket is optimized to fit the design system | Optimization report is `ready` and the author approved it | The author | `brief_lint.py`, `skills/brief-optimization.md` |
| **scope** | The brief is placed against existing designs | Scope report exists; overlaps have a human decision | A person, when there's overlap | Generation Step 2b |
| **flow** | Entry points, flows, the way back, integration changes | `flow_check.py` passes with no errors | — | `flow_check.py` |
| **design** | Reuse check, structure, phone-first layout, 3-3-3 and the mobile pass | Design output has its task paths, glance test and mobile check | A person, at each Decision Protocol choice | Generation Steps 3–10 |
| **audit** | The independent critic applies the 14-category rubric | Latest verdict is `pass` or `minor-issues` | The critic; blockers go to a person | `design-critic` persona |
| **approval** | Sign-off, with everything the design depends on settled | Signed off; every proposed component verified; every integration change accepted by its owner | A person, and the owners of any linked designs | — |
| **build** | The design is implemented at its `codePaths` | Code exists and the token lint is clean | — | Hooks, `token_lint.py`, `design_context.py` |
| **verify** | The built UI is audited against the design | Implementation review (`audit-report`, mode `implementation`) is `pass` or `minor-issues` | The critic | `design-critic` persona |
| **live** | Shipped, and watched | Any change to one of its records sends it back through the loop | — | Session-start hook |

## Iteration

Nothing in the harness is done once. Any record can change: a brief gets a new requirement, a shared pattern is revised, another design adds a link. When one does, change propagation flags every record built on the old version as `needs-review`, and the design **falls back to the stage of the earliest flagged record**. `status` shows it with ↺ and the reason, and `next` says what to revise. The rest of the loop is then re-run from there, with the same gates, so a change never skips the audit it would have needed the first time.

## Holistic

No design is worked on alone:

- **The scope check** sends work to the design that already owns it.
- **The user flow** records how a design connects to the rest of the product. Any change it needs on another design's page is proposed to that design's owner.
- **The design index** holds every design, the code it owns, its decisions and the product's navigation map.
- **`status`** shows, for each design, what it's waiting on from others and what others are waiting on from it ("⇠ waiting on you").
- **Shared patterns** keep designs that share an interaction identical, and a change to one flags the others.

## Learning

`python3 tools/harness.py learn` reads every audit, implementation review, brief-optimization report and gap report, and proposes changes to the design system itself:
- a finding that recurs across designs → a guardrail (a token, a baseline component, a `CLAUDE.md` rule or a lint check), so it can't recur
- a brief conflict that recurs → clearer guidance in the page-brief template or `CLAUDE.md`
- a component requested by several designs → a baseline component
- vague terms that keep being rewritten → entries in `briefPolicy.vocabulary`

Each is a proposal. A person accepts it, the manifest's version is bumped, and `CLAUDE.md` is regenerated and the Design System re-exported. That version bump flags whatever the change affects, and the loop carries on.

## People in the loop

The harness automates checks and bookkeeping, not judgment. People decide:
- the optimized brief
- scope overlaps
- every consequential design choice
- blockers
- sign-off
- integration changes to their designs
- every proposed change to the system

Nothing that needs a person is ever marked done by an agent.

## Running it

| | Claude Code | Claude Design / claude.ai |
|---|---|---|
| Stages | The `design-lead` persona runs them; `harness.py next` says which | The Project instructions run the same stages in order, following this document |
| Gates | Checked by the tools (`harness.py`, `flow_check.py`, `brief_lint.py`, `token_lint.py`) | Checked by the Critic pass. The tools need a connected repo. |
| Shared memory | Manifest and design index in the repo | The same files in a connected repo, or the design index as a Design System section |
| Between runs | Hooks: session start shows each design's stage; edits get design context and the token lint | The default Design System keeps every new canvas on-system |

## Adopting it on an existing product

Designs that shipped before the harness don't have every record. The harness treats their missing early records as **backfill**, not blockers:
- `status` shows them, marked "backfill when it next changes"
- only failed or out-of-date gates decide where a shipped design stands

The first time one changes, it goes through the loop from the stage the change affects, and its records fill in as it does.

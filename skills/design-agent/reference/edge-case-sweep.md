---
name: edge-case-sweep
description: The standard edge-case sweep run on every brief during brief optimization (generation Step 1), before anything is designed. It catches the obvious gaps early — above all the parts of the product a page depends on but nobody briefed, like the admin side that creates what users vote on, or where the data comes from. Every case found is decided: handled here, a new brief, out of scope with a reason, or a question.
---

# Edge-Case Sweep

Most edge cases are found in testing, after the design is built, when they're most expensive. The sweep doesn't claim to find them all. It finds **the obvious ones, every time**, by asking the same questions of every brief, so they aren't left to whoever happens to think of them.

The most expensive gaps aren't odd screen states. They're **missing parts of the product**. A voting page needs someone to create the thing being voted on, a way to get the entries in, and somewhere to see the results. None of that is on the voting page, so none of it is in the voting brief, and it's discovered when someone asks "how do we set up the next one?" The first lens exists for exactly that.

## Inputs

- The brief, including its **"What this page depends on"** section (`templates/page-brief.md`)
- The design index, to find existing designs that already cover a need
- The manifest's `briefPolicy` (`requireEdgeCaseSweep`, and any product-specific `edgeCaseLenses`)

## Step 1: The things the page depends on

List every **entity** the page shows, acts on or needs: the things with a life of their own (a hackathon, a game, a vote, a team). For each, record who handles each part of its life, and where that happens:

| Operation | The question |
|---|---|
| **create** | Who creates it, and on which page? |
| **source** | Where does its data come from: typed in, imported, an integration, a sync? How often, and what if it's late or wrong? |
| **update** | Who can change it after it exists? |
| **publish** | Who makes it visible or opens it? (Only when it has a draft or closed state.) |
| **close** | What ends it: a person, a date, a condition? |
| **delete** | Can it be removed or archived, and by whom? |

Each operation is handled by one of:
- **`this-project`:** this design handles it
- **`existing-design`:** an existing design in the index handles it (give its ID)
- **`new-brief`:** nothing handles it yet, so a separate brief must be opened (give it a title)
- **`out-of-scope`:** deliberately not handled (give the reason)
- **`question`:** unknown, so ask the author

**Nothing is left blank.** In the hackathon example, "create hackathon: `new-brief`, *Hackathon admin*" and "game source: `question`, where do games come from?" are exactly the gaps this step is for.

## Step 2: The lenses

Go through every lens and record what it finds, or `not-applicable` with a reason. A lens with no entry counts as skipped, and the checker treats it that way.

| # | Lens | Ask |
|---|---|---|
| 1 | **Ecosystem** | Covered by Step 1: every entity has an owner for each part of its life. What's upstream of this page (setup, data), and what's downstream (results, reports)? |
| 2 | **Roles** | Who else touches this: admins, moderators, judges, guests, signed-out visitors, support? What does each see, and what happens when someone without permission arrives? |
| 3 | **Setup and first run** | What must exist before the page is useful? What does the very first user see, before there's any data? |
| 4 | **Time** | Before it opens, while it's open, after it closes; a deadline passing mid-task; time zones; scheduled changes |
| 5 | **Concurrency** | Two people at once, stale data, live updates, conflicting edits, counts changing while you look |
| 6 | **Integrity and abuse** | Duplicates (voting twice), self-interest (voting for your own entry), fraud, bots, rate limits, ties |
| 7 | **Scale** | Zero, one, many, too many; very long or missing content, missing images |
| 8 | **Failure and recovery** | What fails, what the user can do about it, undo, appeals. The flow's alternate paths cover the screen side. |
| 9 | **Ending and aftermath** | Results, archiving, export, what users see afterwards, reopening |
| 10 | **Communication** | Who is told what, and when: opening, reminders, closing, results, changes |
| 11 | **Privacy and compliance** | Personal data shown or stored, consent, who can see whose data, retention, age limits |
| 12 | **Access and devices** | Already required by the design system (mobile, accessibility). Note only cases specific to this product, like voting on a phone at the event itself. |

Add your product's own lenses in `briefPolicy.edgeCaseLenses`, for example "content ratings" for a games platform.

## Step 3: Decide every case

Each case gets a disposition:

| Disposition | Means | What happens |
|---|---|---|
| `in-scope` | This design handles it | It becomes an acceptance criterion, a required element or state, or a flow path. `action` says which. |
| `new-brief` | It needs its own design | Listed in the report's `newBriefs`, and opened as a separate page brief. The scope check links the two. |
| `out-of-scope` | Deliberately not handled | Needs a reason the author confirms, and goes into the brief's `outOfScope` |
| `question` | Unknown | Goes to the author. The brief isn't ready while any are open. |
| `not-applicable` | The lens doesn't apply | Needs a reason |

Then run `python3 tools/edge_case_check.py <ticket-brief> --index <design index>`. It checks that:
- every entity operation is decided
- every design it names exists in the index
- every lens is covered
- every in-scope case points to something in the brief
- no question is still open

## What this sweep never does

- **Quietly widens the design.** A missing admin side becomes a new brief, not extra screens bolted onto this one.
- **Invents answers.** An unknown data source is a question, not an assumption.
- **Replaces testing.** It catches the obvious gaps early. Edge cases found later, in the review of the built UI, go into the harness's learning loop: `harness.py learn` proposes each one as a new lens question, and once a person accepts it, the sweep asks it next time.

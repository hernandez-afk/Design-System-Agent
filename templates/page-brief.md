# Page brief: [page name]

<!-- Write in plain language; you don't need to know the design system. The agent's
     brief optimization (skills/brief-optimization.md) turns this into design-ready
     instructions and shows you every change before designing.
     Check it first:  python3 tools/brief_lint.py <this file>
     Replace every [bracketed] placeholder and delete these comments. -->

## Purpose

[One or two sentences: what this page is for, and what should be true once the user leaves it.]

<!-- Good: "Let team admins decide which events send email, so they stop getting alerts they ignore."
     Not: "A modern, clean settings page." That's a look, not a purpose. -->

## Users and context

- **Who:** [who uses it, and how often]
- **Device:** [mostly phone, desktop, or both. Every page is designed phone-first anyway, so say what's typical.]

## Where it fits

- **Arrives from:** [every way in: a menu or settings row, a link in an email, a notification, another page]
- **Goes next:** [where users go once they're done]
- **Pages that should link here:** [existing pages that need a new link or button to this page]

<!-- This becomes the user flow (generation Step 2c). Links on other pages are
     changes to those pages' designs, so name them here rather than assuming them. -->

## Goals (ranked)

1. [The most important outcome. This decides the page's one primary action.]
2. [Next most important]

<!-- Rank them. Two goals can't both be #1. Outcomes, not features:
     "Users can turn off an alert in under a minute", not "add a toggle list". -->

## What users need to do

- [Task, in the user's words] — starts from: [where they begin]
- [Task] — starts from: [where they begin]

<!-- Each task is checked against the 3-3-3 rule: understood in 3 seconds,
     reached in 3 clicks, done in 3 minutes. Say what they need, not which
     control to use: "choose how often" rather than "a dropdown". -->

## Content and data

- [What's shown, with rough amounts: "about 12 event types in 3 groups", "up to 200 rows, growing"]
- [Where it comes from, and anything that changes while the page is open]

## States

- **Loading:** [what's slow, if anything]
- **Empty:** [what a new user with no data sees]
- **Error:** [what can fail, and what the user can do about it]
- **Success:** [how the user knows it worked]

## Constraints

- [Deadlines, technical limits, legal or copy requirements, things that must not change]

## Acceptance criteria

- [A testable statement: "An admin can turn off all email for one event type in 2 taps or fewer from the page."]
- [Given … when … then …, if that's easier]

<!-- Each one must be checkable by looking at the design: numbers, "can", "must", "within".
     "Easy to use" can't be checked; "done in under a minute by a first-time user" can. -->

## Out of scope

- [What this page deliberately doesn't do, so it isn't designed in]

## Related pages and designs

- [Existing pages or designs this must stay consistent with, or might overlap with]

## Open questions

- [Anything you don't know yet. Better listed here than guessed.]

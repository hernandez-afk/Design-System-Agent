# Page patterns: what a kind of page implies

A brief rarely says everything its page needs. "Build a questionnaire" is a **builder**, and every builder needs the same things: whose it is, adding, editing in place, reordering, duplicating, deleting with undo, previewing, saving and publishing. `tools/pattern_check.py` recognizes the pattern from the brief's words and lists what it implies. The brief names it (`pagePattern`) and decides each capability (`patternDecisions`: in-scope, out-of-scope, new-brief or question). The brief gate runs the check, so nothing implied is forgotten.

## Builder (questionnaire, form, survey, quiz, template, page builder)

**Ask first: whose is it?** One per what: each edition, event, team or user builds their own. That decides where the builder is reached from, who can edit it, and what "start from a copy" copies.

**The layout, like Google Forms: minimal, and calm when long.**
- One column of item cards, in order. Each card shows the item itself (its question and type), nothing more.
- **Only the selected item shows its tools:** type, required, duplicate, delete and move, with the rarely used ones in its "⋯" menu. Every other item shows its content and a drag handle. The renderer flags tools on every item.
- **Reorder by dragging, and always by Move up / Move down** in the item's menu, for keyboard and touch (WCAG 2.5.7). The renderer flags drag-only lists.
- **Add** at the end, and after the selected item.
- **Edit in place:** typing into the card changes it. No separate edit screen, and no Save button: it autosaves, and says so next to Preview and Publish ("Draft · saved", or that saving failed).
- **Delete with undo**, not a confirmation dialog.
- **Preview** shows it as the person answering will see it, on a phone.
- **Empty:** the first item is one tap away, with "start from a copy of the last one" when there is a last one.
- **Decide what happens after answers exist:** editing a question that has answers either keeps old answers under the old wording, or is blocked. It's a question for the author, never a silent choice.

Reference: `examples/rendered/questionnaire-builder.html` (passes the checks). Brief: `examples/ticket-brief-questionnaire.example.yaml`.

## The other patterns

| Pattern | Recognized by | It implies |
|---|---|---|
| Voting | vote, poll, ballot, rank | who can vote, vote limits, changing a vote, opening and closing, who sees results |
| Wizard | onboarding, sign up, checkout, setup, step by step | progress, going back keeps data, resuming later, errors per step, review before submit |
| List | browse, list, directory, catalog, library | search or filter, sort, many items, empty and no results, what opening an item shows |
| Settings | settings, preferences, notifications | each setting's current value, applies instantly or on save, defaults, who can change it |
| Dashboard | dashboard, overview, analytics, metrics | the period and changing it, how current it is, no data and loading, what a number opens |

A page can be more than one pattern (`pagePattern: [list, builder]`). The full list of capabilities and the words that suggest them are in `tools/pattern_check.py`.

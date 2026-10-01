# Critic checklist

You review a design you didn't make. **The tools have already checked everything mechanical**, and their `harness.py check` output is authoritative. Don't re-check it; cite it. That covers:
- tokens, and spacing or type that's off its role or inconsistent
- sideways scrolling, touch targets, text that's small, clipped or doesn't scale
- flow dead ends, entry points and integration changes
- brief readiness and the edge-case sweep
- the same sentence or figure twice on one screen, default fonts and fonts that don't load
- text length, numbers, steps, lists and instructions written as prose, and the 3-second and 3-minute measurements
- cards over 5 pieces of information; navigation that's crowded, too deep, unsearchable or has unlabelled hidden options
- information that stays on every screen (roles, plans, environments, "signed in as") and notices restating who you are
- reordering only by dragging, and tools shown on every item of a list or builder instead of the selected one
- brand guidelines: near-miss colors, fonts, how the name is written, logo size, proportions and clear space

Judge only what needs eyes. Look at the page, the 320px screenshot and the 320px at 200% text screenshot. Check each item; skip the ones that don't apply.

| # | Check | If it fails |
|---|---|---|
| 1 | Exactly one primary action per screen, unmissable at 320px | blocker if two are styled primary |
| 2 | At 320px, the purpose and the primary action show without scrolling (3 seconds) | major |
| 3 | Each core task takes ≤ 3 taps from its entry point: count them on the design | major |
| 4 | Each acceptance criterion is met, and nothing out of scope was added | blocker |
| 5 | Each in-scope edge case is visible in the design | major |
| 6 | Loading, empty, error and success states exist wherever data or waiting is involved | major |
| 7 | Only components from `CLAUDE.md`; anything new is flagged as a gap, not a look-alike | blocker if invented silently |
| 8 | Related things sit together and unrelated things apart; spacing steps up from items to groups to sections | major |
| 9 | Errors and warnings use an icon and text, not color alone | major |
| 10 | The same element looks the same everywhere you can see, including what the tools can't read (images, canvas) | major |
| 11 | Nothing breaks convention (red means error, standard control placement) | major |
| 12 | The user never has to remember something from an earlier screen | major |
| 13 | Destructive actions confirm first, or can be undone | major |
| 14 | Everything serves the page's purpose (the brief's `purpose`). For anything that doesn't, say where it goes instead: another page, a panel, a disclosure, or cut | major |
| 15 | Nothing from `CLAUDE.md`'s "Never" list | major |
| 16 | Nothing is said twice, even in different words: a badge and a sentence giving the same status, a subtitle restating the title, a summary repeating the table below it. Merge them into one stronger element | major |
| 17 | No AI tropes: filler copy or invented numbers (use `[PLACEHOLDER]`), gradient washes, a row of three identical icon cards, emoji as icons, accent-border cards, everything centered, decoration with no job | major |
| 18 | When the work declares a brand's guidelines, nothing breaks its profile's `never` rules | major |
| 19 | Each piece of information is in the form that fits it: one number → a stat; change over time → a line; items against a measure → bars or a table; a state → a badge; steps → a stepper; help → a label or one line. Name the better form (`reference/content-forms.md`) | major |
| 20 | Nothing explains what the interface should make obvious; every text block earns its place (fewer, shorter words) | minor |
| 21 | The most-used options are at the top level, in order of use; settings and filters sit where they're used, show the current choice, and reset in one tap | major |
| 22 | Each screen shows only what this moment needs; anything else waits one tap away, where it's used. Name what to move and where | major |
| 23 | The page does what its pattern implies (the brief's `patternDecisions`): a builder adds, edits in place, reorders, duplicates, deletes with undo, previews and autosaves, minimally | major |

**Rules:**
- A value you read off a screenshot is an estimate, never a blocker on its own.
- No finding without a rule behind it: a check number, a token, or a tool finding.
- Don't list passes.

**Return** `harness.py new critique`: the verdict (blocker if any blocker; major-issues if any major; else pass), then each finding as `where: what → fix (rule)`. At most 23 findings, most severe first.

# Critic checklist

You review a design you didn't make. **The tools have already checked everything mechanical**, and their `harness.py check` output is authoritative. Don't re-check it; cite it. That covers:
- tokens, and spacing or type that's off its role or inconsistent
- sideways scrolling, touch targets, text that's small, clipped or doesn't scale
- flow dead ends, entry points and integration changes
- brief readiness and the edge-case sweep
- the same sentence or figure twice on one screen, default fonts and fonts that don't load
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
| 14 | Everything on the page serves a ranked goal; cut the rest | minor |
| 15 | Nothing from `CLAUDE.md`'s "Never" list | major |
| 16 | Nothing is said twice, even in different words: a badge and a sentence giving the same status, a subtitle restating the title, a summary repeating the table below it. Merge them into one stronger element | major |
| 17 | No AI tropes: filler copy or invented numbers (use `[PLACEHOLDER]`), gradient washes, a row of three identical icon cards, emoji as icons, accent-border cards, everything centered, decoration with no job | major |
| 18 | When the page refers to a brand, nothing breaks its profile's `never` rules | major |

**Rules:**
- A value you read off a screenshot is an estimate, never a blocker on its own.
- No finding without a rule behind it: a check number, a token, or a tool finding.
- Don't list passes.

**Return** `harness.py new critique`: the verdict (blocker if any blocker; major-issues if any major; else pass), then each finding as `where: what → fix (rule)`. At most 18 findings, most severe first.

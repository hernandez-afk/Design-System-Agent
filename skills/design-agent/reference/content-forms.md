# Content forms: is it a page, is each thing shown the right way, and can people find it?

Every page has one purpose: what's true once the user leaves it (the brief's `purpose`). Everything on the page serves that purpose, in the form that shows it fastest. `tools/purpose_check.py` checks the brief. The renderer (`tools/screenshots.py`) flags text that's too long and information in prose that has a better form.

## Is it a page?

| The brief has… | Usually better as | Keep it a page when |
|---|---|---|
| No core task, only information | A section of the page it's reached from, a panel or drawer, a tooltip, or a notification | People come back to it on its own, or other pages link to it (`pageJustification`) |
| One small task, reached from one place | A dialog, drawer or inline section where it's reached from | It's too big to fit there, or it has its own address people share |
| The same job as an existing design's page | A revision of that design (the scope check routes it) | Never: extend the existing page |

## The right form for the information

Set each required element's `infoType` and `form` in the brief. A form that doesn't fit gets the forms that do.

| Information (`infoType`) | Show it as | Not as | Why |
|---|---|---|---|
| One number (`single-value`) | stat, label-value pair, badge | table, chart, sentence | It's read at a glance as a number |
| Items against a measure (`comparison`) | bar chart, table | sentence, cards | Differences are seen side by side |
| Change over time (`trend`) | line chart, sparkline next to the stat | table, sentence | A trend is a shape |
| A share (`part-to-whole`) | stacked bar, stat with % | sentence, table | A share reads as a proportion |
| A state (`status`) | badge, inline alert (icon and text) | sentence, card | One word and an icon |
| Steps (`sequence`) | stepper, numbered list, timeline | paragraph | Steps are followed in order |
| Items to scan (`list`) | list, table | sentence | Scanned, not read |
| Many items, same fields (`records`) | table, list | cards, paragraphs | Compared in columns |
| Help (`explanation`) | the control's label, one helper line, tooltip, disclosure | paragraphs above the content | The interface explains itself; the rest waits until asked |
| Rarely needed (`reference`) | disclosure, link, another page | always-visible text | Out of the way |
| Up to 5 options (`choice-few`) | radio group, segmented control | select | Options compared visibly |
| Many options (`choice-many`) | select, combobox | radio group | Wouldn't fit |
| On or off (`toggle`) | switch, checkbox | select, radio | One control |

## Signals the renderer finds in text

| Signal | Becomes |
|---|---|
| More than `contentPolicy.maxNumbersInProse` figures in a sentence | Stats, a table or a chart |
| "First… then… finally" | A stepper or numbered list |
| "Click the blue button…" | A clear label, one helper line, or the empty state |
| "a, b, c and d" | A list |
| A table with one row or one column | Label-value pairs, or a list |
| A block over `maxWordsPerBlock`, or an intro over `maxIntroWords` | One short sentence; the rest behind a disclosure or on another page |
| Over `maxWordsFirstScreen` before the first scroll at 320px | Cut, so the title and primary action are found in 3 seconds |

Long-form text that is the purpose (an article, legal terms, a help page) goes in `[data-longform]` and is exempt.

## Cards and boxes: at most 5 pieces of information, and few buttons

A front-facing card (a game, a product, a person, a report in a list) shows at most `compositionHeuristics.maxCardInformationAreas` (5) separate pieces of information. Count text, images and badges; a table or list inside counts once; actions don't count. Keep the ones that serve the page's purpose and help someone choose. The rest goes in the detail view the card opens.

**Buttons:** at most `maxRepeatedCardActions` (3) on a card that repeats on screen, and `maxCardActions` (5) on any single box. Repeated cards multiply their buttons: 10 cards with 4 buttons is 40 buttons on one screen. Keep the main one or two on the card ("Open", "Vote"), and put the rest (share, archive, delete) in its "⋯" menu or the detail view. A selected item being edited may show its full tools.

The renderer counts both, for anything named a card or tile and anything drawn as a box (a border all round, or a shaded, rounded panel).

## Navigation and controls: few on screen, everything findable

- **Most-used first.** The top level holds the most-used options, in order of use from the brief's core tasks, at most `navigationHeuristics.maxItemsPerLevel` (7). Everything else is grouped one level down, under a label that says what's inside.
- **Few clicks.** Every option is within `maxClicksToAnyOption` (2) clicks of the navigation, counting the menu button when it's collapsed.
- **Findable.** Hidden options always sit behind a labelled control (a button with `aria-expanded`, or `<details><summary>`). Navigation hidden at a width always has a control that opens it. More than `searchWhenOptionsOver` (15) options means a search.
- **Never crowded.** At most `maxVisibleControls` (12) controls on the first screen at 320px. Less-used controls are nested behind one labelled control ("Filters", "More", "Settings").
- **Easy to customize.** Settings and filters people change often sit where they're used, one tap away. The current choice is always visible (a chip, a label on the control), and one control resets it. Personal choices, like pinned items or a saved view, are kept.

The renderer measures the first four. The critic judges the order and the customization.

## Show as little as possible at a time

What's on screen is what this moment needs. Everything else is one tap away, in the place it's used.

- **Persistent bars hold only what every screen needs.** The top bar, sidebars, and anything fixed or sticky keep the logo, the page title, navigation and controls. Nothing else, unless every screen truly needs it (a live countdown during an event): mark that `data-essential`. The renderer flags the rest.
- **Account details live in the account menu.** A role ("Admin"), a plan ("Pro"), an environment ("Production"), or "Signed in as…" isn't shown on every screen. Where it changes what someone can do, mark that action instead ("Admin only" on the one admin action), or show the admin tools themselves, which say it already.
- **No notices restating who you are** ("You are an admin, so…"). The tools that only admins see are the signal.
- **Context appears where it's used:** a filter's current value on the filter, a deadline next to the action it limits, a status on the item it describes.

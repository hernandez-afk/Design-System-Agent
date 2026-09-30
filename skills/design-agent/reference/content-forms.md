# Content forms: is it a page, and is each thing shown the right way?

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

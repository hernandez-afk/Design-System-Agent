---
name: screenshot-review
description: How the agent reads screenshots, both ones people give it (existing pages, a product to learn from, a design system to extract) and ones it takes itself to verify a design or build. What a screenshot can and can't prove, how to measure instead of estimate, and how screenshot evidence enters briefs, audits and the harness.
---

# Screenshot Review

The agent can read screenshots: an existing page to audit, the current product for context, another team's screens, or a design system someone only has as images. It also takes its own, to check a design or build at the sizes that matter. Either way, the same rule applies: **a screenshot shows what something looks like, not what it's made of.** Everything read off one is labeled as seen or estimated, and measured values win whenever they're available.

## What a screenshot can and can't prove

| From a screenshot alone | Reliable? |
|---|---|
| Layout, hierarchy, what's grouped, reading order, the primary action | **Seen.** Good evidence. |
| Missing states, dead ends, clipped or overlapping text, sideways scrolling that's visible | **Seen.** Good evidence, if the viewport is known |
| Contrast problems that are obvious | **Seen**, but confirm the ratio from real color values |
| Exact colors, spacing, font sizes, weights, typefaces | **Estimated.** Compression, scaling and screen density distort them. Never cite as exact. |
| Touch-target sizes, overflow the image doesn't show, text that doesn't scale | **Can't tell** without the viewport and pixel density, or a render |

So:
- **Record the context.** For every screenshot: the viewport width, the pixel density if known (a 1170px-wide phone screenshot is 390px at 3×), the text size, the theme, and which state it shows. Unknown context is written as unknown and asked about. It's never guessed.
- **Estimated values are never blockers on their own.** A finding based only on an estimate ("card padding looks like about 24px") is at most **major**, marked `measured: false`, and says what would confirm it (the code, or a render).
- **Measure whenever you can.** If the page can be rendered, render it with `tools/screenshots.py`: it measures the real values from the page. If the code is available, the consistency check and token lint read the real values.

## Screenshots people give you

Record them first: `python3 tools/screenshots.py --provided <images…> --out <dir>` writes a screenshot set with each image's pixel size and `source: provided`. Then fill in the context you know, and ask about the rest.

Use them for:
- **Standalone audits** of existing UI (audit mode `design`, or `implementation` for a live product). Findings cite the image and say whether they were seen or estimated.
- **Brief context:** screenshots of the current pages a new page connects to. They inform "Where it fits", the user flow's existing screens, and the edge-case sweep's entities, since what's on screen shows what exists.
- **Consistency across the product:** a consistency inventory from screenshots of several screens, with estimated values marked as such.
- **Extracting a design system:** a first draft of tokens and components from screenshots. Every value is `estimated` and must be confirmed against a source before the manifest is `Optimal`. Screenshots never become the source of truth on their own.

## Screenshots the agent takes

`python3 tools/screenshots.py <page or URL> --out <dir>` renders the page at the standard sizes from the manifest:
- the narrowest width (`mobile.minViewportPx`), the phone, each breakpoint and desktop
- the narrowest width and the phone again, at `mobile.maxTextScalePercent` text

From the rendered page it measures:
- sideways scrolling, and **which element causes it**
- touch targets below the minimum
- text below the legibility floor
- text clipped at large text sizes
- text that **doesn't grow** with text size (set in fixed px)
- the real padding and type of every component, checked against the spacing roles and text styles

The output is a `screenshot-set` (`schemas/screenshot-set.schema.json`) plus the images.

Use it at:
- **Design (Step 9b):** when the design is a renderable page, the mobile pass is backed by the screenshot set, not just asserted in `mobileCheck`.
- **Verify:** the implementation review renders the built UI and cites the screenshot set.

## For the critic

Look at every screenshot, and read the measurements beside them:
- **The picture tells you what a user sees:** hierarchy, grouping, the primary action, anything that looks wrong.
- **The measurements tell you what's true.** A screenshot can look fine and still be broken. A 320px view that's 546px wide looks normal in the image, and only the overflow measurement shows the page scrolls sideways.
- Every finding gives its evidence: `screenshot` (seen or estimated), `rendered-measurement` (measured), `code`, or `artifact`.

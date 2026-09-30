# Type pairing

Default fonts are the quickest tell of an AI-made design: Inter, Roboto, Arial, Helvetica, Open Sans, Lato, Montserrat, Poppins, DM Sans, Space Grotesk and system fonts read as *nobody chose this*. `check_compatibility.py` flags them in a manifest, and the renderer flags them on a page (the list: `antiAiDesign.typefaces.generic`, default in `tools/brand_check.py`). **A brand's own fonts always win.** If the brand guidelines require a face, list it in the brand profile's `typefaces` and it's exempt. Never "improve" a brand's fonts.

## Choosing a pair for a new design system

1. **Start from the product, not the font.** Take three words for its character from the brief or the person (e.g. *playful, fast, competitive*). Choose from the matching row below, or propose something better. Offer 2 or 3 pairs at the brief's one stop: type is a direction decision, so it's the person's call.
2. **Contrast on one axis, harmony on the rest.** Differ in class (serif and sans), in width, or in weight, and match x-height and proportions. Two similar sans faces look like a mistake.
3. **The body face does the work.** It must be legible at 16px and at the smallest style (13px in the Baseline), with open shapes and distinct `I l 1` and `0 O`. It needs tabular figures if the product shows numbers, every weight in `typography.weights`, and every language the product ships in.
4. **Display is for display.** Use it only for `xl` and larger styles. Everything interactive (buttons, inputs, labels) is set in the body or UI face.
5. **At most two families, plus one mono** (`antiAiDesign.typefaces.maxFamilies`). One variable superfamily with a width axis counts as one family.
6. **Don't reuse one pair across products.** A different product with the same pair is how AI-made designs end up looking alike.
7. **Load it.** Self-host with `@font-face` and `font-display: swap`. Match the fallback's metrics (`size-adjust`) so the page doesn't shift. The renderer flags a font that doesn't load and falls back.
8. **Licence:** everything below is on Google Fonts under the OFL. Check the licence of anything else before it goes in the manifest.

## Starting points (Google Fonts)

| Character | Display | Body / UI | Why it works |
|---|---|---|---|
| Editorial, considered | Newsreader | Public Sans | A text serif with optical sizes, over a plain, sturdy sans |
| Warm, expressive | Fraunces | Hanken Grotesk | A soft, characterful serif, with a quiet grotesque to calm it |
| Technical, precise | IBM Plex Sans | IBM Plex Sans + IBM Plex Mono | One superfamily. The mono carries code, IDs and numbers |
| Friendly product | Bricolage Grotesque | Figtree | A quirky display grotesque, over a round, readable sans |
| Accessible first | Literata | Atkinson Hyperlegible Next | Both built for reading; Atkinson separates confusable letters |
| Bold, fast: events, sports, leaderboards | Barlow Condensed | Barlow | Condensed headlines fit big numbers at 320px, from the same family |
| Games, arcade, sci-fi | Chakra Petch | Barlow | Angular, techno display, with a neutral body that stays readable |
| Refined, premium | DM Serif Display | Schibsted Grotesk | High-contrast serif headlines, over a crisp grotesque |
| Contemporary, confident | Archivo (expanded) | Archivo | One variable family: width does the contrast |

Pixel and bitmap faces (Silkscreen, Press Start 2P) are for short accents only, like a score or a badge, and never for body text or controls. They fail legibility at small sizes and at 200% text.

## In the manifest

```yaml
typography:
  typefaces: { display: "Chakra Petch", body: "Barlow", ui: "Barlow", mono: "IBM Plex Mono" }
```

Then check it: `python3 tools/check_compatibility.py design-system-manifest.yaml`.

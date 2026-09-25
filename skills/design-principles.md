---
name: design-principles
description: The fixed rules design-generation-skill.md and design-audit-rubric.md both answer to — the eight core principles, the 3-3-3 usability rule, and Wickens' 13 principles of display design. Not manifest-configurable, not per-project preference — these hold regardless of design system.
---

# Design Principles

These are the rules. Not preferences. Not suggestions.

---

## Simplicity Is Architecture

Every element must justify its existence. If it doesn't serve the user's immediate goal, it's clutter. The best interface is the one the user never notices. Remove until it breaks — then add back the last thing.

**Applied:** Generation Step 4 uses "remove until it breaks" as the working technique for shaping information architecture — start minimal, add back only what the screen can't function without. Audited in rubric category 7 (Simplicity & Necessity) and category 9 (Composition & Density, `requireProgressiveDisclosure`).

## Hierarchy Drives Everything

Every screen has one primary action. Make it unmissable. Secondary actions support — they never compete. If everything is bold, nothing is bold. Visual weight must match functional importance.

**Applied:** `color.usagePolicy.maxPrimaryActionsPerScreen` (new, default 1) makes this a checkable constraint rather than a vibe. Audited in rubric category 10.

## Consistency Is Non-Negotiable

The same component must look and behave identically everywhere. If you find inconsistency, flag it — do not invent a third variation. All values reference design system tokens. No hardcoded colors, spacing, or sizes. Ever.

**Applied:** This is the registry/reuse system's entire reason for existing. "Flag, don't invent a third variation" is now explicit in rubric category 1 for standalone audits of existing designs. Hardcoded-value findings in category 3 are **blockers**, not majors — "ever" doesn't leave room for a lesser severity.

## Alignment Is Precision

Every element sits on a grid. No exceptions. If something is off by 1–2 pixels, it's wrong. Alignment separates premium from good-enough. The eye detects misalignment before the brain can name it.

**Applied:** `layout.alignmentTolerancePx` (new, default 0) makes "no exceptions" literal rather than aspirational. Audited in rubric category 4 as a blocker, not a minor — this principle explicitly rejects treating misalignment as cosmetic.

## Whitespace Is a Feature

Space is not empty — it is structure. Crowded interfaces feel cheap. Breathing room feels premium. When in doubt, add more space, not more elements.

**Applied:** Generation Step 5's default bias when a layout decision is ambiguous: prefer the spacing.scale step up, not a denser one. Not an audit rule by itself — it's a generation-time tiebreaker, checked indirectly through category 3 (Token & Scale Consistency) and category 9 (Composition & Density).

## Responsive Is the Real Design

Mobile is the starting point. Tablet and desktop are enhancements. Design for thumbs first, then cursors. Every screen must feel intentional at every viewport — not just resized. If it looks off at any screen size, it's not done.

**Applied:** Generation Step 5 now designs from `layout.breakpoints`' smallest step upward, not desktop-down. Audited in rubric category 4 — "intentional at every viewport" strengthens the existing breakpoint-behavior check from "doesn't break" to "was actually designed for," not merely resized.

## Design the Feeling

Premium apps feel calm, confident, and quiet. Every interaction should feel responsive and intentional. Transitions should feel like physics, not decoration. The app should feel like it respects the user's time.

**Applied:** `motion.easing` tokens already exist for this — "physics not decoration" means entrance/exit/transition curves should behave like momentum (ease-out on entrance, ease-in on exit), not linear or bouncy-for-its-own-sake. Audited in rubric category 8/10 alongside the existing loading-animation checks.

**Note on scope:** unlike the other seven principles, "calm, confident, quiet" describes a specific emotional register. Most of this system is deliberately manifest-configurable so it generalizes across design systems (a playful consumer app and a clinical dashboard shouldn't feel identical) — this principle is being treated as universal per your instruction that these are rules, not preferences, but flag if you want it scoped to specific project types instead of applied everywhere.

## No Cosmetic Fixes Without Structural Thinking

Never suggest a change without explaining what it accomplishes in the hierarchy. "Make this blue" is not an instruction. "Change CTA color to brand-primary to increase contrast against secondary actions" is. Every change must have a design reason, not just a preference.

**Applied:** This is exactly what `implementationNote` + the "Why this matters" column in `audit-presentation-template.md` already enforce structurally — the bad/good examples in that template are this principle in practice. Strengthened requirement: the rationale must cite a structural cause (hierarchy, consistency, contrast ratio, a named token) — "looks better" is not a valid rationale and should be rejected the same way a missing `implementationNote` is.

---

# Usability & Display-Design Criteria

The eight principles above say what a good interface *is*. The two sets below make it *checkable*: the 3-3-3 rule measures whether a person can actually use the design, and Wickens' 13 principles of display design (Wickens, Lee, Liu & Gordon-Becker, *An Introduction to Human Factors Engineering*) explain why a display is or isn't easy to perceive, understand, and remember. Thresholds live in the manifest's `usabilityHeuristics`; the checks are rubric categories 12 and 13.

## The 3-3-3 Rule

Every core task in the ticket brief (`coreTasks`) must pass all three:

1. **3 seconds to understand.** A first-time user, glancing at the screen, can tell what it is for and what the primary action is within `glanceSeconds` — at the smallest breakpoint (`glanceBreakpoint`), without scrolling, and without reading body text. The heading and the one primary action carry this; if either needs explanation, the hierarchy is wrong.
2. **3 clicks to reach.** From its entry point, a core task is reachable in at most `maxClicksToCoreTask` clicks/taps. Typing into a field doesn't count; every navigation, selection, or toggle does.
3. **3 minutes to complete.** A first-time user can finish the core task in under `maxCoreTaskMinutes`, estimated step by step with the assumptions stated.

**The limits are guides, not goals.** Research on the three-click rule shows people don't give up after three clicks when every click is obviously the right one — what matters is that each step has clear *information scent* (the label tells you what's behind it). So:
- Never meet the click limit by cramming: it does not override `maxInlineInputs`, progressive disclosure, or pagination. If they conflict, that's a Decision Protocol moment, not a silent trade.
- A path that goes over the limit is acceptable only with a stated reason and every step's scent documented.

**Applied:** the ticket brief lists `coreTasks`; generation Step 9b walks each one and records a `glanceTest` and `taskPaths` in the design output; audited in rubric category 12.

## Wickens' 13 Principles of Display Design

### Perceptual principles
1. **Make displays legible.** Text, icons, and data must be readable in the real conditions of use — size, contrast, and resolution at the smallest breakpoint. Nothing below `displayDesign.minReadableTextPx`; nothing truncated into meaninglessness.
2. **Avoid absolute judgment limits.** People can't reliably tell apart more than a few levels of one visual variable (shade, size, hue) from memory. Don't encode more than `displayDesign.maxAbsoluteJudgmentLevels` levels on a single dimension without direct labels or a second dimension.
3. **Top-down processing.** People see what they expect. Follow established conventions (placement of standard controls, red = error, green = success, up = more); when a design must break an expectation, make the difference unmistakable.
4. **Redundancy gain.** A message is received more reliably when it arrives through more than one channel. Critical states — errors, warnings, destructive actions, status — use at least two cues (color *and* icon *and/or* text).
5. **Discriminability.** Similar-looking items get confused. Elements that mean different things must look clearly different — especially when they sit side by side or trigger different outcomes. Emphasize the features that differ, not the ones they share.

### Mental-model principles
6. **Pictorial realism.** A display should look like what it represents: higher values higher, more is bigger, time runs left to right in left-to-right locales.
7. **The moving part.** Things that change should move the way the user's mental model says they move: progress fills forward, an increase animates upward, a panel slides from where it came from.

### Attention principles
8. **Minimize information access cost.** Information used often, or together, should be reachable with the least effort — no repeated scrolling, tab-switching, or drilling to find what a task needs every time.
9. **Proximity compatibility.** Information that must be mentally combined belongs close together (or visibly linked by color, line, or container); unrelated information should *not* look grouped.
10. **Multiple resources.** Attention can be split across channels (visual, auditory, haptic) better than within one. Don't pile every signal onto the visual channel while the user is reading; for time-critical alerts, use a second modality where the platform supports it.

### Memory principles
11. **Replace memory with visual information (knowledge in the world).** Don't make people remember what the interface can show. Values, options, and context from a previous step stay visible; available actions are visible, not hidden behind unmarked gestures.
12. **Predictive aiding.** Show what's about to happen: consequences before committing, time remaining, what the next step is, when a limit will be reached. Anticipating is easier than reacting.
13. **Consistency.** The same thing looks and behaves the same everywhere, including across other designs in the design index. (This deepens *Consistency Is Non-Negotiable* above; the component registry and scope check exist to enforce it.)

**Applied:** principles 1–5 shape generation Steps 5–8 (layout, typography, color, motion); 6–7 shape data-viz and motion (Step 8); 8–9 shape information architecture (Step 4); 10–12 shape feedback and navigation (Steps 8–9); 13 is enforced by Steps 2b and 3. All 13 are audited in rubric category 13.

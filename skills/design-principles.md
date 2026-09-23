---
name: design-principles
description: The fixed rules design-generation-skill.md and design-audit-rubric.md both answer to. Not manifest-configurable, not per-project preference — these hold regardless of design system.
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

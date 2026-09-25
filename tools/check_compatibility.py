#!/usr/bin/env python3
"""Check how compatible a design system is with this agent.

Usage: python3 tools/check_compatibility.py <manifest.yaml>
           [--claude-md CLAUDE.md] [--index design-index.yaml] [--schemas schemas/]

Reports one of three levels, per standard/REQUIREMENTS.md:
  Not compatible  the agent will halt (schema errors, missing project context)
  Minimum         the agent runs, but falls back to defaults or can't satisfy
                  some rubric checks
  Optimal         everything explicit, every value passes, baseline components
                  present — what standard/design-system-manifest.yaml shows
Exit 0 = Optimal, 1 = Minimum, 2 = Not compatible.
"""
import argparse
import json
import os
import sys

import jsonschema
import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from export_claude_design import contrast  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

# Settings the agent reads that have schema defaults. Leaving one out works,
# but the agent then decides it for you and the audit can't hold you to it.
EXPLICIT = [
    "meta.decisionProtocol", "meta.brandExclusions", "meta.claudeMd",
    "color.contrastStandard", "color.interactionStates.hover", "color.interactionStates.active",
    "color.interactionStates.focus", "color.usagePolicy.maxSimultaneousSecondaryAccents",
    "color.usagePolicy.maxPrimaryActionsPerScreen", "color.accents.onPrimary",
    "color.accents.success", "color.accents.warning", "color.accents.error", "color.accents.info",
    "color.neutrals.textSecondary",
    "typography.weights", "typography.scale.steps", "typography.lineHeightRatio", "typography.roles",
    "layout.gridColumns", "layout.gutterPx", "layout.breakpoints", "layout.containerMaxWidthPx",
    "layout.alignmentTolerancePx", "motion", "radius", "icons.library",
    "accessibility.minTouchTargetPx", "accessibility.requireVisibleFocusStates", "accessibility.requireSemanticHtml",
    "registryPolicy.onMissingComponent", "registryPolicy.onMissingVariant", "registryPolicy.requireApprovalBeforeReuse",
    "registryPolicy.requireOperationalVerification", "registryPolicy.verificationReviewer", "registryPolicy.similarityCheck",
    "automation", "compositionHeuristics", "navigationHeuristics", "motionUsagePolicy",
    "usabilityHeuristics", "scopePolicy", "platform.targets", "mobile",
]

# The components the rubric's checks assume exist, with the variants they need.
BASELINE = {
    "Button": ("action", ["primary", "secondary", "ghost", "destructive"], "every action; one primary per screen (cat. 10)"),
    "Input": ("input", ["default", "error"], "forms with visible labels (cat. 3, formLabel)"),
    "Card": ("display", ["default"], "containers without shadows"),
    "InlineAlert": ("feedback", ["info", "success", "warning", "error"], "critical states with two cues (Wickens 4)"),
    "Skeleton": ("feedback", ["default"], "loading states (motionUsagePolicy, cat. 8)"),
    "Dialog": ("overlay", ["confirm-destructive"], "confirming destructive actions (cat. 8)"),
    "Breadcrumb": ("navigation", ["default"], "navigational ties past breadcrumbThresholdDepth (cat. 10)"),
    "Pagination": ("navigation", ["default"], "lists over listPaginationThreshold (cat. 9)"),
}
RECOMMENDED = {"Toast": "non-blocking confirmations", "EmptyState": "empty states in verification reports", "Tabs": "peer views"}


def get(d, path):
    for key in path.split("."):
        if not isinstance(d, dict) or key not in d:
            return None
        d = d[key]
    return d


def color_value(m, role):
    resolved = get(m, "color.resolved") or {}
    if role in resolved:
        return next(iter(resolved[role].values()), None)
    v = get(m, "color." + role)
    return v if isinstance(v, str) and v.startswith("#") else None


def check(m, schemas, claude_md, index_path):
    halt, gaps, notes = [], [], []

    # --- Minimum: the agent can run --------------------------------------
    schema = json.load(open(os.path.join(schemas, "design-system-manifest.schema.json")))
    for e in sorted(jsonschema.Draft7Validator(schema).iter_errors(m), key=lambda e: list(e.path)):
        halt.append(f"Schema: {'.'.join(map(str, e.path)) or '(root)'}: {e.message}")
    targets = get(m, "platform.targets") or ["claude-code"]
    required_ctx = (get(m, "meta.claudeMd.required") is not False)
    if "claude-code" in targets and required_ctx:
        stamp = f"<!-- design-system-manifest: {get(m, 'meta.name')} v{get(m, 'meta.version')} -->"
        if not claude_md or not os.path.exists(claude_md):
            halt.append("No CLAUDE.md with the design system in it (generate it from templates/CLAUDE.md).")
        else:
            text = open(claude_md).read()
            if not text.startswith(stamp):
                halt.append(f"CLAUDE.md's first line isn't the version stamp `{stamp}`.")
            if "{{" in text:
                halt.append("CLAUDE.md still has unfilled {{...}} placeholders.")
    if halt:
        return halt, gaps, notes

    # --- Optimal: nothing left to defaults ---------------------------------
    missing = [p for p in EXPLICIT if get(m, p) is None]
    if missing:
        gaps.append("Left to defaults (set them explicitly): " + ", ".join(missing))

    # --- Optimal: values pass the agent's own checks ------------------------
    std = get(m, "color.contrastStandard") or "WCAG-AA"
    need_text = 7.0 if std == "WCAG-AAA" else 4.5
    need_ui = 4.5 if std == "WCAG-AAA" else 3.0
    pairs = [("neutrals.textPrimary", "neutrals.background", need_text), ("neutrals.textPrimary", "neutrals.surface", need_text),
             ("neutrals.textSecondary", "neutrals.background", need_text), ("neutrals.textSecondary", "neutrals.surface", need_text),
             ("accents.onPrimary", "accents.primary", need_text), ("interactionStates.focus", "neutrals.background", need_ui)]
    pairs += [(f"accents.{s}", "neutrals.surface", need_text) for s in ("success", "warning", "error", "info")]
    unresolved = False
    for fg, bg, need in pairs:
        a, b = color_value(m, fg), color_value(m, bg)
        if not (a and b):
            unresolved = True
            continue
        r = contrast(a, b)
        if r < need:
            gaps.append(f"Contrast: {fg} on {bg} is {r:.2f}:1, needs {need}:1 ({std}).")
    if unresolved:
        gaps.append("Some colors have no real value (color.resolved or hex), so contrast can't be checked.")
    sec = get(m, "color.accents.secondary")
    clashes = [s for s in ("success", "warning", "error", "info") if sec and get(m, f"color.accents.{s}") == sec]
    if clashes:
        gaps.append(f"Secondary accent is the same color as {', '.join(clashes)}: it will read as a status (cat. 10).")

    scale = get(m, "typography.scale") or {}
    steps = scale.get("steps") or ["base"]
    base_i = steps.index("base") if "base" in steps else 0
    floor = get(m, "usabilityHeuristics.displayDesign.minReadableTextPx") or 12
    small = [f"{s} ({round(scale['baseSizePx'] * scale['ratio'] ** (i - base_i))}px)" for i, s in enumerate(steps)
             if round(scale["baseSizePx"] * scale["ratio"] ** (i - base_i)) < floor]
    if small:
        gaps.append(f"Type steps below the {floor}px legibility floor (Wickens 1): {', '.join(small)}.")
    if len(get(m, "typography.weights") or []) > 3:
        gaps.append("More than 3 font weights.")

    sp = get(m, "spacing") or {}
    off_unit = [v for v in sp.get("scale", []) if v % sp.get("baseUnitPx", 4)]
    if off_unit:
        gaps.append(f"Spacing steps not multiples of baseUnitPx: {off_unit}.")
    if sp.get("scale") != sorted(sp.get("scale", [])):
        gaps.append("spacing.scale isn't in ascending order.")
    if get(m, "layout.gutterPx") is not None and get(m, "layout.gutterPx") not in sp.get("scale", []):
        gaps.append("layout.gutterPx isn't a spacing.scale step.")
    bps = list((get(m, "layout.breakpoints") or {}).values())
    if bps != sorted(bps):
        gaps.append("Breakpoints aren't ascending sm < md < lg < xl.")
    if (get(m, "accessibility.minTouchTargetPx") or 44) < 44:
        gaps.append("minTouchTargetPx is below 44px.")

    # mobile at all times
    mob = get(m, "mobile") or {}
    if mob.get("minViewportPx", 320) > 360:
        gaps.append(f"mobile.minViewportPx is {mob['minViewportPx']}px: designs must be verified at 360px or narrower (320px recommended).")
    if mob.get("maxTextScalePercent", 200) < 200:
        gaps.append("mobile.maxTextScalePercent is below 200% (WCAG 1.4.4).")
    if mob.get("minTargetSpacingPx", 8) < 8:
        gaps.append("mobile.minTargetSpacingPx is below 8px.")
    if bps and min(bps) > 640:
        gaps.append("The smallest breakpoint is above 640px, so there's no phone layout step.")
    phone = get(m, "platform.claudeDesign.canvasBoards.phone.w")
    if "claude-design" in (get(m, "platform.targets") or []) and phone and phone > 430:
        gaps.append(f"The Claude Design phone artboard is {phone}px wide; phones are 430px or narrower.")

    for path in ("registryPolicy.similarityCheck.weights", "scopePolicy.overlapCheck.weights"):
        w = get(m, path)
        if w and abs(sum(w.values()) - 1) > 1e-6:
            gaps.append(f"{path} sum to {sum(w.values()):g}, not 1.0.")
    sc = get(m, "registryPolicy.similarityCheck") or {}
    if sc.get("reuseThreshold", .7) <= sc.get("extendThreshold", .4):
        gaps.append("reuseThreshold must be above extendThreshold.")
    oc = get(m, "scopePolicy.overlapCheck") or {}
    if oc.get("mergeThreshold", .6) <= oc.get("relatedThreshold", .3):
        gaps.append("mergeThreshold must be above relatedThreshold.")

    # --- Optimal: baseline components ---------------------------------------
    comps = {c["name"]: c for c in m.get("components", [])}
    for name, (cat, variants, why) in BASELINE.items():
        c = comps.get(name)
        if not c or c.get("status") != "approved":
            gaps.append(f"Baseline component missing or not approved: {name} ({cat}) — needed for {why}.")
            continue
        have = {v["name"] for v in c.get("variants", []) if v.get("status") == "approved"}
        lacking = [v for v in variants if v not in have]
        if lacking:
            gaps.append(f"{name} is missing approved variant(s) {lacking} — needed for {why}.")
    no_props = [c["name"] for c in m.get("components", []) if not c.get("props") and not any(v.get("props") for v in c.get("variants", []))]
    if no_props:
        gaps.append(f"Components with no props, so the similarity check can't score them: {', '.join(no_props)}.")
    for name, why in RECOMMENDED.items():
        if name not in comps:
            notes.append(f"Recommended component not present: {name} ({why}).")

    # --- Optimal: per platform ----------------------------------------------
    if "claude-code" in targets:
        if not get(m, "development.uiPaths"):
            gaps.append("development.uiPaths isn't set, so the token lint and design context can't find UI code.")
        if get(m, "development.tokenLint.mode") == "off":
            gaps.append("development.tokenLint.mode is off: off-token values won't be caught while coding.")
    if index_path and os.path.exists(index_path):
        index = yaml.safe_load(open(index_path)) or {}
        idx_schema = json.load(open(os.path.join(schemas, "design-index.schema.json")))
        errs = list(jsonschema.Draft7Validator(idx_schema).iter_errors(index))
        if errs:
            gaps.append(f"Design index doesn't match its schema: {errs[0].message}")
        for p in index.get("projects", []):
            if p.get("status") in ("approved", "shipped") and not p.get("codePaths"):
                gaps.append(f"Design {p['id']} is {p['status']} but has no codePaths, so its code gets no design context.")
    else:
        notes.append("No design index found; the agent creates one with the first design.")
    return halt, gaps, notes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("--claude-md", default=None, help="default: CLAUDE.md next to the manifest")
    ap.add_argument("--index", default=None, help="default: the manifest's scopePolicy.designIndexPath, next to the manifest")
    ap.add_argument("--schemas", default=os.path.join(HERE, "..", "schemas"))
    args = ap.parse_args()
    base = os.path.dirname(os.path.abspath(args.manifest))
    m = yaml.safe_load(open(args.manifest))
    claude_md = args.claude_md or os.path.join(base, get(m, "meta.claudeMd.path") or "CLAUDE.md")
    index = args.index or os.path.join(base, get(m, "scopePolicy.designIndexPath") or "design-index.yaml")
    halt, gaps, notes = check(m, args.schemas, claude_md, index)

    name = f"{get(m, 'meta.name')} v{get(m, 'meta.version')}"
    if halt:
        print(f"{name}: NOT COMPATIBLE — the agent will halt.")
        for h in halt:
            print("  ✗", h)
        return 2
    level = "OPTIMAL" if not gaps else "MINIMUM"
    print(f"{name}: {level}" + (" — the agent runs, but:" if gaps else " — meets every requirement."))
    for g in gaps:
        print("  •", g)
    for n in notes:
        print("  ·", n)
    return 0 if not gaps else 1


if __name__ == "__main__":
    sys.exit(main())

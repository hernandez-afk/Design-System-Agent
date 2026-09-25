#!/usr/bin/env python3
"""Flag off-token values in UI code: colors, spacing, font sizes and radii.

Usage: python3 tools/token_lint.py <file>... [--manifest design-system-manifest.yaml]

Allowed values come from the manifest: color roles (framework names and
resolved hex), spacing.scale, the type scale and radius tokens, plus
development.tokenLint.allow. Checks Tailwind utilities (color and spacing
classes, arbitrary [..px] values) and CSS declarations (color, spacing,
font-size, border-radius), per development.tokenLint.framework.

Exit 0 = clean (or mode 'warn'/'off'); exit 2 = violations in 'block' mode,
with the report on stderr so a Claude Code hook sends it back to be fixed.
"""
import argparse
import fnmatch
import os
import re
import sys

import yaml


def globmatch(path, pattern):
    """fnmatch where '**/' also matches zero directories (src/**/*.css matches src/a.css)."""
    return fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(path, pattern.replace("**/", ""))

SPACING_PREFIX = r"(?:p|px|py|pt|pr|pb|pl|ps|pe|m|mx|my|mt|mr|mb|ml|ms|me|gap|gap-x|gap-y|space-x|space-y|inset|inset-x|inset-y|top|right|bottom|left)"
COLOR_PREFIX = r"(?:bg|text|border|border-[trblxy]|ring|ring-offset|outline|divide|fill|stroke|from|via|to|placeholder|accent|caret|decoration|shadow)"
TW_COLOR = re.compile(rf"(?<![\w-]){COLOR_PREFIX}-([a-z]+-\d{{2,3}})(?:/\d+)?(?![\w-])")
TW_SPACING = re.compile(rf"(?<![\w-])-?{SPACING_PREFIX}-(\d+(?:\.5)?)(?![\w.-])")
TW_ARBITRARY = re.compile(r"(?<![\w-])([a-z-]+)-\[(-?\d+(?:\.\d+)?)px\]")
HEX = re.compile(r"(?<![\w&])#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3,4})\b")
CSS_DECL = re.compile(r"(?<![\w-])(margin|padding|gap|row-gap|column-gap|inset|top|right|bottom|left|font-size|border-radius)(?:-[a-z]+)?\s*:\s*([^;}\"']+)", re.I)
PX = re.compile(r"(-?\d+(?:\.\d+)?)px")
# fixed sizes: width/height, not min-/max- (limits are how fluid components stay in bounds)
TW_SIZE = re.compile(r"(?<![\w-])(w|h|size)-(\d+(?:\.5)?)(?![\w./-])")
CSS_SIZE = re.compile(r"(?<![\w-])(width|height)\s*:\s*(\d+(?:\.\d+)?)px", re.I)
LIMIT_PROPS = {"min-w", "max-w", "min-h", "max-h"}


def allowed_values(m):
    color = m.get("color", {})
    names, hexes = {"white", "black", "transparent", "current", "inherit"}, set()
    for group in ("neutrals", "accents", "interactionStates"):
        for k, v in (color.get(group) or {}).items():
            if isinstance(v, str) and k != "temperature":
                names.add(v.lower())
    for values in (color.get("resolved") or {}).values():
        hexes |= {v.lower() for v in values.values() if v.startswith("#")}
    spacing = set(m.get("spacing", {}).get("scale", [])) | {0}
    t = m.get("typography", {}).get("scale", {})
    steps = t.get("steps") or ["base"]
    base_i = steps.index("base") if "base" in steps else 0
    type_px = {round(t.get("baseSizePx", 16) * t.get("ratio", 1.25) ** (i - base_i)) for i in range(len(steps))}
    radius = {r["px"] for r in (m.get("radius", {}) or {}).get("tokens", [])} | {0, 9999}
    extra = {float(a[:-2]) for a in m.get("development", {}).get("tokenLint", {}).get("allow", []) if a.endswith("px")}
    max_fixed = m.get("mobile", {}).get("maxFixedSizePx", 64)
    return names, hexes, spacing, type_px, radius, extra, max_fixed


def lint(path, m, shown=None):
    names, hexes, spacing, type_px, radius, extra, max_fixed = allowed_values(m)
    fixed_why = f"fixed size above mobile.maxFixedSizePx ({max_fixed}px): components must be fluid — use w-full, %, or min-/max- limits"
    framework = m.get("development", {}).get("tokenLint", {}).get("framework", "both")
    problems = []
    in_block = False
    for n, raw in enumerate(open(path, encoding="utf-8", errors="replace"), 1):
        # skip comments: // line comments, /* block */ comments, {/* JSX */}
        line = raw
        if in_block:
            if "*/" not in line:
                continue
            line, in_block = line.split("*/", 1)[1], False
        line = re.sub(r"/\*.*?\*/", "", line)
        if "/*" in line:
            line, in_block = line.split("/*", 1)[0], True
        line = re.sub(r"(^|\s)//.*$", r"\1", line)

        def flag(value, why):
            problems.append(f"{shown or path}:{n}: {value} — {why}")
        for h in HEX.findall(line):
            if h.lower() not in hexes:
                flag(h, "color not in the design system (use a color role token)")
        if framework in ("tailwind", "both"):
            for c in TW_COLOR.findall(line):
                if c.lower() not in names:
                    flag(c, f"color not in the design system; roles use {', '.join(sorted(names - {'white', 'black', 'transparent', 'current', 'inherit'}))}")
            for s in TW_SPACING.findall(line):
                px = float(s) * 4
                if px not in spacing and px not in extra:
                    flag(f"{s} ({px:g}px)", f"spacing not in spacing.scale {sorted(spacing - {0})}")
            for prop, units in TW_SIZE.findall(line):
                if float(units) * 4 > max_fixed:
                    flag(f"{prop}-{units} ({float(units) * 4:g}px)", fixed_why)
            for prop, v in TW_ARBITRARY.findall(line):
                px, ok = abs(float(v)), spacing | type_px | radius | extra
                if prop in LIMIT_PROPS:
                    continue
                if prop in ("w", "h", "size"):
                    if px > max_fixed:
                        flag(f"{prop}-[{v}px]", fixed_why)
                    continue
                if px not in ok:
                    flag(f"{prop}-[{v}px]", "arbitrary value not in the spacing, type or radius scale")
        if framework in ("css", "both"):
            for prop, v in CSS_SIZE.findall(line):
                if float(v) > max_fixed:
                    flag(f"{prop.lower()}: {v}px", fixed_why)
            for prop, value in CSS_DECL.findall(line):
                prop = prop.lower()
                ok = type_px if prop == "font-size" else radius if prop == "border-radius" else spacing
                for v in PX.findall(value):
                    if abs(float(v)) not in ok | extra:
                        flag(f"{prop}: {v}px", f"not in the {'type' if prop == 'font-size' else 'radius' if prop == 'border-radius' else 'spacing'} scale {sorted(ok)}")
    return problems


def lint_files(files, root, m):
    """Return (mode, report). report is '' when clean or when linting is off."""
    cfg = m.get("development", {})
    mode = cfg.get("tokenLint", {}).get("mode", "block")
    if mode == "off":
        return mode, ""
    problems = []
    for f in files:
        rel = os.path.relpath(os.path.abspath(f), os.path.abspath(root))
        if cfg.get("uiPaths") and not any(globmatch(rel, g) for g in cfg["uiPaths"]):
            continue
        if os.path.isfile(f):
            problems += lint(f, m, rel)
    if not problems:
        return mode, ""
    return mode, "Off-token values (design system: {} v{}):\n{}\nReplace each with a token from the manifest, and make fixed sizes fluid.".format(
        m["meta"]["name"], m["meta"]["version"], "\n".join(problems))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--manifest", default="design-system-manifest.yaml")
    ap.add_argument("--root", default=os.environ.get("CLAUDE_PROJECT_DIR", "."))
    args = ap.parse_args()
    with open(os.path.join(args.root, args.manifest)) as f:
        m = yaml.safe_load(f)
    mode, report = lint_files(args.files, args.root, m)
    if not report:
        return 0
    if mode == "block":
        print(report, file=sys.stderr)
        return 2
    print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())

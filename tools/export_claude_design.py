#!/usr/bin/env python3
"""Export a design-system manifest to a Claude Design System's tokens.json.

Usage: python3 tools/export_claude_design.py <manifest.yaml> <out-dir>

Writes <out-dir>/project/tokens.json in the Design System's list shape and
prints problems: roles with no resolved color, duplicate names, text below the
legibility floor, and text/fill pairs that fail the manifest's contrast
standard. Exits 1 on errors (nothing usable to export); warnings exit 0.
"""
import json
import os
import re
import sys

import yaml

# Text-on-fill pairs to check, as (foreground role, background role, minimum
# ratio key). "text" = body text threshold, "ui" = 3:1 non-text/large text.
CONTRAST_PAIRS = [
    ("neutrals.textPrimary", "neutrals.background", "text"),
    ("neutrals.textPrimary", "neutrals.surface", "text"),
    ("neutrals.textSecondary", "neutrals.background", "text"),
    ("neutrals.textSecondary", "neutrals.surface", "text"),
    ("accents.onPrimary", "accents.primary", "text"),
    ("interactionStates.focus", "neutrals.background", "ui"),
]
MIN_RATIO = {"WCAG-AA": {"text": 4.5, "ui": 3.0}, "WCAG-AAA": {"text": 7.0, "ui": 4.5}}

USAGE = {
    "neutrals.background": "Page background.",
    "neutrals.surface": "Cards, panels and inputs on the page background.",
    "neutrals.border": "Borders and dividers; structure without shadows.",
    "neutrals.textPrimary": "Headings, body text and form labels.",
    "neutrals.textSecondary": "Readable subtext and captions — never form labels.",
    "accents.primary": "The one primary action per screen.",
    "accents.onPrimary": "Text and icons on a primary fill.",
    "accents.secondary": "The single competing action; at most the manifest's limit on screen at once.",
    "accents.success": "Success states, always with an icon or text.",
    "accents.warning": "Warning states, always with an icon or text.",
    "accents.error": "Error states, always with an icon or text.",
    "accents.info": "Informational states, always with an icon or text.",
    "interactionStates.hover": "Hover fill for interactive elements.",
    "interactionStates.active": "Pressed state.",
    "interactionStates.focus": "Keyboard focus ring; visible without a pointer.",
}
NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")


def luminance(hex_color):
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    channels = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def kebab(role):
    leaf = role.split(".")[-1]
    return re.sub(r"(?<!^)(?=[A-Z])", "-", leaf).lower()


def main(manifest_path, out_dir):
    m = yaml.safe_load(open(manifest_path))
    errors, warnings = [], []
    color = m.get("color", {})
    themes = color.get("themes") or [{"id": "light", "name": "Light"}]
    theme_ids = [t["id"] for t in themes]
    resolved = color.get("resolved") or {}
    if not resolved:
        errors.append("color.resolved is empty — a Design System needs real color values.")

    # every role the manifest names must have a resolved value
    roles = [f"{group}.{k}" for group in ("neutrals", "accents", "interactionStates")
             for k, v in (color.get(group) or {}).items() if k != "temperature" and isinstance(v, str)]
    for role in roles:
        if role not in resolved:
            errors.append(f"No resolved value for color role '{role}' ({color[role.split('.')[0]][role.split('.')[1]]}).")

    color_tokens, names = [], set()
    for role, values in resolved.items():
        name = kebab(role)
        if name in names or not NAME_RE.match(name):
            errors.append(f"Token name '{name}' (from '{role}') is duplicated or invalid.")
        names.add(name)
        value = {t: values[t] for t in theme_ids if t in values}
        if theme_ids[0] not in value:
            errors.append(f"'{role}' has no value for the first theme '{theme_ids[0]}'.")
        color_tokens.append({"name": name, "value": value, "usage": USAGE.get(role, f"Color role {role}.")})

    # contrast, per theme
    std = color.get("contrastStandard", "WCAG-AA")
    for fg, bg, kind in CONTRAST_PAIRS:
        if fg not in resolved or bg not in resolved:
            continue
        for t in theme_ids:
            a, b = resolved[fg].get(t, resolved[fg][theme_ids[0]]), resolved[bg].get(t, resolved[bg][theme_ids[0]])
            if not (a.startswith("#") and b.startswith("#")):
                continue
            ratio, need = contrast(a, b), MIN_RATIO[std][kind]
            if ratio < need:
                warnings.append(f"Contrast {fg} on {bg} ({t}): {ratio:.2f}:1, needs {need}:1 for {std}.")

    # type scale
    typo = m["typography"]
    scale = typo["scale"]
    steps = scale.get("steps") or ["base"]
    base_i = steps.index("base") if "base" in steps else 0
    lh = typo.get("lineHeightRatio", 1.5)
    faces = typo.get("typefaces", {})
    weights = typo.get("weights") or [400]
    floor = (m.get("usabilityHeuristics", {}).get("displayDesign", {}) or {}).get("minReadableTextPx", 12)
    text_styles, display_styles = [], []
    for i, step in enumerate(steps):
        size = round(scale["baseSizePx"] * scale["ratio"] ** (i - base_i))
        style = {"name": step, "fontSize": f"{size}px", "lineHeight": f"{round(size * lh)}px",
                 "fontWeight": max(weights) if i > base_i else min(weights)}
        if size < floor:
            warnings.append(f"Type step '{step}' is {size}px, below minReadableTextPx ({floor}px) — not for text.")
        (display_styles if i > base_i else text_styles).append(style)
    families = {role: f'"{face}", {"serif" if role == "display" else "system-ui, sans-serif"}'
                for role, face in faces.items()}
    groups = [{"name": "Text", "family": "body", "styles": text_styles}]
    if display_styles:
        groups.append({"name": "Display", "family": "display" if "display" in families else "body", "styles": display_styles})

    spacing = [{"name": f"space-{px}", "value": f"{px}px", "usage": f"Spacing scale step {i + 1} of {len(m['spacing']['scale'])}."}
               for i, px in enumerate(m["spacing"]["scale"])]
    radius = [{"name": r["name"], "value": f"{r['px']}px", "usage": r.get("usage", "")}
              for r in (m.get("radius", {}) or {}).get("tokens", [])]
    for t in spacing + radius:
        if t["name"] in names or not NAME_RE.match(t["name"]):
            errors.append(f"Token name '{t['name']}' is duplicated or invalid.")
        names.add(t["name"])

    tokens = {
        "name": m["meta"]["name"],
        "version": 1,
        "meta": {"source": f"design-system-manifest v{m['meta']['version']}"},
        "color": {"themes": themes, "tokens": color_tokens},
        "type": {"fonts": [], "families": families, "groups": groups},
        "spacing": {"tokens": spacing},
    }
    if radius:
        tokens["radius"] = {"tokens": radius}

    for w in warnings:
        print("WARNING:", w)
    for e in errors:
        print("ERROR:", e)
    if errors:
        return 1
    os.makedirs(os.path.join(out_dir, "project"), exist_ok=True)
    path = os.path.join(out_dir, "project", "tokens.json")
    with open(path, "w") as f:
        json.dump(tokens, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"Wrote {path}: {len(color_tokens)} colors, {len(text_styles) + len(display_styles)} type styles, "
          f"{len(spacing)} spacing, {len(radius)} radius tokens.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1], sys.argv[2]))

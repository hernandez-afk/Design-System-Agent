#!/usr/bin/env python3
"""Warn when something meant to follow a brand's guidelines doesn't match them.

Usage: python3 tools/brand_check.py [files…] [--manifest design-system-manifest.yaml]

The manifest's brandGuidelines lists guideline profiles (brand/<name>.yaml,
schemas/brand-guidelines.schema.json). A profile applies to a file or page
when it mentions one of the profile's triggers (e.g. "Atari"), declares it
(<meta name="brand-guidelines" content="Atari">), or when the manifest entry
says applies: always. Then:
  - colors close to a brand color but not it are flagged (the classic
    off-brand miss: a red that's nearly the brand red)
  - with strictPalette, any non-neutral color outside the palette is flagged
  - fonts the guidelines don't allow are flagged
  - the brand name in a form the guidelines don't allow is flagged
  - the manifest itself is checked when the entry applies always
A profile with no values yet still warns when it's referenced, so a page
that's meant to follow the guidelines is never silently unchecked.
screenshots.py uses the same functions on the rendered page (colors, fonts,
text and logo size and proportions). Exit 0 = nothing to warn about, 2 = warnings.
"""
import argparse
import os
import re
import sys

import yaml

HEX = re.compile(r"#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")
FONT_DECL = re.compile(r"font-family\s*:\s*([^;}\"]+)|fontFamily\s*[:=]\s*[\"'`{]+([^\"'`}]+)", re.I)
# Fonts that read as "nobody chose this": system defaults and the faces every template ships with.
# A brand's own guidelines can still require one (brandGuidelines profile typefaces win).
DEFAULT_GENERIC_FONTS = ["Inter", "Roboto", "Arial", "Helvetica", "Helvetica Neue", "Open Sans", "Lato", "Montserrat",
                         "Poppins", "Segoe UI", "-apple-system", "BlinkMacSystemFont", "SF Pro", "SF Pro Text", "Noto Sans",
                         "Nunito", "Raleway", "DM Sans", "Space Grotesk", "Times New Roman", "Times", "Verdana", "system-ui"]
GENERIC_FAMILIES = {"serif", "sans-serif", "monospace", "cursive", "fantasy", "system-ui", "ui-sans-serif",
                    "ui-serif", "ui-monospace", "emoji", "math", "inherit", "initial", "unset"}


def generic_fonts(m):
    return [f.lower() for f in ((m.get("antiAiDesign", {}) or {}).get("typefaces", {}) or {}).get("generic", DEFAULT_GENERIC_FONTS)]


def brand_fonts(m, base):
    """Fonts some applicable brand's guidelines require, which the generic-font warning then allows."""
    return {f.lower() for _, p, _ in profiles(m, base) if p for f in p.get("typefaces", []) or []}


def load(p):
    with open(p) as f:
        return yaml.safe_load(f) or {}


def profiles(m, base):
    """(entry, profile, path) for each brandGuidelines entry whose profile file exists."""
    out = []
    for e in m.get("brandGuidelines", []) or []:
        path = os.path.join(base, e["profile"])
        if os.path.exists(path):
            out.append((e, load(path), path))
        else:
            out.append((e, None, path))
    return out


def filled(p):
    logo = p.get("logo", {}) or {}
    return bool(p.get("colors") or p.get("typefaces") or p.get("nameForms")
                or any(logo.get(k) for k in ("aspectRatio", "minWidthPx", "minClearSpacePx")))


# --- color distance (CIE76 in Lab: ~2 is barely visible, ~10 is "a different red") ---------
def to_rgb(h):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def to_lab(h):
    def lin(c):
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(c) for c in to_rgb(h))
    x, y, z = (r * .4124 + g * .3576 + b * .1805) / .95047, r * .2126 + g * .7152 + b * .0722, (r * .0193 + g * .1192 + b * .9505) / 1.08883
    f = lambda t: t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
    fx, fy, fz = f(x), f(y), f(z)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def delta_e(a, b):
    return sum((p - q) ** 2 for p, q in zip(to_lab(a), to_lab(b))) ** 0.5


def neutral(h):
    _, a, b = to_lab(h)
    return (a * a + b * b) ** 0.5 < 6


def color_findings(color, where, p):
    """A warning if `color` is near a brand color but not it, or (strictPalette) off-palette."""
    pal = [(c["name"], c["hex"]) for c in p.get("colors", []) or [] if c.get("hex")]
    if not pal:
        return []
    dists = sorted((delta_e(color, h), n, h) for n, h in pal)
    d, name, h = dists[0]
    near = p.get("nearMissDeltaE", 10)
    if d < 1.5:
        return []
    full = name if name.lower().startswith(p["name"].lower()) else f"{p['name']} {name}"
    if d <= near:
        return [f"{where}: {color} is close to {full} {h.upper()} but isn't it (ΔE {d:.0f}); use the exact value."]
    if p.get("strictPalette") and not neutral(color):
        return [f"{where}: {color} isn't a {p['name']} color (nearest: {full} {h.upper()}); the palette is strict."]
    return []


def font_findings(family, where, p):
    allowed = {f.lower() for f in p.get("typefaces", []) or []}
    fam = family.strip().strip("\"'")
    if not allowed or fam.lower() in allowed or fam.lower() in GENERIC_FAMILIES:
        return []
    return [f"{where}: font '{fam}' isn't in the {p['name']} guidelines ({', '.join(p['typefaces'])})."]


def name_findings(text, where, p):
    forms = p.get("nameForms", []) or []
    if not forms:
        return []
    out = []
    for word in sorted({w for t in p.get("triggers", []) or [] for w in re.findall(rf"\b{re.escape(t)}\b", text, re.I)}):
        if word not in forms:
            out.append(f"{where}: the name is written '{word}'; the {p['name']} guidelines allow {', '.join(repr(f) for f in forms)}.")
    return out


def referenced(text, p, entry=None):
    if entry and entry.get("applies") == "always":
        return True
    if re.search(r'name=["\']brand-guidelines["\'][^>]*content=["\']' + re.escape(p.get("name", "")), text, re.I):
        return True
    return any(re.search(rf"\b{re.escape(t)}\b", text, re.I) for t in p.get("triggers", []) or [])


def unfilled_warning(p, path, where):
    src = p.get("source") or "the official guidelines"
    return (f"{where} refers to {p.get('name')}, but {path} has no values yet, so it can't be checked. "
            f"Fill it from {src}.")


def check_manifest(m, p):
    """For a system that is a brand's system (applies: always): tokens and typefaces vs the guidelines."""
    out = []
    color = m.get("color", {}) or {}
    resolved = color.get("resolved", {}) or {}
    for group in ("neutrals", "accents", "interactionStates"):
        for role, v in (color.get(group, {}) or {}).items():
            v = next(iter((resolved.get(f"{group}.{role}") or {}).values()), v)
            if isinstance(v, str) and v.startswith("#"):
                out += color_findings(v, f"manifest color.{group}.{role}", p)
    for role, fam in ((m.get("typography", {}) or {}).get("typefaces", {}) or {}).items():
        out += font_findings(fam, f"manifest typography.typefaces.{role}", p)
    return out


def check_text(text, where, p):
    """Source files and pages: name forms, hex colors, font-family declarations."""
    out = name_findings(re.sub(r"<[^>]+>", " ", text), where, p)
    for h in sorted(set(HEX.findall(text))):
        out += color_findings(h, where, p)
    for a, b in FONT_DECL.findall(text):
        first = (a or b).split(",")[0]
        if first.strip().startswith(("var(", "$", "{")):
            continue
        out += font_findings(first, where, p)
    return sorted(set(out))


def check_rendered(brand, p):
    """What capture.js measured on the rendered page, as (kind, warning) pairs."""
    out = [("name", w) for w in name_findings(brand.get("text", ""), "page text", p)]
    for color, where in (brand.get("colors") or {}).items():
        out += [("color", w) for w in color_findings(color, where, p)]
    for fam, where in (brand.get("fonts") or {}).items():
        out += [("font", w) for w in font_findings(fam, where, p)]
    logo = p.get("logo", {}) or {}
    for lg in brand.get("logos") or []:
        if logo.get("minWidthPx") and lg["w"] < logo["minWidthPx"]:
            out.append(("logo", f"{lg['where']}: the logo is {lg['w']}px wide; the {p['name']} minimum is {logo['minWidthPx']}px."))
        want = logo.get("aspectRatio") or (lg["naturalW"] / lg["naturalH"] if lg.get("naturalW") and lg.get("naturalH") else None)
        if want and lg["h"] and abs(lg["w"] / lg["h"] - want) / want > 0.03:
            out.append(("logo", f"{lg['where']}: the logo is drawn at {lg['w']}×{lg['h']}px, which stretches it (ratio {lg['w'] / lg['h']:.2f}, should be {want:.2f})."))
        if logo.get("minClearSpacePx") and lg.get("clearPx") is not None and lg["clearPx"] < logo["minClearSpacePx"]:
            out.append(("logo", f"{lg['where']}: {lg['clearPx']}px of clear space around the logo; the {p['name']} minimum is {logo['minClearSpacePx']}px."))
    return sorted(set(out))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*")
    ap.add_argument("--manifest", default="design-system-manifest.yaml")
    args = ap.parse_args()
    m = load(args.manifest)
    base = os.path.dirname(os.path.abspath(args.manifest))
    warnings = []
    for entry, p, path in profiles(m, base):
        if p is None:
            warnings.append(f"brandGuidelines lists {entry['profile']}, which doesn't exist.")
            continue
        if entry.get("applies") == "always":
            warnings += ([unfilled_warning(p, entry['profile'], "The manifest")] if not filled(p) else check_manifest(m, p))
        for f in args.files:
            text = open(f, errors="replace").read()
            if not referenced(text, p, entry):
                continue
            warnings += [unfilled_warning(p, entry['profile'], f)] if not filled(p) else check_text(text, f, p)
    for w in warnings:
        print("  ⚠", w)
    print(f"brand: {len(warnings)} warning(s)" if warnings else "brand: nothing to warn about")
    return 2 if warnings else 0


if __name__ == "__main__":
    sys.exit(main())

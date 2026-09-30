#!/usr/bin/env python3
"""Render a design or built page at the standard viewports and measure it.

Usage: python3 tools/screenshots.py <page.html | URL> --out <dir>
           [--manifest design-system-manifest.yaml] [--id ID]
       python3 tools/screenshots.py --provided <images…> --out <dir> [--id ID]
           (records screenshots someone gave you: pixel sizes, with the context left to fill in)

Takes full-page screenshots at the narrowest width (mobile.minViewportPx),
the phone, each breakpoint and desktop, plus the narrow and phone widths at
mobile.maxTextScalePercent text. From the rendered page it measures what a
screenshot can only estimate: sideways overflow, touch targets below
accessibility.minTouchTargetPx, text below minReadableTextPx, clipped text,
and the computed padding and type of every component, which it checks
against spacing.roles and typography.styles.

Writes <dir>/screenshot-set.yaml (schemas/screenshot-set.schema.json) and
the PNGs. The critic reads both. Exit 0 = no findings, 2 = findings.
Needs Node with Playwright and Chromium (npm i -g playwright).
"""
import argparse
import datetime
import json
import os
import re
import subprocess
import sys
import tempfile
from collections import defaultdict

import yaml

import brand_check

HERE = os.path.dirname(os.path.abspath(__file__))


def config(m, target, out, manifest_path):
    mob, bps = m.get("mobile", {}) or {}, (m.get("layout", {}) or {}).get("breakpoints", {}) or {}
    boards = (m.get("platform", {}) or {}).get("claudeDesign", {}).get("canvasBoards", {}) or {}
    narrow, scale = mob.get("minViewportPx", 320), mob.get("maxTextScalePercent", 200)
    phone = (boards.get("phone") or {}).get("w", 390)
    desktop = (boards.get("desktop") or {}).get("w", 1440)
    vps = [{"name": "narrow", "w": narrow, "h": 640, "textScales": [100, scale], "inventory": True},
           {"name": "phone", "w": phone, "h": 844, "textScales": [100, scale], "inventory": False}]
    for name in ("md", "lg"):
        if name in bps:
            vps.append({"name": name, "w": bps[name], "h": 900, "textScales": [100], "inventory": False})
    vps.append({"name": "desktop", "w": desktop, "h": 900, "textScales": [100], "inventory": True})
    base = os.path.dirname(os.path.abspath(manifest_path))
    logos = sorted({r["selector"] for _, p, _ in brand_check.profiles(m, base) if p for r in brand_check.logo_rules(p) if r.get("selector")})
    return {"target": target, "outDir": out, "viewports": vps,
            "repetition": (m.get("antiAiDesign", {}) or {}).get("repetition", {}) or {},
            "logoSelectors": logos,
            "primaryHexes": primary_hexes(m, base),
            "minTouch": (m.get("accessibility", {}) or {}).get("minTouchTargetPx", 44),
            "minTextPx": (m.get("usabilityHeuristics", {}) or {}).get("displayDesign", {}).get("minReadableTextPx", 12)}


def primary_hexes(m, base):
    """The primary action color of the project's system and of any reference brand system."""
    out = []
    for mm in [m] + [yaml.safe_load(open(os.path.join(base, e["designSystem"]))) or {}
                     for e in m.get("brandGuidelines", []) or [] if e.get("designSystem") and os.path.exists(os.path.join(base, e["designSystem"]))]:
        c = mm.get("color", {}) or {}
        v = next(iter(((c.get("resolved") or {}).get("accents.primary") or {}).values()), None) or (c.get("accents") or {}).get("primary")
        if isinstance(v, str) and v.startswith("#"):
            out.append(v.lower())
    return out


CONTENT_DEFAULTS = {"maxWordsPerBlock": 30, "maxSentencesPerBlock": 2, "maxIntroWords": 20, "maxWordsFirstScreen": 60,
                    "maxWordsPerScreen": 250, "maxNumbersInProse": 2}
FIGURE = re.compile(r"(?:[$€£¥]\s?)?\d[\d,.]*(?:\s?(?:%|k|m|bn))?", re.I)
STEPS = re.compile(r"\b(first|then|next|after that|afterwards|finally|step \d+|once you)\b", re.I)
INSTRUCTS = re.compile(r"\b(click|tap|press|select the|use the \w+ (?:button|menu|link|tab)|scroll)\b", re.I)


def inline_list(text):
    """'a, b, c and d': three or more short items in a sentence."""
    for sentence in re.split(r"(?<=[.!?])\s+", text):
        parts = sentence.rstrip(".!?").split(", ")
        if len(parts) >= 3 and re.search(r"\b(and|or)\b", parts[-1]) and all(len(x.split()) <= 3 for x in parts[1:-1]):
            return True
    return False


def content_findings(m, shots):
    """Text limits, information in prose that has a better form, and the measurable parts of 3-3-3."""
    cp = {**CONTENT_DEFAULTS, **((m.get("contentPolicy") or {}))}
    t3 = ((m.get("usabilityHeuristics") or {}).get("threeThreeThree") or {})
    tt = {"readingWordsPerMinute": 200, "secondsPerField": 8, "secondsPerChoice": 3, **(cp.get("taskTime") or {})}
    out, seen = [], set()

    def add(sev, cat, item, desc, shot):
        if (item, desc) not in seen:
            seen.add((item, desc))
            out.append({"severity": sev, "category": cat, "rubricItem": item, "description": desc,
                        "evidence": {"kind": "rendered-measurement", "ref": shot["file"], "measured": True}})
    C, T = "content-and-purpose", "three-three-three-usability"
    for s in shots:
        c = (s.get("antiAi") or {}).get("content")
        if not c:
            continue
        for b in c["blocks"]:
            if b["intro"] and b["words"] > cp["maxIntroWords"]:
                add("major", C, f"The line under a title is over {cp['maxIntroWords']} words: say what the page is for, in one line",
                    f"{b['where']}: {b['words']} words.", s)
            elif b["words"] > cp["maxWordsPerBlock"]:
                add("major", C, f"Text block over {cp['maxWordsPerBlock']} words: keep one short sentence, and put the rest behind a disclosure or on another page",
                    f"{b['where']}: {b['words']} words.", s)
            elif b["sentences"] > cp["maxSentencesPerBlock"]:
                add("major", C, f"Text block over {cp['maxSentencesPerBlock']} sentences", f"{b['where']}: {b['sentences']} sentences.", s)
            figs = [f for f in FIGURE.findall(b["text"]) if re.search(r"\d", f)]
            if b["words"] >= 8 and len(figs) > cp["maxNumbersInProse"]:
                add("major", C, "Numbers in a sentence: show them as stats, a table or a chart, not prose",
                    f"{b['where']}: {len(figs)} figures ({', '.join(figs[:4])}).", s)
            if len(STEPS.findall(b["text"])) >= 2:
                add("major", C, "Steps written as prose: show them as a stepper or a numbered list",
                    f"{b['where']}: '{b['text'][:70]}…'", s)
            if b["words"] >= 6 and INSTRUCTS.search(b["text"]):
                add("minor", C, "Instructions for the interface in prose: make the control explain itself (its label, one helper line, or the empty state)",
                    f"{b['where']}: '{b['text'][:70]}…'", s)
            if inline_list(b["text"]):
                add("minor", C, "Items listed in a sentence: show them as a list", f"{b['where']}: '{b['text'][:70]}…'", s)
        for t in c["tables"]:
            if t["rows"] <= 1:
                add("minor", C, "A table with one row: show it as label-value pairs", f"{t['where']}.", s)
            elif t["cols"] <= 1:
                add("minor", C, "A table with one column: show it as a list", f"{t['where']}.", s)
        if c["totalWords"] > cp["maxWordsPerScreen"]:
            add("major", C, f"Over {cp['maxWordsPerScreen']} words on one screen: cut, or move reference text to a disclosure or another page",
                f"{c['totalWords']} words.", s)
        if s["viewport"]["name"] != "narrow":
            continue
        # 3 seconds, at the narrowest width: the purpose and the primary action, in the first screen
        g, vh = c["glance"], c["viewportH"]
        if not g["h1"]:
            add("major", T, "3 seconds: no page title (h1), so the page's purpose isn't stated", "No visible h1.", s)
        elif g["h1"]["top"] >= vh:
            add("major", T, "3 seconds: the page title is below the first screen", f"{g['h1']['where']} starts at {g['h1']['top']}px; the screen is {vh}px.", s)
        if g["primaries"] and min(p_["top"] for p_ in g["primaries"]) >= vh:
            add("major", T, f"3 seconds: the primary action is below the first screen at {s['viewport']['w']}px",
                f"{g['primaries'][0]['where']} starts at {g['primaries'][0]['top']}px; the screen is {vh}px.", s)
        maxp = ((m.get("color") or {}).get("usagePolicy") or {}).get("maxPrimaryActionsPerScreen", 1)
        if len(g["primaries"]) > maxp:
            add("major", T, "More than one primary action on the screen", ", ".join(p_["where"] for p_ in g["primaries"][:4]) + ".", s)
        if c["firstScreenWords"] > cp["maxWordsFirstScreen"]:
            add("major", T, f"3 seconds: over {cp['maxWordsFirstScreen']} words to read before the first scroll",
                f"{c['firstScreenWords']} words in the first {vh}px at {s['viewport']['w']}px.", s)
        # 3 minutes: a rough estimate of this screen alone
        e = c["effort"]
        secs = e["words"] / tt["readingWordsPerMinute"] * 60 + e["fields"] * tt["secondsPerField"] + e["choices"] * tt["secondsPerChoice"]
        limit = t3.get("maxCoreTaskMinutes", 3) * 60
        if secs > limit:
            add("major", T, f"3 minutes: this screen alone takes about {secs / 60:.1f} min (estimate)",
                f"{e['words']} words to read, {e['fields']} fields, {e['choices']} choices.", s)
        if not e["actions"] and not e["fields"]:
            add("minor", C, "No action on this page: is it a page? It may fit as a section of the page it's reached from, a panel, or a tooltip",
                "No buttons, links or fields outside navigation.", s)
    return out


def structure_findings(m, shots):
    """Cards with too many pieces of information, and navigation that's crowded, deep or hard to search."""
    comp = {"maxCardInformationAreas": 5, **((m.get("compositionHeuristics") or {}))}
    nh = {"maxItemsPerLevel": 7, "maxClicksToAnyOption": 2, "searchWhenOptionsOver": 15, "maxVisibleControls": 12,
          **((m.get("navigationHeuristics") or {}))}
    out, seen = [], {}

    def add(sev, cat, item, key, desc, shot):
        if key in seen:  # one finding per kind of card or nav; count the other instances, once each
            if desc not in seen[key]["_descs"]:
                seen[key]["_descs"].add(desc)
                seen[key]["_more"] = seen[key].get("_more", 0) + 1
            return
        f = {"severity": sev, "category": cat, "rubricItem": item, "description": desc,
             "evidence": {"kind": "rendered-measurement", "ref": shot["file"], "measured": True}}
        f["_descs"] = {desc}
        seen[key] = f
        out.append(f)
    N = "navigation-color-and-motion-feedback"
    for s in shots:
        st = (s.get("antiAi") or {}).get("structure")
        if not st:
            continue
        w = f"{s['viewport']['w']}px"
        for c in st["cards"]:
            if c["areas"] > comp["maxCardInformationAreas"]:
                kind = c["where"].split(' "')[0]
                add("major", "composition-and-density",
                    f"A card shows more than {comp['maxCardInformationAreas']} pieces of information: keep the ones that serve the page's purpose, and move the rest to the detail view",
                    ("card", kind), f"{c['where']}: {c['areas']} ({', '.join(c['parts'][:6])}).", s)
        for n in st["nav"]:
            if not n["visible"] and not n["hasOpener"]:
                add("major", N, "Navigation disappears at this width with no control to open it", ("nav-gone", n["where"], w),
                    f"{n['where']} is hidden at {w}.", s)
            for lv in n["levels"]:
                if lv["items"] > nh["maxItemsPerLevel"]:
                    add("major", N, f"More than {nh['maxItemsPerLevel']} items at one level: keep the most-used at the top, and group the rest one level down",
                        ("nav-level", lv["where"]), f"{lv['where']}: {lv['items']} items.", s)
            if n["maxClicks"] > nh["maxClicksToAnyOption"]:
                add("major", N, f"An option is more than {nh['maxClicksToAnyOption']} clicks deep: flatten the menu",
                    ("nav-deep", n["where"]), f"{n['where']}: {n['maxClicks']} clicks to the deepest option.", s)
            if n["options"] > nh["searchWhenOptionsOver"] and not st["search"]:
                add("major", N, f"Over {nh['searchWhenOptionsOver']} options and no search: add one, so anything can be found by name",
                    ("nav-search", n["where"]), f"{n['where']}: {n['options']} options.", s)
            for h in n["unlabelledHidden"]:
                add("major", N, "Hidden options with no labelled control to open them: they can't be found",
                    ("nav-hidden", h), f"{h} in {n['where']}.", s)
        if s["viewport"]["name"] == "narrow" and s["textScalePercent"] == 100 and st["controlsOnFirstScreen"] > nh["maxVisibleControls"]:
            add("major", N, f"More than {nh['maxVisibleControls']} controls on the first screen: nest the less-used ones behind one labelled control",
                ("controls", w), f"{st['controlsOnFirstScreen']} controls in the first screen at {w}.", s)
    for f in out:
        f.pop("_descs", None)
        more = f.pop("_more", 0)
        if more:
            f["description"] += f" (and {more} more like it)"
    return out


def step_px(m):
    t = (m.get("typography", {}) or {}).get("scale", {}) or {}
    steps = t.get("steps") or ["base"]
    b = steps.index("base") if "base" in steps else 0
    return {s: round(t.get("baseSizePx", 16) * t.get("ratio", 1.25) ** (i - b)) for i, s in enumerate(steps)}


def inventory_and_findings(m, shots):
    findings = []
    add = lambda sev, cat, item, desc, shot: findings.append(
        {"severity": sev, "category": cat, "rubricItem": item, "description": desc,
         "evidence": {"kind": "rendered-measurement", "ref": shot["file"], "measured": True}})
    for s in shots:
        where = f"{s['viewport']['w']}px" + (f" at {s['textScalePercent']}% text" if s["textScalePercent"] != 100 else "")
        if s["overflowPx"] > 0 and s["viewport"]["name"] in ("narrow", "phone"):
            who = ", ".join(o["element"] for o in s["offenders"]) or "the page"
            add("blocker", "mobile-and-dynamic-components", "Content scrolls sideways at minViewportPx",
                f"Scrolls sideways by {s['overflowPx']}px at {where}; widest: {who}.", s)
        if s["textScalePercent"] != 100:
            for t in s.get("notScaling", [])[:8]:
                add("major", "mobile-and-dynamic-components", "Text doesn't grow with the text scale (WCAG 1.4.4): it's set in fixed px",
                    f"{t['element']} stays {t['fontSizePx']:g}px at {where}.", s)
            for c in s["clipped"][:5]:
                add("major", "mobile-and-dynamic-components", "Text is clipped at maxTextScalePercent", f"{c['element']} is clipped at {where}.", s)
        if s["textScalePercent"] == 100:
            for t in s["smallTargets"][:8]:
                add("blocker", "accessibility", "Interactive targets smaller than accessibility.minTouchTargetPx",
                    f"{t['element']} is {t['widthPx']}×{t['heightPx']}px at {where}.", s)
            for t in s["smallText"][:8]:
                add("major", "display-design-wickens", "Text below minReadableTextPx (Wickens 1: legibility)",
                    f"{t['element']} is {t['fontSizePx']:g}px at {where}.", s)
    # de-duplicate findings repeated across widths
    seen, unique = set(), []
    for f in findings:
        key = (f["rubricItem"], f["description"].split(" at ")[0])
        if key not in seen:
            seen.add(key)
            unique.append(f)

    # computed-style inventory, checked against roles and styles
    roles = {}
    for r in (m.get("spacing", {}) or {}).get("roles", []) or []:
        for el in r.get("appliesTo", []) or []:
            roles[(el, r.get("property", "padding"))] = r
    styles = {el: st for st in (m.get("typography", {}) or {}).get("styles", []) or [] for el in st.get("appliesTo", []) or []}
    px_of = step_px(m)
    spacing, typo = defaultdict(list), defaultdict(list)
    for s in shots:
        for e in s.get("inventory") or []:
            where = f"{e['where']} @ {s['file']}"
            t, r, b, l = e["padding"]
            if any(e["padding"]):
                spacing[(e["key"], "padding-y")].append((t, where))
                spacing[(e["key"], "padding-x")].append((l, where))
            if e["gap"]:
                spacing[(e["key"], "gap")].append((e["gap"], where))
            typo[e["key"]].append((e["fontSizePx"], e["fontWeight"], where, e.get("tag")))
    inv_sp, inv_ty = [], []
    for (key, prop), found in sorted(spacing.items()):
        role = roles.get((key, prop)) or (roles.get((key, "padding")) if prop.startswith("padding") else None)
        values = sorted({v for v, _ in found})
        ok = len(values) == 1 and (not role or values[0] == role["px"])
        inv_sp.append({"element": key, "property": prop, **({"role": role["name"], "expectedPx": role["px"]} if role else {}),
                       "found": [{"px": v, "where": w} for v, w in found], "consistent": ok})
        if not ok and (role or len(values) > 1):
            desc = f"{key} {prop}: " + "; ".join(f"{v}px ({sum(1 for x, _ in found if x == v)}×)" for v in values)
            if role:
                desc += f"; role '{role['name']}' is {role['px']}px"
            unique.append({"severity": "major", "category": "token-and-scale-consistency",
                           "rubricItem": "The same kind of element has different spacing, or isn't its role's value",
                           "description": desc + ".", "evidence": {"kind": "rendered-measurement", "ref": "computed styles", "measured": True}})
    for key, found in sorted(typo.items()):
        st = styles.get(key) or styles.get(found[0][3] if key == found[0][3] else None)
        found = [(f, w, wh) for f, w, wh, _ in found]
        combos = sorted({(round(f), w) for f, w, _ in found})
        exp = (px_of.get(st["step"]), st["weight"]) if st else None
        ok = len(combos) == 1 and (not exp or combos[0] == exp)
        inv_ty.append({"element": key, **({"style": st["name"], "expected": f"{exp[0]}px / {exp[1]}"} if st else {}),
                       "found": [{"value": f"{f:g}px / {w}", "where": wh} for f, w, wh in found], "consistent": ok})
        if not ok and (st or len(combos) > 1):
            desc = f"<{key}>: " + "; ".join(f"{f}px / {w}" for f, w in combos)
            if st:
                desc += f"; style '{st['name']}' is {exp[0]}px / {exp[1]}"
            unique.append({"severity": "major", "category": "token-and-scale-consistency",
                           "rubricItem": "Text of the same kind uses different styles, or isn't its style",
                           "description": desc + ".", "evidence": {"kind": "rendered-measurement", "ref": "computed styles", "measured": True}})
    return unique, {"spacing": inv_sp, "typography": inv_ty}


def anti_ai_findings(m, shots, manifest_path, declared=()):
    """Repetition, fonts, and brand guidelines, from the inventory shots."""
    out, seen = [], set()
    base = os.path.dirname(os.path.abspath(manifest_path))

    def add(sev, cat, item, desc, shot):
        if (item, desc) not in seen:
            seen.add((item, desc))
            out.append({"severity": sev, "category": cat, "rubricItem": item, "description": desc,
                        "evidence": {"kind": "rendered-measurement", "ref": shot["file"], "measured": True}})
    tf = (m.get("typography", {}) or {}).get("typefaces", {}) or {}
    ours = {v.lower() for v in tf.values() if isinstance(v, str)}
    generic = set(brand_check.generic_fonts(m))
    max_fam = ((m.get("antiAiDesign", {}) or {}).get("typefaces", {}) or {}).get("maxFamilies", 2)
    for s in shots:
        a = s.get("antiAi")
        if not a:
            continue
        for r in a["repeatedText"]:
            add("major", "anti-ai-design", "The same information appears twice on one screen: say it once, as one stronger element",
                f"'{r['value'][:60]}' appears in {', '.join(r['where'])}.", s)
        for r in a["repeatedFigures"]:
            add("major", "anti-ai-design", "The same figure appears twice on one screen: show it once, where it matters most",
                f"{r['value']} appears in {', '.join(r['where'])}.", s)
        required = brand_check.brand_fonts(m, base, a["brand"]["text"], declared)
        fams = {f: v for f, v in a["fonts"].items() if f.lower() not in brand_check.GENERIC_FAMILIES}
        for fam, v in fams.items():
            if not v["renders"]:
                add("major", "anti-ai-design", "A font the page asks for doesn't load, so it renders in a fallback",
                    f"'{fam}' ({v['where']}) renders in the fallback: load it (@font-face or a font link).", s)
            elif ours and fam.lower() not in ours and fam.lower() not in required:
                add("major", "token-and-scale-consistency", "Text uses a font that isn't one of the manifest's typefaces",
                    f"'{fam}' ({v['where']}); the typefaces are {', '.join(sorted(set(tf.values())))}.", s)
            if fam.lower() in generic and fam.lower() not in required:
                add("major", "anti-ai-design", "A default font: choose a pairing for this product (reference/type-pairing.md)",
                    f"'{fam}' ({v['where']}) is a default font.", s)
        mono = [f for f in fams if "mono" in f.lower() or f.lower() == (tf.get("mono") or "").lower()]
        if len(fams) - len(mono) > max_fam:
            add("minor", "anti-ai-design", f"More than {max_fam} type families (plus one mono)", f"{', '.join(fams)}.", s)
        text = a["brand"]["text"]
        for entry, p, path in brand_check.profiles(m, base):
            if not p:
                continue
            applies = brand_check.referenced(text, p, entry, declared)
            item = f"Meant to follow the {p.get('name')} guidelines, and doesn't match"
            if not brand_check.filled(p):
                if applies:
                    add("minor", "brand-guidelines", item, brand_check.unfilled_warning(p, entry['profile'], "The page"), s)
                continue
            kinds = {"color": "colors", "font": "fonts", "name": "how the name is written", "logo": "the logo", "type": "type roles"}
            for kind, w in brand_check.check_rendered(a["brand"], p):
                if applies:
                    add("major", "brand-guidelines", f"{item}: {kinds[kind]}", w, s)
                elif kind == "logo":  # a brand's logo follows its rules on any page
                    add("major", "brand-guidelines", f"The {p.get('name')} logo breaks its rules", w, s)
    return out


def image_size(path):
    """(width, height) of a PNG or JPEG, without extra libraries."""
    import struct
    with open(path, "rb") as f:
        head = f.read(26)
        if head[:8] == b"\x89PNG\r\n\x1a\n":
            return struct.unpack(">II", head[16:24])
        if head[:2] == b"\xff\xd8":
            f.seek(2)
            while True:
                marker, = struct.unpack(">H", f.read(2))
                length, = struct.unpack(">H", f.read(2))
                if marker in (0xFFC0, 0xFFC1, 0xFFC2):
                    h, w = struct.unpack(">xHH", f.read(5))
                    return w, h
                f.seek(length - 2, 1)
    return None, None


def provided(files, out, set_id):
    os.makedirs(out, exist_ok=True)
    shots = []
    for f in files:
        w, h = image_size(f)
        shots.append({"file": f, "imagePx": {"w": w, "h": h},
                      "viewport": {"w": None, "h": None}, "pixelDensity": None,
                      "textScalePercent": None, "theme": None, "state": None})
    record = {"id": set_id or os.path.basename(out.rstrip("/")), "source": "provided",
              "capturedAt": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
              "shots": shots, "findings": []}
    with open(os.path.join(out, "screenshot-set.yaml"), "w") as fh:
        yaml.safe_dump(record, fh, sort_keys=False, allow_unicode=True)
    print(f"{record['id']}: {len(shots)} provided screenshot(s) recorded → {os.path.relpath(out)}/screenshot-set.yaml")
    for s in shots:
        print(f"  {s['file']}: {s['imagePx']['w']}×{s['imagePx']['h']}px image. Viewport, pixel density, text size, theme and state: unknown, so ask.")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target", nargs="?")
    ap.add_argument("--provided", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--manifest", default="design-system-manifest.yaml")
    ap.add_argument("--id", default=None)
    ap.add_argument("--brand", action="append", default=[], help="brand guidelines the design declares, e.g. --brand Atari")
    args = ap.parse_args()
    if args.provided:
        return provided(args.provided, os.path.abspath(args.out), args.id)
    if not args.target:
        sys.exit("Give a page or URL to render, or --provided <images…>")
    m = yaml.safe_load(open(args.manifest)) or {}
    target = args.target if "://" in args.target else "file://" + os.path.abspath(args.target)
    out = os.path.abspath(args.out)
    cfg = config(m, target, out, args.manifest)
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(cfg, f)
    env = dict(os.environ)
    try:
        env["NODE_PATH"] = subprocess.run(["npm", "root", "-g"], capture_output=True, text=True).stdout.strip()
    except FileNotFoundError:
        sys.exit("Needs Node.js with Playwright: npm i -g playwright")
    res = subprocess.run(["node", os.path.join(HERE, "render", "capture.js"), f.name], env=env, capture_output=True, text=True)
    os.unlink(f.name)
    if res.returncode:
        sys.exit("Rendering failed: " + res.stderr.strip())
    shots = json.load(open(os.path.join(out, "results.json")))["shots"]
    os.unlink(os.path.join(out, "results.json"))
    # Work that declares a reference brand (e.g. the Atari guidelines) is checked against that
    # brand's design system instead of the project's.
    text = next((x["antiAi"]["brand"]["text"] for x in shots if x.get("antiAi")), "")
    ref = brand_check.reference_system(m, os.path.dirname(os.path.abspath(args.manifest)), text, args.brand)
    system_path = ref[1] if ref else args.manifest
    if ref:
        m = yaml.safe_load(open(system_path)) or {}
    findings, inventory = inventory_and_findings(m, shots)
    findings += anti_ai_findings(m, shots, system_path, args.brand)
    findings += content_findings(m, shots)
    findings += structure_findings(m, shots)
    record = {
        "id": args.id or os.path.basename(out.rstrip("/")),
        "source": "rendered",
        "target": args.target,
        "capturedAt": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "designSystem": f"{(m.get('meta') or {}).get('name')}" + (f" (reference: the {ref[0]} guidelines are declared)" if ref else ""),
        "manifestVersion": (m.get("meta") or {}).get("version"),
        "shots": [{"file": s["file"], "viewport": s["viewport"], "textScalePercent": s["textScalePercent"],
                   "method": "root font-size" if s["textScalePercent"] != 100 else "none",
                   "overflowPx": s["overflowPx"]} for s in shots],
        "computedInventory": inventory,
        "findings": findings,
    }
    with open(os.path.join(out, "screenshot-set.yaml"), "w") as f:
        yaml.safe_dump(record, f, sort_keys=False, allow_unicode=True)
    print(f"{record['id']}: {record['designSystem']}, {len(shots)} screenshots, {len(findings)} finding(s) → {os.path.relpath(out)}/screenshot-set.yaml")
    for fd in findings:
        print(f"  [{fd['severity']}] {fd['description']}")
    return 2 if findings else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Check that the same kind of element has the same spacing and type everywhere.

Usage: python3 tools/consistency_check.py <file-or-dir>... [--manifest design-system-manifest.yaml]
                                          [--root .] [--inventory]

The token lint checks each value is on the scale; this checks consistency
across files. Every component (<Card>, <Button>) and text element (h1–h6, p,
label) is collected with its padding, gap and text style (Tailwind classes),
then checked two ways:
  - the same element with different values in different places
  - a value that isn't its spacing.roles / typography.styles entry
--inventory prints the inventory in the audit report's consistencyInventory
shape, for the critic.

Exit 0 = consistent, 2 = findings.
"""
import argparse
import os
import re
import sys
from collections import defaultdict

import yaml

TAG = re.compile(r"<([A-Z][\w.]*|h[1-6]|p|label|button|li)\b([^>]*?)className=\s*[\"'{`]+([^\"'`}]*)", re.S)
SPACING = re.compile(r"(?<![\w-])(p|px|py|gap|space-y|space-x)-(\d+(?:\.5)?|\[\d+px\])(?![\w-])")
SIZE = re.compile(r"(?<![\w-])text-(xs|sm|base|lg|[2-9]?xl)(?![\w-])")
WEIGHT = re.compile(r"(?<![\w-])font-(thin|extralight|light|normal|medium|semibold|bold|extrabold|black)(?![\w-])")
WEIGHTS = {"thin": 100, "extralight": 200, "light": 300, "normal": 400, "medium": 500, "semibold": 600, "bold": 700, "extrabold": 800, "black": 900}
PROPERTY = {"p": "padding", "px": "padding-x", "py": "padding-y", "gap": "gap", "space-y": "gap", "space-x": "gap"}
EXTS = (".tsx", ".jsx", ".ts", ".js", ".vue", ".svelte", ".html")


def px_of(v):
    return float(v[1:-3]) if v.startswith("[") else float(v) * 4


def files_in(paths):
    for p in paths:
        if os.path.isdir(p):
            for d, _, names in os.walk(p):
                yield from (os.path.join(d, n) for n in sorted(names) if n.endswith(EXTS))
        elif p.endswith(EXTS):
            yield p


def collect(paths, root):
    spacing = defaultdict(list)   # (element, property) -> [(px, where)]
    text = defaultdict(list)      # element -> [(step, weight, where)]
    for f in files_in(paths):
        src = open(f, encoding="utf-8", errors="replace").read()
        rel = os.path.relpath(f, root)
        for m in TAG.finditer(src):
            tag, classes = m.group(1), m.group(3)
            where = f"{rel}:{src.count(chr(10), 0, m.start()) + 1}"
            for prefix, v in SPACING.findall(classes):
                spacing[(tag, PROPERTY[prefix])].append((px_of(v), where))
            size, weight = SIZE.search(classes), WEIGHT.search(classes)
            if size or weight:
                text[tag].append((size.group(1) if size else None, WEIGHTS[weight.group(1)] if weight else None, where))
    return spacing, text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--manifest", default="design-system-manifest.yaml")
    ap.add_argument("--root", default=os.environ.get("CLAUDE_PROJECT_DIR", "."))
    ap.add_argument("--inventory", action="store_true")
    args = ap.parse_args()
    m = yaml.safe_load(open(os.path.join(args.root, args.manifest))) or {}
    roles = {}
    for r in (m.get("spacing", {}) or {}).get("roles", []) or []:
        for el in r.get("appliesTo", []) or []:
            prop = r.get("property", "padding")
            roles[(el, prop)] = r
            if prop == "padding":  # a padding role also governs each axis
                roles.setdefault((el, "padding-x"), r)
                roles.setdefault((el, "padding-y"), r)
    styles = {el: s for s in (m.get("typography", {}) or {}).get("styles", []) or [] for el in s.get("appliesTo", []) or []}

    spacing, text = collect(args.paths, args.root)
    findings, inv_sp, inv_ty = [], [], []

    for (el, prop), found in sorted(spacing.items()):
        values = sorted({v for v, _ in found})
        role = roles.get((el, prop))
        consistent = len(values) == 1 and (not role or values[0] == role["px"])
        inv_sp.append({"element": el, "property": prop, **({"role": role["name"], "expectedPx": role["px"]} if role else {}),
                       "found": [{"px": v, "where": w} for v, w in found], "consistent": consistent})
        if len(values) > 1:
            by = "; ".join(f"{v:g}px at {', '.join(w for x, w in found if x == v)}" for v in values)
            findings.append(f"{el} {prop} differs across the product: {by}.")
        if role:
            wrong = [(v, w) for v, w in found if v != role["px"]]
            if wrong:
                findings.append(f"{el} {prop} should be {role['px']:g}px (spacing role '{role['name']}'), but is "
                                + "; ".join(f"{v:g}px at {w}" for v, w in wrong) + ".")

    for el, found in sorted(text.items()):
        combos = sorted({(s or "?", str(w) if w else "?") for s, w, _ in found})
        st = styles.get(el)
        expected = f"{st['step']} / {st['weight']}" if st else None
        mism = [(s, w, where) for s, w, where in found if st and ((s and s != st["step"]) or (w and w != st["weight"]))]
        consistent = len(combos) == 1 and not mism
        inv_ty.append({"element": el, **({"style": st["name"], "expected": expected} if st else {}),
                       "found": [{"value": f"{s or '?'} / {w or '?'}", "where": where} for s, w, where in found], "consistent": consistent})
        if len(combos) > 1:
            findings.append(f"<{el}> text differs across the product: "
                            + "; ".join(f"{s} / {w} at {', '.join(x for a, b, x in found if (a or '?', str(b) if b else '?') == (s, w))}" for s, w in combos) + ".")
        for s, w, where in mism:
            findings.append(f"<{el}> at {where} is {s or '?'} / {w or '?'}, but the '{st['name']}' style is {expected}.")

    if args.inventory:
        print(yaml.safe_dump({"consistencyInventory": {"spacing": inv_sp, "typography": inv_ty}}, sort_keys=False, allow_unicode=True))
        return 0 if not findings else 2
    n_el = len({el for el, _ in spacing} | set(text))
    print(f"Consistency: {'CONSISTENT' if not findings else f'{len(findings)} finding(s)'} across {n_el} kinds of element")
    for f in findings:
        print("  •", f)
    return 0 if not findings else 2


if __name__ == "__main__":
    sys.exit(main())

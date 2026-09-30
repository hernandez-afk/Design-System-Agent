#!/usr/bin/env python3
"""Place a brief against existing designs, without the model doing the arithmetic.

Usage: python3 tools/scope_check.py <ticket-brief.yaml> --index design-index.yaml
                                    [--manifest design-system-manifest.yaml]

Scores every design in the index by shared scope terms and shared surfaces
(a parent surface matches its children), using scopePolicy's weights with the
priority weight spread over the other two, since priority overlap is a
judgment call left to the person. Then routes each surface the brief touches:
one an existing design owns is a revision of that design, not new work.
Prints only what matters: related designs, and routes to other designs.
Exit 0 = new work only, 1 = overlaps to decide.
"""
import argparse
import sys

import yaml


def load(p):
    with open(p) as f:
        return yaml.safe_load(f) or {}


def surface_match(a, b):
    return a == b or a.startswith(b + "/") or b.startswith(a + "/")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("brief")
    ap.add_argument("--index", required=True)
    ap.add_argument("--manifest")
    args = ap.parse_args()
    b, idx = load(args.brief), load(args.index)
    pol = (load(args.manifest).get("scopePolicy", {}) if args.manifest else {}) or {}
    oc = pol.get("overlapCheck", {}) or {}
    w = oc.get("weights", {}) or {}
    wt, ws = w.get("termOverlap", 0.4), w.get("surfaceOverlap", 0.35)
    wt, ws = wt / (wt + ws), ws / (wt + ws)
    merge, related = oc.get("mergeThreshold", 0.6), oc.get("relatedThreshold", 0.3)

    terms = {t.lower() for t in b.get("scopeTerms", [])}
    surfaces = b.get("surfaces", [])
    rows, routes = [], []
    for p in idx.get("projects", []):
        if p["id"] == b.get("ticketKey"):
            continue
        pt = {t.lower() for t in p.get("scopeTerms", [])}
        ps = p.get("surfaces", [])
        t = len(terms & pt) / len(terms | pt) if terms | pt else 0
        matched = [s for s in surfaces if any(surface_match(s, x) for x in ps)]
        union = set(surfaces) | set(ps)
        s = len(matched) / len(union) if union else 0
        score = wt * t + ws * s
        if score > 0:
            dep = p.get("status") == "deprecated"
            cls = "unrelated" if dep or score < related else "belongs-to-existing" if score >= merge else "related"
            rows.append((score, p, cls, sorted(terms & pt), matched))
        if p.get("status") != "deprecated":
            routes += [(s_, p) for s_ in surfaces if any(s_ == x or s_.startswith(x + "/") for x in ps)]

    rows.sort(key=lambda r: -r[0])
    shown = [r for r in rows if r[2] != "unrelated"]
    print(f"{b.get('ticketKey')} scope: " + ("new work, no related designs" if not shown and not routes else
                                             f"{len(shown)} related design(s), {len(routes)} surface(s) owned elsewhere"))
    for score, p, cls, shared_t, shared_s in shown:
        print(f"  {p['id']} {p['title']} ({p.get('status')}): {score:.2f} {cls}; terms {shared_t or '-'}, surfaces {shared_s or '-'}")
    for s_, p in routes:
        print(f"  route: '{s_}' is owned by {p['id']} {p['title']}: work there is a revision of {p['id']}")
    return 1 if shown or routes else 0


if __name__ == "__main__":
    sys.exit(main())

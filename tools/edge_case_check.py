#!/usr/bin/env python3
"""Check a brief's edge-case sweep (skills/design-agent/reference/edge-case-sweep.md) is complete.

Usage: python3 tools/edge_case_check.py <ticket-brief.yaml> [--index design-index.yaml]
                                        [--manifest design-system-manifest.yaml]

Checks that every entity has a decision for each part of its life (create,
source, and any others listed), that designs it names exist in the index,
that every lens was considered, that in-scope cases point at something in the
brief, and that no question is left open. Lists the new briefs the sweep says
are needed, like an admin side nobody briefed.

Result: COMPLETE (exit 0), NEEDS ANSWERS (exit 1), INCOMPLETE (exit 2).
"""
import argparse
import re
import sys

import yaml

LENSES = ["ecosystem", "roles", "setup", "time", "concurrency", "integrity", "scale",
          "failure", "ending", "communication", "privacy", "access"]


def load(path):
    with open(path) as f:
        return yaml.safe_load(f) or {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("brief")
    ap.add_argument("--index")
    ap.add_argument("--manifest")
    args = ap.parse_args()
    b = load(args.brief)
    index = load(args.index) if args.index else {"projects": []}
    manifest = load(args.manifest) if args.manifest else {}
    projects = {p["id"]: p for p in index.get("projects", [])}
    lenses = LENSES + [l["name"] for l in manifest.get("briefPolicy", {}).get("edgeCaseLenses", []) or []]

    incomplete, questions, new_briefs, notes = [], [], [], []
    ids = {x["id"] for x in b.get("acceptanceCriteria", []) + b.get("coreTasks", []) + b.get("priorities", [])}

    entities = b.get("entities") or []
    if not entities:
        incomplete.append("No entities listed: which things does this page show, act on or need, and who creates them?")
    for e in entities:
        for op, d in (e.get("operations") or {}).items():
            where = f"{e['name']} · {op}"
            how, ref = d.get("handledBy"), d.get("ref", "")
            if how == "existing-design":
                if ref not in projects:
                    incomplete.append(f"{where}: handled by '{ref}', which isn't in the design index.")
                elif projects[ref].get("status") == "deprecated":
                    incomplete.append(f"{where}: handled by {ref}, which is deprecated.")
            elif how == "new-brief":
                new_briefs.append((ref, where))
            elif how == "question":
                questions.append(f"{where}: {ref}")
            elif how == "out-of-scope" and not ref:
                incomplete.append(f"{where}: out of scope with no reason.")
        for op in ("create", "source"):
            if op not in (e.get("operations") or {}):
                incomplete.append(f"{e['name']}: no decision for '{op}'. Who does it, or where does it come from?")

    # things the brief talks about but never lists: the unbriefed admin side usually hides here
    names = [e["name"].lower() for e in entities]
    exempt = {t.lower() for t in b.get("nonEntityTerms", [])}
    for term in b.get("scopeTerms", []):
        head = term.lower().split()[0]
        if term.lower() in exempt or len(head) < 4:
            continue
        if not any(n[:3] == head[:3] for n in names):
            incomplete.append(f"'{term}' is one of the brief's scope terms but isn't listed as an entity. "
                              "Who creates it, and where does it come from? (Or list it in nonEntityTerms.)")

    cases = b.get("edgeCases") or []
    covered = {c["lens"] for c in cases} | ({"ecosystem"} if entities else set())
    for lens in lenses:
        if lens not in covered:
            incomplete.append(f"Lens '{lens}' wasn't considered: add a case, or 'not-applicable' with a reason.")
    out_of_scope_text = " ".join(b.get("outOfScope", [])).lower()
    for c in cases:
        where, action = f"{c['id']} ({c['lens']})", c.get("action", "")
        if c["disposition"] == "question":
            questions.append(f"{where}: {action or c['case']}")
        elif c["disposition"] == "new-brief":
            new_briefs.append((action or c["case"], where))
        elif c["disposition"] in ("out-of-scope", "not-applicable") and not action:
            incomplete.append(f"{where}: {c['disposition']} with no reason.")
        elif c["disposition"] == "in-scope":
            refs = set(re.findall(r"\b(?:AC|T|P)\d+\b", action))
            if not refs and not re.search(r"\b(element|state|flow)\b", action, re.I):
                incomplete.append(f"{where}: in scope, but its action doesn't point to an acceptance criterion, task, element, state or flow path.")
            for r in refs - ids:
                incomplete.append(f"{where}: points to {r}, which isn't in the brief.")
        if c["disposition"] == "out-of-scope" and action and not any(w in out_of_scope_text for w in re.findall(r"\w{5,}", action.lower())[:3]):
            notes.append(f"{where}: out of scope, but not listed in the brief's outOfScope.")

    status = "INCOMPLETE" if incomplete else "NEEDS ANSWERS" if questions else "COMPLETE"
    print(f"{b.get('ticketKey')} edge-case sweep: {status}  "
          f"({len(entities)} entities, {len(cases)} cases, {len(covered & set(lenses))}/{len(lenses)} lenses)")
    for i in incomplete:
        print("  ✗", i)
    for q in questions:
        print("  ?", q)
    if new_briefs:
        print("  New briefs needed:")
        seen = set()
        for title, where in new_briefs:
            if title not in seen:
                seen.add(title)
                print(f"    + {title}  (from {', '.join(w for t, w in new_briefs if t == title)})")
    for n in notes:
        print("  ·", n)
    return 2 if incomplete else 1 if questions else 0


if __name__ == "__main__":
    sys.exit(main())

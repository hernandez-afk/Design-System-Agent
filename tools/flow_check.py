#!/usr/bin/env python3
"""Check a user flow, and how it plugs into the product.

Usage: python3 tools/flow_check.py <user-flow.yaml> --index design-index.yaml
           [--brief ticket-brief.yaml] [--manifest design-system-manifest.yaml] [--mermaid]

Checks that every core task has a flow from a real entry point, every screen
is reachable and has a way out (no dead ends), every async step has an error
path, click counts are within the 3-3-3 limit, and every entry point on
another design's page has an integration change owned by that design.
--mermaid prints the flow as a Mermaid diagram instead.

Result: OK (exit 0), WARNINGS (exit 1), ERRORS (exit 2).
"""
import argparse
import sys
from collections import defaultdict

import yaml


def load(path):
    with open(path) as f:
        return yaml.safe_load(f) or {}


def entries_to(flow, f):
    return next((e["to"] for e in flow["entryPoints"] if e["id"] == f["entryPoint"]), f["steps"][0]["screen"])


def mermaid(flow):
    sid = {s["id"]: s for s in flow["screens"]}
    shape = {"new": ('["', '"]'), "existing": ('("', '")'), "system": ('[/"', '"/]'), "external": ('>"', '"]')}
    lines = ["flowchart LR"]
    for s in flow["screens"]:
        a, b = shape[s["kind"]]
        lines.append(f'  {s["id"]}{a}{s["name"]}{b}')
    for e in flow["entryPoints"]:
        lines.append(f'  {e["from"]} -->|"{e["id"]}: {e["trigger"]}"| {e["to"]}')
    for f in flow["flows"]:
        for st in f["steps"]:
            if st.get("next"):
                lines.append(f'  {st["screen"]} -->|"{f["taskId"]}: {st["action"]}"| {st["next"]}')
    for f in flow["flows"]:
        for a in f["alternatePaths"]:
            if a.get("to"):
                lines.append(f'  {entries_to(flow, f)} -.->|"{f["taskId"]} {a["kind"]}"| {a["to"]}')
    for b in flow.get("backNavigation", []):
        if b.get("to"):
            lines.append(f'  {b["screen"]} -.->|"back"| {b["to"]}')
    for x in flow.get("exits", []):
        lines.append(f'  {x["from"]} -.->|"{x["when"]}"| {x["to"]}')
    for ic in flow["integrationChanges"]:
        if ic["screen"] in sid:
            lines.append(f'  {ic["screen"]}:::changed')
    lines.append("  classDef changed stroke-dasharray: 4 3")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("flow")
    ap.add_argument("--index", required=True)
    ap.add_argument("--brief")
    ap.add_argument("--manifest")
    ap.add_argument("--mermaid", action="store_true")
    args = ap.parse_args()
    flow, index = load(args.flow), load(args.index)
    if args.mermaid:
        print(mermaid(flow))
        return 0

    errors, warnings = [], []
    screens = {s["id"]: s for s in flow["screens"]}
    projects = {p["id"]: p for p in index.get("projects", [])}
    surface_owner = {s: p["id"] for p in index.get("projects", []) for s in p.get("surfaces", [])}
    entries = {e["id"]: e for e in flow["entryPoints"]}
    max_clicks = 3
    if args.manifest:
        max_clicks = (load(args.manifest).get("usabilityHeuristics", {}).get("threeThreeThree", {}) or {}).get("maxClicksToCoreTask", 3)

    # screens are real
    for s in flow["screens"]:
        if s["kind"] in ("new", "existing") and not s.get("surface"):
            errors.append(f"Screen {s['id']} ({s['name']}) is '{s['kind']}' but has no surface.")
        if s["kind"] == "existing":
            owner = surface_owner.get(s.get("surface"))
            if not owner:
                errors.append(f"Screen {s['id']} ({s['name']}) is 'existing', but no design in the index owns surface '{s.get('surface')}'. Run the scope check.")
            elif s.get("owningProject") and s["owningProject"] != owner:
                errors.append(f"Screen {s['id']} says it's owned by {s['owningProject']}, but the index says {owner}.")
            elif projects.get(owner, {}).get("status") == "deprecated":
                warnings.append(f"Screen {s['id']} is on {owner}, which is deprecated: users shouldn't enter from there.")

    # every core task has a flow, from a real entry point
    if args.brief:
        tasks = {t["id"] for t in load(args.brief).get("coreTasks", [])}
        missing = tasks - {f["taskId"] for f in flow["flows"]}
        if missing:
            errors.append(f"Core task(s) with no flow: {', '.join(sorted(missing))}.")
    for e in flow["entryPoints"]:
        for end in ("from", "to"):
            if e[end] not in screens:
                errors.append(f"Entry point {e['id']} {end} '{e[end]}' isn't a listed screen.")
        if e["to"] in screens and screens[e["to"]]["kind"] != "new":
            errors.append(f"Entry point {e['id']} leads to {e['to']}, which isn't a screen in this design.")
        src = screens.get(e["from"], {})
        if src.get("route") is None and src.get("kind") == "external" and not e.get("carriesState"):
            warnings.append(f"Entry point {e['id']} comes from outside the product and passes no state: say what the link carries, or 'nothing'.")
        if src.get("kind") == "external" and not e.get("whenSignedOut"):
            warnings.append(f"Entry point {e['id']} comes from outside the product but doesn't say what happens when signed out.")

    # integration: entry points on existing pages need a change owned by that page's design
    changes_by_screen = defaultdict(list)
    for ic in flow["integrationChanges"]:
        changes_by_screen[ic["screen"]].append(ic)
        if ic["screen"] not in screens:
            errors.append(f"Integration change {ic['id']} is on '{ic['screen']}', which isn't a listed screen.")
            continue
        s = screens[ic["screen"]]
        if s["kind"] == "existing" and ic["owner"] != surface_owner.get(s.get("surface")):
            errors.append(f"Integration change {ic['id']} is on {s['name']}, owned by {surface_owner.get(s.get('surface'))}, but names '{ic['owner']}' as owner.")
        if ic["status"] == "rejected":
            errors.append(f"Integration change {ic['id']} was rejected by {ic['owner']}: the entry point it supports can't ship. Rework the flow.")
        elif ic["status"] == "proposed":
            warnings.append(f"Integration change {ic['id']} ({ic['change']}) is still proposed: {ic['owner']} has to accept it before this ships.")
    for e in flow["entryPoints"]:
        src = screens.get(e["from"], {})
        if src.get("kind") in ("existing", "external") and not changes_by_screen.get(e["from"]):
            errors.append(f"Entry point {e['id']} starts on {src.get('name')}, but no integration change adds it there. "
                          "The link has to be created by whoever owns that page.")

    # reachability, dead ends, back navigation
    graph = defaultdict(set)
    for e in flow["entryPoints"]:
        graph[e["from"]].add(e["to"])
    for f in flow["flows"]:
        for st in f["steps"]:
            if st["screen"] not in screens:
                errors.append(f"{f['taskId']}: step on unknown screen '{st['screen']}'.")
            if st.get("next"):
                graph[st["screen"]].add(st["next"])
    starts = {e["from"] for e in flow["entryPoints"]}
    seen, todo = set(starts), list(starts)
    while todo:
        for n in graph[todo.pop()]:
            if n not in seen:
                seen.add(n)
                todo.append(n)
    for s in flow["screens"]:
        if s["kind"] == "new" and s["id"] not in seen:
            errors.append(f"Screen {s['id']} ({s['name']}) can't be reached from any entry point.")
    backs = {b["screen"] for b in flow.get("backNavigation", [])}
    outs = {x["from"] for x in flow.get("exits", [])} | set(graph)
    for s in flow["screens"]:
        if s["kind"] == "new":
            if s["id"] not in backs:
                errors.append(f"Screen {s['id']} ({s['name']}) has no way back defined — including when reached by a deep link with no history.")
            if s["id"] not in outs and s["id"] not in backs:
                errors.append(f"Screen {s['id']} ({s['name']}) is a dead end.")

    # each flow: error paths for async steps, done state, click budget
    for f in flow["flows"]:
        if f["entryPoint"] not in entries:
            errors.append(f"{f['taskId']}: entry point '{f['entryPoint']}' isn't listed.")
        kinds = {a["kind"] for a in f["alternatePaths"]}
        if any(st.get("async") for st in f["steps"]) and "error" not in kinds:
            errors.append(f"{f['taskId']}: has an async step but no error path.")
        if not f.get("done"):
            errors.append(f"{f['taskId']}: no 'done' — how does the user know it worked?")
        clicks = sum(1 for st in f["steps"] if st["isClick"])
        if clicks > max_clicks:
            warnings.append(f"{f['taskId']}: {clicks} clicks from its entry point, over the {max_clicks}-click limit. Needs an overLimitReason in taskPaths, or a shorter flow.")
        if screens.get(entries.get(f["entryPoint"], {}).get("from"), {}).get("kind") == "external" and "signed-out" not in kinds:
            warnings.append(f"{f['taskId']}: starts outside the product but has no signed-out path.")

    status = "ERRORS" if errors else "WARNINGS" if warnings else "OK"
    print(f"{flow['id']}: {status}")
    for e in errors:
        print("  ✗", e)
    for w in warnings:
        print("  •", w)
    return 2 if errors else 1 if warnings else 0


if __name__ == "__main__":
    sys.exit(main())

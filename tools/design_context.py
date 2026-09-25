#!/usr/bin/env python3
"""Show the design context for a file: which design owns it and what it decided.

Usage: python3 tools/design_context.py <file> [--index design-index.yaml]
                                               [--manifest design-system-manifest.yaml]

Looks the file up in the design index (projects' codePaths) and prints the
owning design's scope, surfaces, components, decisions (from its design
output), shared patterns with other designs, and any artifacts flagged for
review. Prints nothing for files outside development.uiPaths. Always exits 0:
this informs, it never blocks.
"""
import argparse
import fnmatch
import os
import sys

import yaml


def globmatch(path, pattern):
    """fnmatch where '**/' also matches zero directories (src/**/*.css matches src/a.css)."""
    return fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(path, pattern.replace("**/", ""))


def load(path):
    try:
        with open(path) as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return None


def matches(path, globs):
    return any(globmatch(path, g) for g in globs or [])


def decisions_for(project, base):
    """Decision-log entries from the project's design-output artifact, if its file is available."""
    for a in project.get("artifacts", []):
        if a.get("type") == "design-output" and a.get("path"):
            out = load(os.path.join(base, a["path"])) or load(a["path"])
            if out:
                return out.get("decisionLog", [])
    return []


def describe(project, index, base):
    lines = [f"## Design context: {project['id']} — {project['title']} ({project['status']})",
             project.get("scopeSummary", "")]
    if project["status"] == "deprecated":
        lines.append("**Deprecated design.** Don't extend it; check `relatedProjects` for what replaced it.")
    if project.get("surfaces"):
        lines.append("Surfaces: " + ", ".join(project["surfaces"]))
    if project.get("componentsUsed"):
        lines.append("Components to use here: " + ", ".join(project["componentsUsed"]))
    decisions = decisions_for(project, base)
    if decisions:
        lines.append("Decisions already made (follow them; changing one is a design change):")
        for d in decisions:
            by = f", inherited from {d['inheritedFrom']}" if d.get("inheritedFrom") else ""
            lines.append(f"- {d['decision']}: **{d['chosen']}** ({d.get('mode', '')}{by})")
    for r in project.get("relatedProjects", []):
        if r["relation"] == "shares-pattern":
            lines.append(f"Shares a pattern with {r['projectId']}: {r.get('note', '')} Keep both the same.")
    stale = [a for a in project.get("artifacts", []) if a.get("reviewStatus") == "needs-review"]
    if stale:
        lines.append("Flagged for review — the design may be out of date:")
        lines += [f"- {a['id']}: {a.get('reviewReason', '')}" for a in stale]
    return "\n".join(l for l in lines if l)


def context_for(rel, root, manifest, index):
    """Return (owner_ids, text) for a repo-relative path. owner_ids is empty for unowned
    files; text is '' for files outside development.uiPaths that no design owns."""
    dev = manifest.get("development", {})
    ui_paths = dev.get("uiPaths")
    owners = [p for p in index.get("projects", []) if matches(rel, p.get("codePaths"))]
    if not owners:
        if ui_paths and matches(rel, ui_paths) and dev.get("designContext", {}).get("onUnownedUi", "warn") == "warn":
            return [], (f"## Design context: no design owns `{rel}`\n"
                        "New UI here has no design behind it. Before it ships, run the scope check "
                        "(design-generation Step 2b): it may belong to an existing design, or need a new one.")
        return [], ""
    # most specific owner first: the one whose matching glob is longest
    owners.sort(key=lambda p: -max(len(g) for g in p["codePaths"] if globmatch(rel, g)))
    return [p["id"] for p in owners], "\n\n".join(describe(p, index, root) for p in owners)


def load_project(root, manifest_path, index_path=None):
    manifest = load(os.path.join(root, manifest_path)) or {}
    index_path = index_path or manifest.get("scopePolicy", {}).get("designIndexPath", "design-index.yaml")
    index = load(os.path.join(root, index_path)) or {"projects": []}
    return manifest, index


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--index", default=None, help="default: the manifest's scopePolicy.designIndexPath")
    ap.add_argument("--manifest", default="design-system-manifest.yaml")
    ap.add_argument("--root", default=os.environ.get("CLAUDE_PROJECT_DIR", "."))
    args = ap.parse_args()
    manifest, index = load_project(args.root, args.manifest, args.index)
    rel = os.path.relpath(os.path.abspath(args.file), os.path.abspath(args.root))
    _, text = context_for(rel, args.root, manifest, index)
    if text:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())

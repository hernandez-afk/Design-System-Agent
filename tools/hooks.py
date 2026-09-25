#!/usr/bin/env python3
"""Claude Code hooks that keep design context inside day-to-day development.

Wired up by templates/claude-settings.json. Each subcommand reads the hook's
JSON from stdin.

  session-start  Prints the design system's name and version, every design in
                 the index with the code it owns and any review flags, and a
                 warning if CLAUDE.md's version stamp is stale. Claude Code adds
                 this output to the session's context.
  pre-edit       The first time in a session that Claude edits a file owned by
                 a design, the edit is held once, with that design's context
                 (scope, components, decisions, shared patterns, review flags)
                 as the reason, and Claude retries following it. Later edits to
                 the same design's files go straight through.
  post-edit      Runs the token lint on the edited file (exit 2 = off-token
                 values, sent back to Claude to fix), and reminds once per
                 session when UI is being written that no design owns.

Paths default to the repo root (CLAUDE_PROJECT_DIR): design-system-manifest.yaml,
and the index at the manifest's scopePolicy.designIndexPath.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from design_context import context_for, load_project  # noqa: E402
from token_lint import lint_files  # noqa: E402

ROOT = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
MANIFEST = os.environ.get("DESIGN_MANIFEST", "design-system-manifest.yaml")
SEEN_DIR = os.path.join(ROOT, ".claude", ".design-context-seen")


def read_input():
    try:
        return json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return {}


def edited_path(data):
    ti = data.get("tool_input") or {}
    path = ti.get("file_path") or ti.get("path") or ""
    return os.path.relpath(os.path.abspath(path), os.path.abspath(ROOT)) if path else ""


def seen(session, key):
    """True if this session already got this piece of context; marks it seen otherwise."""
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", f"{session}--{key}")
    marker = os.path.join(SEEN_DIR, safe)
    if os.path.exists(marker):
        return True
    os.makedirs(SEEN_DIR, exist_ok=True)
    open(marker, "w").close()
    return False


def session_start(data):
    manifest, index = load_project(ROOT, MANIFEST)
    if not manifest:
        return 0
    meta = manifest.get("meta", {})
    lines = [f"# Design system: {meta.get('name')} v{meta.get('version')}",
             "Every UI change follows CLAUDE.md and the design that owns the code. "
             "Editing a design's files shows its decisions first; off-token values are sent back to fix."]
    claude_md = os.path.join(ROOT, meta.get("claudeMd", {}).get("path", "CLAUDE.md"))
    stamp = f"<!-- design-system-manifest: {meta.get('name')} v{meta.get('version')} -->"
    try:
        with open(claude_md) as f:
            first = f.readline().strip()
        if first != stamp:
            lines.append(f"**Warning:** CLAUDE.md is out of date (has `{first}`, manifest is v{meta.get('version')}). "
                         "Its tokens may be stale: regenerate it from the manifest before UI work.")
    except FileNotFoundError:
        lines.append("**Warning:** there's no CLAUDE.md with the design system in it. Generate it from the manifest "
                     "(templates/CLAUDE.md) before UI work.")
    projects = index.get("projects", [])
    stages = {}
    try:  # the harness stage per design; the summary still works without it
        from harness import Harness
        idx_path = os.path.join(ROOT, manifest.get("scopePolicy", {}).get("designIndexPath", "design-index.yaml"))
        h = Harness(idx_path, os.path.join(ROOT, MANIFEST), ROOT)
        h.manifest_path = os.path.join(ROOT, MANIFEST)
        stages = {p["id"]: h.stage(h.gates(p), p) for p in projects if p.get("status") != "deprecated"}
    except Exception:
        pass
    if projects:
        lines.append("\n## Designs, their harness stage, and the code they own")
        for p in projects:
            flags = sum(1 for a in p.get("artifacts", []) if a.get("reviewStatus") == "needs-review")
            code = ", ".join(p.get("codePaths", [])) or "no code linked yet"
            note = f" — {flags} artifact(s) need review" if flags else ""
            stage = f", stage: {stages[p['id']]}" if p["id"] in stages else ""
            lines.append(f"- {p['id']} {p['title']} ({p['status']}{stage}): {code}{note}")
        lines.append("Run `python3 .claude/design-agent/tools/harness.py next --project <ID>` for what a design needs next.")
    print("\n".join(lines))
    return 0


def pre_edit(data):
    rel = edited_path(data)
    if not rel:
        return 0
    manifest, index = load_project(ROOT, MANIFEST)
    owners, text = context_for(rel, ROOT, manifest, index)
    if not owners or seen(data.get("session_id", "default"), "design-" + "+".join(owners)):
        return 0
    reason = (f"{text}\n\nThis is the design context for `{rel}`. Read it, then retry the edit following these "
              "decisions and components. If the change you intend contradicts a decision, stop and raise it as a "
              "design change instead of editing.")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                              "permissionDecision": "deny",
                                              "permissionDecisionReason": reason}}))
    return 0


def post_edit(data):
    rel = edited_path(data)
    if not rel:
        return 0
    manifest, index = load_project(ROOT, MANIFEST)
    if not manifest:
        return 0
    messages = []
    mode, report = lint_files([os.path.join(ROOT, rel)], ROOT, manifest)
    if report:
        messages.append(report)
    owners, text = context_for(rel, ROOT, manifest, index)
    if not owners and text and not seen(data.get("session_id", "default"), "unowned-" + os.path.dirname(rel)):
        messages.append(text)
    if not messages:
        return 0
    if report and mode == "warn":
        messages[0] = "Warning (tokenLint mode: warn) — " + messages[0]
    # PostToolUse can't undo the edit; exit 2 sends stderr back to Claude to act on.
    print("\n\n".join(messages), file=sys.stderr)
    return 2


if __name__ == "__main__":
    commands = {"session-start": session_start, "pre-edit": pre_edit, "post-edit": post_edit}
    if len(sys.argv) != 2 or sys.argv[1] not in commands:
        sys.exit(__doc__)
    sys.exit(commands[sys.argv[1]](read_input()))

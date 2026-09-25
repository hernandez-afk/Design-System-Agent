#!/usr/bin/env python3
"""The design harness: where every design is, what's blocking it, and what the
system should learn. See HARNESS.md.

Usage:
  python3 tools/harness.py status [--project ID]   stage, gates and blockers per design
  python3 tools/harness.py next --project ID       the next action, with the command to run
  python3 tools/harness.py learn [--min 2]         recurring findings → proposed system changes
Options: --index design-index.yaml --manifest design-system-manifest.yaml --root .

A design's stage is worked out from its records in the design index, never
typed in: it's the first stage whose gate doesn't pass. A record flagged
needs-review sends the design back to that record's stage, which is how
iteration happens: change anything upstream, and the harness shows exactly
what has to be redone.
"""
import argparse
import os
import subprocess
import sys
from collections import Counter, defaultdict

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
STAGES = ["brief", "scope", "flow", "design", "audit", "approval", "build", "verify"]
STAGE_OF = {"prd": "brief", "page-brief": "brief", "ticket-brief": "brief", "brief-optimization-report": "brief",
            "scope-overlap-report": "scope", "user-flow": "flow", "design-output": "design",
            "component-gap-report": "design", "component-verification-report": "design",
            "audit-report": "audit", "implementation-review": "verify"}
NEXT = {
    "brief": "Optimize the brief (skills/brief-optimization.md, generation Step 1): lint it, answer the open questions, and get the author's approval.",
    "scope": "Run the scope placement check (generation Step 2b) against the design index, and record the human decision.",
    "flow": "Map the user flow (generation Step 2c), then pass: python3 tools/flow_check.py <flow> --index <index> --brief <brief>",
    "design": "Design it (generation Steps 3–10): reuse check, structure, phone-first layout, 3-3-3 walk-through and mobile pass.",
    "audit": "Have the design-critic audit it (generation Step 11). Revise on major issues; a blocker goes to a person.",
    "approval": "Get the human sign-off, with every proposed component verified and every integration change accepted by its owner.",
    "build": "Build it at the design's codePaths. The token lint and design-context hooks keep the code on-system: python3 tools/token_lint.py <files>",
    "verify": "Have the design-critic audit the built UI against the design, its acceptance criteria and the tokens (audit-report mode: implementation).",
}
OK = ("pass", "note")


def load(path):
    try:
        with open(path) as f:
            return yaml.safe_load(f) or {}
    except (FileNotFoundError, TypeError):
        return None


class Harness:
    def __init__(self, index_path, manifest_path, root):
        self.root, self.index_path = root, index_path
        self.index = load(index_path) or {"projects": []}
        self.manifest = load(manifest_path) or {}
        self.projects = {p["id"]: p for p in self.index.get("projects", [])}
        self.flows = {}  # project id -> loaded user flow
        for p in self.projects.values():
            a = self.artifact(p, "user-flow")
            if a and self.read(a):
                self.flows[p["id"]] = (a, self.read(a))

    # -- records -----------------------------------------------------------
    def resolve(self, path):
        for base in (self.root, os.getcwd(), os.path.dirname(os.path.abspath(self.index_path))):
            full = os.path.join(base, path)
            if os.path.exists(full):
                return full
        return None

    def read(self, artifact):
        path = artifact.get("path") or ""
        if not path.endswith((".yaml", ".yml", ".json")):
            return None
        full = self.resolve(path)
        return load(full) if full else None

    @staticmethod
    def artifact(project, kind):
        found = [a for a in project.get("artifacts", []) if a["type"] == kind]
        return max(found, key=lambda a: a.get("version", 1)) if found else None

    # -- gates -------------------------------------------------------------
    def gates(self, p):
        g = {}
        policy = self.manifest.get("briefPolicy", {})
        # brief
        report, brief = self.artifact(p, "brief-optimization-report"), self.artifact(p, "ticket-brief")
        if not brief:
            g["brief"] = ("missing", "no ticket brief on record")
        elif policy.get("requireOptimization", True) and not report:
            g["brief"] = ("missing", "the brief was never optimized (no brief-optimization-report)")
        elif report and self.read(report) is not None:
            r = self.read(report)
            if r.get("readiness") != "ready":
                g["brief"] = ("fail", f"brief readiness is '{r.get('readiness')}': {len(r.get('openQuestions', []))} open question(s)")
            elif policy.get("approvalBeforeGeneration", True) and not r.get("approvedBy"):
                g["brief"] = ("fail", "the optimized brief hasn't been approved by its author")
            else:
                g["brief"] = ("pass", "optimized and approved")
        else:
            g["brief"] = ("pass", "optimized (on record)")
        # scope
        a = self.artifact(p, "scope-overlap-report")
        if not a:
            required = self.manifest.get("scopePolicy", {}).get("requireScopeCheck", True)
            g["scope"] = ("missing", "no scope check on record") if required else ("pass", "scope check not required")
        else:
            r = self.read(a)
            if r and self.manifest.get("scopePolicy", {}).get("onOverlap", "ask") == "ask" \
                    and r.get("recommendation") != "new-project" and not r.get("humanDecision"):
                g["scope"] = ("fail", f"scope recommendation '{r.get('recommendation')}' is waiting for a human decision")
            else:
                g["scope"] = ("pass", "placed")
        # flow
        if p["id"] in self.flows:
            fa, flow = self.flows[p["id"]]
            cmd = [sys.executable, os.path.join(HERE, "flow_check.py"), self.resolve(fa["path"]), "--index", self.index_path]
            if brief and brief.get("path") and self.resolve(brief["path"]):
                cmd += ["--brief", self.resolve(brief["path"])]
            res = subprocess.run(cmd, capture_output=True, text=True)
            lines = [l.strip(" ✗•") for l in res.stdout.splitlines()[1:]]
            g["flow"] = {0: ("pass", "flow checks out"), 1: ("note", "; ".join(lines))}.get(res.returncode, ("fail", "; ".join(lines[:3])))
        elif self.artifact(p, "user-flow"):
            g["flow"] = ("pass", "mapped (on record)")
        else:
            g["flow"] = ("missing", "no user flow on record")
        # design
        a = self.artifact(p, "design-output")
        out = self.read(a) if a else None
        if not a:
            g["design"] = ("missing", "no design output yet")
        elif out is not None:
            lacking = [k for k in ("mobileCheck", "taskPaths", "glanceTest") if not out.get(k)]
            g["design"] = ("fail", "design output is missing " + ", ".join(lacking)) if lacking else ("pass", f"revision {out.get('revisionNumber', 0)}")
        else:
            g["design"] = ("pass", "designed (on record)")
        # audit
        audits = [x for x in p.get("artifacts", []) if x["type"] == "audit-report"]
        if not audits:
            g["audit"] = ("missing", "not audited yet")
        else:
            last = max(audits, key=lambda x: x.get("version", 1))
            r = self.read(last)
            verdict = r.get("overallVerdict") if r else None
            if verdict in (None, "pass", "minor-issues"):
                g["audit"] = ("pass", f"audit {verdict or 'on record'}")
            else:
                g["audit"] = ("fail", f"latest audit verdict is '{verdict}'")
        # approval
        waiting = []
        if p["id"] in self.flows:
            waiting = [f"{ic['id']} to {ic['owner']} ({ic['status']})" for ic in self.flows[p["id"]][1].get("integrationChanges", [])
                       if ic["status"] in ("proposed", "rejected")]
        if waiting:
            g["approval"] = ("fail", "integration changes not accepted: " + ", ".join(waiting))
        elif out is not None and not out.get("signOff") and p.get("status") not in ("approved", "shipped"):
            g["approval"] = ("missing", "no human sign-off on the design output")
        else:
            g["approval"] = ("pass", "signed off" if (out or {}).get("signOff") else f"status: {p.get('status')}")
        # build
        if not p.get("codePaths"):
            g["build"] = ("missing", "no codePaths: the code isn't linked to this design")
        else:
            files = self.code_files(p["codePaths"])
            if not files:
                g["build"] = ("missing", "no code at its codePaths yet")
            else:
                res = subprocess.run([sys.executable, os.path.join(HERE, "token_lint.py"), *files, "--root", self.root,
                                      "--manifest", os.path.relpath(self.manifest_path, self.root)], capture_output=True, text=True)
                n = sum(1 for l in res.stderr.splitlines() + res.stdout.splitlines() if " — " in l)
                g["build"] = ("fail", f"token lint: {n} off-token value(s) in {len(files)} file(s)") if res.returncode == 2 else ("pass", f"{len(files)} file(s), token-clean")
        # verify
        a = self.artifact(p, "implementation-review")
        r = self.read(a) if a else None
        if not a:
            g["verify"] = ("missing", "the built UI hasn't been reviewed against the design")
        elif r and r.get("overallVerdict") not in ("pass", "minor-issues"):
            g["verify"] = ("fail", f"implementation review verdict is '{r.get('overallVerdict')}'")
        else:
            g["verify"] = ("pass", "built as designed")
        # staleness overrides: a flagged record sends the design back to its stage
        for x in p.get("artifacts", []):
            if x.get("reviewStatus") == "needs-review":
                stage = STAGE_OF.get(x["type"])
                if stage and g.get(stage, ("pass",))[0] != "stale":
                    g[stage] = ("stale", f"{x['id']}: {x.get('reviewReason', 'needs review')}")
        return g

    def code_files(self, globs):
        sys.path.insert(0, HERE)
        from design_context import globmatch
        found = []
        for d, _, names in os.walk(self.root):
            if "/." in d or "node_modules" in d:
                continue
            for n in names:
                rel = os.path.relpath(os.path.join(d, n), self.root)
                if any(globmatch(rel, g) for g in globs):
                    found.append(os.path.join(d, n))
        return sorted(found)

    @staticmethod
    def legacy(p):
        """Designs that shipped before the harness: missing early records are gaps to backfill, not blockers."""
        return p.get("status") in ("approved", "shipped")

    def stage(self, gates, p):
        blocking = ("fail", "stale") if self.legacy(p) else ("fail", "stale", "missing")
        return next((s for s in STAGES if gates[s][0] in blocking), "live")

    def incoming(self, pid):
        return [f"{ic['id']} from {other}: {ic['change']} ({ic['status']})"
                for other, (_, flow) in self.flows.items() if other != pid
                for ic in flow.get("integrationChanges", []) if ic["owner"] == pid and ic["status"] in ("proposed",)]


def cmd_status(h, only):
    icon = {"pass": "✓", "note": "✓", "fail": "✗", "missing": "·", "stale": "↺"}
    for pid, p in h.projects.items():
        if only and pid != only:
            continue
        if p.get("status") == "deprecated":
            print(f"{pid} {p['title']}: deprecated (not tracked)\n")
            continue
        g = h.gates(p)
        stage = h.stage(g, p)
        print(f"{pid} {p['title']} — stage: {stage.upper()}  (recorded status: {p.get('status')})")
        for s in STAGES:
            state, detail = g[s]
            if state == "missing" and h.legacy(p):
                detail += " (not on record: backfill when it next changes)"
            print(f"  {icon[state]} {s:9} {detail}")
        for line in h.incoming(pid):
            print(f"  ⇠ waiting on you: {line}")
        print()


def cmd_next(h, pid):
    p = h.projects.get(pid)
    if not p:
        print(f"No design '{pid}' in the index. A new design starts with a page brief: templates/page-brief.md")
        return 1
    g = h.gates(p)
    stage = h.stage(g, p)
    if stage == "live":
        print(f"{pid} is live. Any change to one of its records sends it back through the harness.")
        return 0
    state, detail = g[stage]
    why = {"stale": "needs redoing", "fail": "is blocked", "missing": "hasn't happened"}[state]
    print(f"{pid} — stage {stage.upper()} {why}: {detail}")
    if state == "stale":
        print(f"Next: revise the {stage} for that change, then carry on from there. How: {NEXT[stage]}")
    else:
        print(f"Next: {NEXT[stage]}")
    incoming = h.incoming(pid)
    if incoming:
        print("Also waiting on this design's owner:\n  " + "\n  ".join(incoming))
    return 0


def cmd_learn(h, min_count):
    findings, conflicts, gaps, rewrites = defaultdict(set), defaultdict(set), defaultdict(set), Counter()
    for pid, p in h.projects.items():
        for a in p.get("artifacts", []):
            r = h.read(a) if a.get("path") else None
            if not r:
                continue
            if a["type"] in ("audit-report", "implementation-review"):
                for c in r.get("categories", []):
                    for f in c.get("findings", []):
                        findings[(c["category"], f.get("manifestReference") or f["rubricItem"][:60])].add(pid)
            elif a["type"] == "brief-optimization-report":
                for c in r.get("conflicts", []):
                    conflicts[c["rule"]].add(pid)
                for c in r.get("changes", []):
                    rewrites[c["kind"]] += 1
            elif a["type"] == "component-gap-report":
                for gap in r.get("gaps", []):
                    gaps[gap["suggestedName"]].add(pid)
    proposals = []
    for (cat, ref), ps in sorted(findings.items(), key=lambda kv: -len(kv[1])):
        if len(ps) >= min_count:
            proposals.append(f"Recurring audit finding in {len(ps)} design(s) [{cat}: {ref}] ({', '.join(sorted(ps))}). "
                             "Add a guardrail so it can't recur: a token, a baseline component, a CLAUDE.md rule, or a lint check.")
    for rule, ps in conflicts.items():
        if len(ps) >= min_count:
            proposals.append(f"Briefs keep conflicting with {rule} ({', '.join(sorted(ps))}). Explain it in the page-brief template or CLAUDE.md.")
    for name, ps in gaps.items():
        if len(ps) >= min_count:
            proposals.append(f"'{name}' was requested as a new component by {len(ps)} design(s) ({', '.join(sorted(ps))}). Consider a baseline component.")
    for kind, n in rewrites.items():
        if n >= max(min_count, 2) and kind in ("vague-term", "solution-to-need"):
            proposals.append(f"{n} brief rewrites of kind '{kind}'. Add your team's recurring terms to briefPolicy.vocabulary.")
    print("Proposed system changes:" if proposals else f"No recurring patterns yet (looking for {min_count}+ occurrences).")
    for pr in proposals:
        print("  •", pr)
    print("\nEach is a proposal: a person accepts it, then the manifest's version is bumped and CLAUDE.md is regenerated.")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["status", "next", "learn"])
    ap.add_argument("--project")
    ap.add_argument("--min", type=int, default=2)
    ap.add_argument("--index", default="design-index.yaml")
    ap.add_argument("--manifest", default="design-system-manifest.yaml")
    ap.add_argument("--root", default=os.environ.get("CLAUDE_PROJECT_DIR", "."))
    args = ap.parse_args()
    h = Harness(args.index, args.manifest, args.root)
    h.manifest_path = args.manifest
    if args.command == "status":
        cmd_status(h, args.project)
        return 0
    if args.command == "next":
        if not args.project:
            sys.exit("next needs --project")
        return cmd_next(h, args.project)
    return cmd_learn(h, args.min)


if __name__ == "__main__":
    sys.exit(main())

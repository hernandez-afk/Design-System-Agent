#!/usr/bin/env python3
"""The design harness: where every design is, what's blocking it, and what the
system should learn. See HARNESS.md.

Usage:
  python3 tools/harness.py status [--project ID]   stage, gates and blockers per design
  python3 tools/harness.py next --project ID       the next action, with the command to run
  python3 tools/harness.py check --project ID [--page page.html]
                                                   every mechanical check in one call; prints only failures
  python3 tools/harness.py new <ticket-brief|user-flow|design-output|critique>
                                                   a minimal skeleton to fill in (no need to read schemas)
  python3 tools/harness.py record --project ID --type TYPE --path PATH [--title T] [--depends ID:VER,…]
                                                   register or bump a record in the design index
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
    "brief": "Optimize the brief (skills/design-agent/reference/brief-optimization.md, generation Step 1): lint it, answer the open questions, and get the author's approval.",
    "scope": "Run the scope placement check (generation Step 2b) against the design index, and record the human decision.",
    "flow": "Map the user flow (generation Step 2c), then pass: python3 tools/flow_check.py <flow> --index <index> --brief <brief>",
    "design": "Design it (generation Steps 3–10): reuse check, structure, phone-first layout, 3-3-3 walk-through and mobile pass.",
    "audit": "Have the design-critic audit it (generation Step 11). Revise on major issues; a blocker goes to a person.",
    "approval": "Get the human sign-off, with every proposed component verified and every integration change accepted by its owner.",
    "build": "Build it at the design's codePaths. The token lint and design-context hooks keep the code on-system: python3 tools/token_lint.py <files>",
    "verify": "Have the design-critic audit the built UI against the design, its acceptance criteria and the tokens (audit-report mode: implementation).",
}
OK = ("pass", "note")
SKELETONS = {
    "ticket-brief": """ticketKey: ""            # e.g. DES-600
approvedBy: ""           # set once the author approves (after their questions are answered)
title: ""
purpose: ""              # one sentence: what's true once the user leaves this page
pageJustification: ""    # only if it has no task, or is small and reached from one place: why it's a page
sourceType: "page-brief"
scopeTerms: []           # specific nouns: ["hackathon", "vote"]
surfaces: []             # ["hackathon/vote"]
connections: { arrivesFrom: [], goesNext: [], mustLinkHere: [] }
priorities:              # ranked; P1 decides the one primary action
  - { id: "P1", statement: "", source: "explicit" }
coreTasks:
  - { id: "T1", statement: "", linkedPriority: "P1", entryPoint: "" }
requiredElements:
  - { description: "", targetCategory: "display", linkedPriority: "P1", infoType: "", form: "", states: [] }
    # infoType: single-value comparison trend part-to-whole status sequence list records explanation reference
    #           choice-few choice-many toggle action input   (form: what it's shown as; purpose_check suggests)
acceptanceCriteria:      # testable: who, action, measurable result
  - { id: "AC1", statement: "", source: "explicit" }
entities:                # handledBy: this-project | existing-design | new-brief | out-of-scope | question (+ ref)
  - name: ""
    operations: { create: { handledBy: "", ref: "" }, source: { handledBy: "", ref: "" } }
edgeCases:               # one line per lens; not-applicable needs a reason in action
  # lenses: roles setup time concurrency integrity scale failure ending communication privacy access
  - { id: "EC1", lens: "roles", case: "", disposition: "", action: "" }
outOfScope: []
openQuestions: []
""",
    "user-flow": """id: ""                   # DES-xxx-flow-1
projectId: ""
briefRef: ""
screens:                 # kind: new | existing (needs surface + owningProject) | system | external
  - { id: "S1", name: "", kind: "new", surface: "" }
entryPoints:
  - { id: "E1", from: "", to: "S1", trigger: "", carriesState: "", whenSignedOut: "" }
flows:                   # one per core task; every async step needs an error path
  - taskId: "T1"
    entryPoint: "E1"
    steps: [ { screen: "S1", action: "", isClick: true, async: false } ]
    done: ""
    alternatePaths: [ { kind: "error", when: "", then: "" } ]
backNavigation: [ { screen: "S1", back: "", to: "" } ]
exits: []
integrationChanges: []   # changes to other designs' pages: { id, screen, change, owner, status: proposed }
""",
    "design-output": """ticket: ""
projectId: ""
manifestVersion: ""
artifact: { format: "html", location: "" }
screenshotSetRef: ""     # from `harness.py check --page`: replaces a hand-written mobileCheck
userFlowRef: ""
componentsUsed: [ { name: "", variant: "", status: "approved" } ]
decisionLog: []          # only decisions a person made or should know about
acceptanceResults: [ { criterionId: "AC1", met: true, evidence: "" } ]
taskPaths: [ { taskId: "T1", steps: [ { action: "", isClick: true } ], clickCount: 1, estimatedSeconds: 0, estimateBasis: "" } ]
glanceTest: [ { screen: "", breakpoint: "sm", purposeVisible: true, primaryActionVisible: true, pass: true } ]
""",
    "critique": """verdict: ""              # pass | minor-issues | major-issues | blocker
toolSummary: ""          # path to the `harness.py check` output; not copied here
findings:                # only failures; format: where: what -> fix (rule)
  - { severity: "", where: "", what: "", fix: "", rule: "" }
""",
}



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
        lite = (self.manifest.get("harness", {}) or {}).get("mode", "lite") == "lite"
        brief_doc = self.read(brief) if brief else None
        if not brief:
            g["brief"] = ("missing", "no ticket brief on record")
        elif lite and not report and brief_doc is not None:
            # lite: no separate report; the brief carries its open questions and the author's approval
            q = brief_doc.get("openQuestions") or []
            if q:
                g["brief"] = ("fail", f"{len(q)} open question(s) for the author")
            elif policy.get("approvalBeforeGeneration", True) and not brief_doc.get("approvedBy"):
                g["brief"] = ("fail", "the author hasn't approved the brief (set approvedBy)")
            else:
                g["brief"] = ("pass", f"approved by {brief_doc.get('approvedBy')}")
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
        if g["brief"][0] == "pass" and policy.get("requireEdgeCaseSweep", True) and brief and brief.get("path") \
                and brief["path"].endswith((".yaml", ".yml")) and self.resolve(brief["path"]):
            res = subprocess.run([sys.executable, os.path.join(HERE, "edge_case_check.py"), self.resolve(brief["path"]),
                                  "--index", self.index_path], capture_output=True, text=True)
            out_lines = res.stdout.splitlines()
            new = [l.strip()[2:].split("  (from")[0] for l in out_lines if l.strip().startswith("+ ")]
            extra = f"; new briefs needed: {', '.join(new)}" if new else ""
            if res.returncode == 2:
                first = next((l.strip()[2:] for l in out_lines if l.strip().startswith("✗")), "")
                g["brief"] = ("fail", f"edge-case sweep incomplete: {first}{extra}")
            elif res.returncode == 1:
                n = sum(1 for l in out_lines if l.strip().startswith("?"))
                g["brief"] = ("fail", f"edge-case sweep has {n} open question(s){extra}")
            elif new:
                g["brief"] = ("note", f"optimized; edge-case sweep complete{extra}")
        if g["brief"][0] in OK and brief and brief.get("path") and brief["path"].endswith((".yaml", ".yml")) \
                and self.resolve(brief["path"]):
            res = subprocess.run([sys.executable, os.path.join(HERE, "purpose_check.py"), self.resolve(brief["path"])],
                                 capture_output=True, text=True)
            if res.returncode == 2:
                first = next((l.strip()[2:] for l in res.stdout.splitlines() if l.strip().startswith("✗")), "")
                n = sum(1 for l in res.stdout.splitlines() if l.strip().startswith("✗"))
                g["brief"] = ("fail", f"purpose check: {first}" + (f" (+{n - 1} more: purpose_check.py)" if n > 1 else ""))
        # scope
        a = self.artifact(p, "scope-overlap-report")
        if not a and lite and brief and brief.get("path") and self.resolve(brief["path"]):
            # lite: the scope tool decides; a record is only needed when there's an overlap to settle
            res = subprocess.run([sys.executable, os.path.join(HERE, "scope_check.py"), self.resolve(brief["path"]),
                                  "--index", self.index_path, "--manifest", self.manifest_path], capture_output=True, text=True)
            out_lines = [l.strip() for l in res.stdout.splitlines()]
            if res.returncode == 0:
                g["scope"] = ("pass", "new work: no other design owns it (scope_check)")
            else:
                g["scope"] = ("fail", "overlaps to decide with the author: " + "; ".join(out_lines[1:3])
                              + " — record the decision as a scope-overlap-report")
        elif not a:
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
            verdict = (r.get("overallVerdict") or r.get("verdict")) if r else None
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
        elif not self.legacy(p) and not (out or {}).get("signOff"):
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
                cons = subprocess.run([sys.executable, os.path.join(HERE, "consistency_check.py"), *files, "--root", self.root,
                                       "--manifest", os.path.relpath(self.manifest_path, self.root)], capture_output=True, text=True)
                c = sum(1 for l in cons.stdout.splitlines() if l.strip().startswith("•"))
                problems = ([f"token lint: {n} off-token value(s)"] if res.returncode == 2 else []) + \
                           ([f"consistency: {c} finding(s)"] if cons.returncode == 2 else [])
                g["build"] = ("fail", f"{'; '.join(problems)} in {len(files)} file(s)") if problems else ("pass", f"{len(files)} file(s), token-clean and consistent")
        # verify
        a = self.artifact(p, "implementation-review")
        r = self.read(a) if a else None
        if not a:
            g["verify"] = ("missing", "the built UI hasn't been reviewed against the design")
        elif r and (r.get("overallVerdict") or r.get("verdict")) not in ("pass", "minor-issues"):
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


def cmd_check(h, pid, page, out):
    """Every mechanical check for one design, in one call. Prints failures only, so the model
    reads a few lines instead of each tool's full output."""
    p = h.projects.get(pid)
    lines = []
    if p:
        g = h.gates(p)
        stage = h.stage(g, p)
        lines.append(f"{pid} — stage {stage.upper()}")
        for s in STAGES:
            state, detail = g[s]
            if state in ("fail", "stale") or (state == "missing" and not h.legacy(p) and STAGES.index(s) <= STAGES.index(stage)):
                lines.append(f"  {s}: {detail[:220]}")
    else:
        lines.append(f"{pid}: not in the design index yet (use `record`)")
    if page:
        out = out or os.path.join(h.root, ".design-agent", "shots", pid or "page")
        brands = [a for b in ((p or {}).get("brandGuidelines") or []) for a in ("--brand", b)]
        res = subprocess.run([sys.executable, os.path.join(HERE, "screenshots.py"), page, "--out", out,
                              "--manifest", h.manifest_path, "--id", f"{pid}-shots", *brands], capture_output=True, text=True)
        record = load(os.path.join(out, "screenshot-set.yaml")) or {}
        groups = {}
        for f in record.get("findings", []):  # one line per problem, not per width or element
            groups.setdefault((f["severity"], f["rubricItem"]), []).append(f["description"])
        order = {"blocker": 0, "major": 1, "minor": 2}
        if record.get("designSystem", "").find("reference") >= 0:
            lines.append(f"  checked against: {record['designSystem']}")
        lines.append(f"  page: {sum(len(v) for v in groups.values())} finding(s) in {len(groups)} problem(s); "
                     f"screenshots in {os.path.relpath(out)}")
        for (sev, item), descs in sorted(groups.items(), key=lambda kv: order[kv[0][0]]):
            more = f" (+{len(descs) - 1} similar)" if len(descs) > 1 else ""
            lines.append(f"    [{sev}] {item}: {descs[0][:150]}{more}")
    ok = len(lines) == 1 or (len(lines) == 2 and lines[1].startswith("  page: 0 "))
    print("\n".join(lines + (["  all checks pass"] if ok else [])))
    return 0 if ok else 2


def cmd_new(kind):
    if kind not in SKELETONS:
        sys.exit(f"Unknown skeleton '{kind}'. Choose: {', '.join(SKELETONS)}")
    print(SKELETONS[kind], end="")
    return 0


def cmd_record(h, pid, kind, path, title, depends):
    """Register or bump a record, so the model doesn't hand-edit the index. Rewrites the index
    file (YAML comments aren't kept)."""
    if kind not in STAGE_OF and kind != "page-brief":
        sys.exit(f"Unknown type '{kind}'.")
    index = h.index
    p = h.projects.get(pid)
    if not p:
        p = {"id": pid, "title": title or pid, "status": "in-progress", "scopeSummary": "", "scopeTerms": [],
             "surfaces": [], "artifacts": []}
        index.setdefault("projects", []).append(p)
    art_id = f"{pid}-{kind}" if kind != "ticket-brief" else pid
    existing = next((a for a in p["artifacts"] if a["id"] == art_id), None)
    deps = []
    for d in (depends or "").split(","):
        if d.strip():
            ref, _, ver = d.strip().partition(":")
            deps.append({"artifactId": ref, "version": int(ver or 1)})
    if existing:
        existing["version"] = existing.get("version", 1) + 1
        existing["path"], existing["reviewStatus"] = path, "current"
        existing.pop("reviewReason", None)
        if deps:
            existing["dependsOn"] = deps
        # flag direct dependents built on the old version (change propagation)
        for a in p["artifacts"]:
            for d in a.get("dependsOn", []):
                if d["artifactId"] == art_id and d["version"] < existing["version"]:
                    a["reviewStatus"], a["reviewReason"] = "needs-review", f"{art_id} v{d['version']} → v{existing['version']}"
        v = existing["version"]
    else:
        entry = {"id": art_id, "type": kind, "path": path, "version": 1, "reviewStatus": "current"}
        if deps:
            entry["dependsOn"] = deps
        p["artifacts"].append(entry)
        v = 1
    with open(h.index_path, "w") as f:
        yaml.safe_dump(index, f, sort_keys=False, allow_unicode=True)
    flagged = [a["id"] for a in p["artifacts"] if a.get("reviewStatus") == "needs-review"]
    print(f"{art_id} v{v} recorded on {pid}" + (f"; needs review: {', '.join(flagged)}" if flagged else ""))
    return 0


def cmd_learn(h, min_count):
    findings, conflicts, gaps, rewrites = defaultdict(set), defaultdict(set), defaultdict(set), Counter()
    late = []  # found only after build: the edge cases the sweep should have asked about
    for pid, p in h.projects.items():
        for a in p.get("artifacts", []):
            r = h.read(a) if a.get("path") else None
            if not r:
                continue
            if a["type"] in ("audit-report", "implementation-review"):
                for f in r.get("findings", []):  # the compact critique format
                    findings[("critique", f.get("rule") or f.get("what", "")[:60])].add(pid)
                    if a["type"] == "implementation-review":
                        late.append((pid, f.get("what", "")))
                for c in r.get("categories", []):
                    for f in c.get("findings", []):
                        findings[(c["category"], f.get("manifestReference") or f["rubricItem"][:60])].add(pid)
                        if a["type"] == "implementation-review" or r.get("mode") == "implementation":
                            late.append((pid, f.get("description", f["rubricItem"])))
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
    for pid, desc in late:  # every late finding counts, even once: it's what the sweep missed
        proposals.append(f"Found only after build in {pid}: \"{desc.strip()[:120].rstrip('.')}\". Add a lens question "
                         "(briefPolicy.edgeCaseLenses) or a page-brief prompt, so the edge-case sweep asks it next time.")
    print("Proposed system changes:" if proposals else f"No recurring patterns yet (looking for {min_count}+ occurrences).")
    for pr in proposals:
        print("  •", pr)
    print("\nEach is a proposal: a person accepts it, then the manifest's version is bumped and CLAUDE.md is regenerated.")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["status", "next", "check", "new", "record", "learn"])
    ap.add_argument("kind", nargs="?", help="for new: the skeleton")
    ap.add_argument("--project")
    ap.add_argument("--page")
    ap.add_argument("--out")
    ap.add_argument("--type")
    ap.add_argument("--path")
    ap.add_argument("--title")
    ap.add_argument("--depends")
    ap.add_argument("--min", type=int, default=2)
    ap.add_argument("--index", default="design-index.yaml")
    ap.add_argument("--manifest", default="design-system-manifest.yaml")
    ap.add_argument("--root", default=os.environ.get("CLAUDE_PROJECT_DIR", "."))
    args = ap.parse_args()
    if args.command == "new":
        return cmd_new(args.kind)
    h = Harness(args.index, args.manifest, args.root)
    h.manifest_path = args.manifest
    if args.command == "status":
        cmd_status(h, args.project)
        return 0
    if args.command == "next":
        if not args.project:
            sys.exit("next needs --project")
        return cmd_next(h, args.project)
    if args.command == "check":
        if not args.project:
            sys.exit("check needs --project")
        return cmd_check(h, args.project, args.page, args.out)
    if args.command == "record":
        if not (args.project and args.type and args.path):
            sys.exit("record needs --project, --type and --path")
        return cmd_record(h, args.project, args.type, args.path, args.title, args.depends)
    return cmd_learn(h, args.min)


if __name__ == "__main__":
    sys.exit(main())

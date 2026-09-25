#!/usr/bin/env python3
"""Check a page brief (templates/page-brief.md) is ready for brief optimization.

Usage: python3 tools/brief_lint.py <page-brief.md> [--manifest design-system-manifest.yaml]

Finds the mechanical problems that make designs go wrong: missing sections,
leftover template placeholders, vague words (with what they mean in the design
system), solution-first wording, lists with no amounts, missing states, and
acceptance criteria that can't be checked. The judgment calls (ranking,
conflicts with the design system, rewrites) are skills/brief-optimization.md.

Result: READY (exit 0), NEEDS WORK (exit 1), or NOT READY (exit 2).
"""
import argparse
import os
import re
import sys

REQUIRED = ["Purpose", "Goals (ranked)", "What users need to do", "Content and data", "Acceptance criteria"]
RECOMMENDED = ["Users and context", "States", "Out of scope", "Related pages and designs"]

VAGUE = {
    "pop": "hierarchy: the one primary action, accents.primary contrast",
    "stand out": "hierarchy: the one primary action",
    "eye-catching": "hierarchy: the one primary action",
    "clean": "simplicity + whitespace: minimum elements, roomier spacing",
    "minimal": "simplicity + whitespace",
    "simple": "simplicity, or 3-3-3 — say which outcome",
    "intuitive": "3-3-3: understood in 3 s, reached in 3 clicks, done in 3 min",
    "easy": "3-3-3 — give the measurable version",
    "user-friendly": "3-3-3 — give the measurable version",
    "fast": "3-3-3 time limit + a loading state",
    "quick": "3-3-3 time limit",
    "modern": "no rule — say what outcome it should produce",
    "sleek": "no rule — say what outcome it should produce",
    "fresh": "no rule — say what outcome it should produce",
    "premium": "no rule — say what outcome it should produce",
    "nice": "no rule — say what outcome it should produce",
    "on-brand": "accents.primary / secondary per color.usagePolicy",
    "etc": "unbounded — list everything, or give a count",
    "and so on": "unbounded — list everything, or give a count",
    "various": "unbounded — list them, or give a count",
}
SOLUTIONS = ["dropdown", "drop-down", "modal", "popup", "pop-up", "carousel", "slider", "accordion", "checkbox",
             "radio button", "toggle", "switch", "tab", "tabs", "button", "hamburger", "sidebar", "tooltip"]
VOLUME_NOUNS = r"\b(list|table|rows|items|entries|results|cards|feed)\b"
TESTABLE = re.compile(r"\d|\b(can|must|cannot|within|at most|at least|or fewer|or more|given|when|then|shows?|sees?)\b", re.I)
STATES = ["loading", "empty", "error", "success"]


def sections(text):
    out, current = {}, None
    for line in text.splitlines():
        h = re.match(r"^##\s+(.+?)\s*$", line)
        if h:
            current = h.group(1)
            out[current] = []
        elif current is not None:
            out[current].append(line)
    return {k: "\n".join(v) for k, v in out.items()}


def strip_comments(text):
    return re.sub(r"<!--.*?-->", "", text, flags=re.S)


def items(body):
    return [l.strip()[2:].strip() if l.strip().startswith("- ") else re.sub(r"^\d+\.\s*", "", l.strip())
            for l in body.splitlines() if re.match(r"^\s*(- |\d+\.\s)", l)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("brief")
    ap.add_argument("--manifest", default=None, help="adds briefPolicy.vocabulary terms to the vague-word map")
    args = ap.parse_args()
    raw = open(args.brief, encoding="utf-8").read()
    text = strip_comments(raw)
    vocab = dict(VAGUE)
    if args.manifest and os.path.exists(args.manifest):
        import yaml
        vocab.update((yaml.safe_load(open(args.manifest)) or {}).get("briefPolicy", {}).get("vocabulary", {}) or {})
    errors, warnings = [], []
    sec = sections(text)

    for name in REQUIRED:
        if name not in sec or not sec[name].strip():
            errors.append(f"Missing or empty section: '{name}'.")
    for name in RECOMMENDED:
        if name not in sec or not sec[name].strip():
            warnings.append(f"Section '{name}' is missing or empty.")
    placeholders = re.findall(r"\[[^\]\n]{3,}\]", text)
    if placeholders:
        shown = [p if len(p) <= 40 else p[:37] + "…]" for p in sorted(set(placeholders))]
        errors.append(f"{len(set(placeholders))} template placeholder(s) still in the brief: {', '.join(shown[:4])}{' …' if len(shown) > 4 else ''}")

    goals = items(sec.get("Goals (ranked)", ""))
    if len(goals) > 5:
        warnings.append(f"{len(goals)} goals: more than 5 usually means the page is doing too much. Consider splitting it.")

    for task in items(sec.get("What users need to do", "")):
        if "starts from" not in task.lower():
            warnings.append(f"Task has no starting point ('— starts from: …'): \"{task}\"")

    for name, body in sec.items():
        for n, line in enumerate(body.splitlines(), 1):
            low = line.lower()
            for word, meaning in vocab.items():
                if re.search(rf"(?<![\w-]){re.escape(word)}(?![\w-])", low):
                    warnings.append(f"[{name}] vague: \"{word}\" → {meaning}")
            if name in ("Goals (ranked)", "What users need to do", "Acceptance criteria", "Purpose"):
                for s in SOLUTIONS:
                    if re.search(rf"\b{re.escape(s)}s?\b", low):
                        warnings.append(f"[{name}] solution-first: \"{s}\" — describe the need, and let the reuse check pick the component.")
                        break

    for line in items(sec.get("Content and data", "")):
        if re.search(VOLUME_NOUNS, line, re.I) and not re.search(r"\d", line):
            warnings.append(f"[Content and data] no amount: \"{line}\" — give a count or range (pagination starts above listPaginationThreshold).")

    states_text = sec.get("States", "").lower()
    def described(state):
        m = re.search(rf"\*\*{state}:\*\*[ \t]*(.*)", states_text)
        if m:  # the template's "**Loading:** …" line: described if something real follows it
            return bool(m.group(1).strip()) and not m.group(1).strip().startswith("[")
        return state in states_text
    missing_states = [s for s in STATES if not described(s)]
    if missing_states:
        warnings.append(f"States not described: {', '.join(missing_states)}.")

    criteria = items(sec.get("Acceptance criteria", ""))
    for c in criteria:
        if not TESTABLE.search(c):
            warnings.append(f"[Acceptance criteria] not testable: \"{c}\" — add who, what, and a measurable result.")

    level = "NOT READY" if errors else "NEEDS WORK" if warnings else "READY"
    print(f"{os.path.basename(args.brief)}: {level}")
    for e in errors:
        print("  ✗", e)
    for w in warnings:
        print("  •", w)
    return 2 if errors else 1 if warnings else 0


if __name__ == "__main__":
    sys.exit(main())

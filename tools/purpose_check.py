#!/usr/bin/env python3
"""Does this page earn being a page, and is every piece of it shown the right way?

Usage: python3 tools/purpose_check.py <ticket-brief.yaml>

Checks a ticket brief before anything is designed:
  - it states the page's purpose: what's true once the user leaves
  - the page has a job only a page can do. A page with no core task, only
    information, is usually better as a section of the page it's reached
    from, a panel, a tooltip or a notification. Keep it a page only with a
    pageJustification (people come back to it on its own, it's linked to).
  - every required element serves a ranked priority. One that doesn't is cut,
    or moved to where it's used.
  - each element's information is shown in a form that fits it (its infoType
    and form): numbers as numbers, change over time as a line, steps as a
    stepper, status as a badge. A mismatch comes with the forms that fit.
Exit 0 = pass, 1 = suggestions only, 2 = failures.
"""
import argparse
import sys

import yaml

# infoType → (forms that fit, forms that don't, why). Also reference/content-forms.md.
FORMS = {
    "single-value": (["stat", "key-value", "badge"], ["table", "chart-line", "chart-bar", "paragraph"],
                     "one number is read at a glance as a number"),
    "comparison": (["chart-bar", "table"], ["paragraph", "card-grid"], "differences between items are seen side by side"),
    "trend": (["chart-line", "sparkline"], ["table", "paragraph", "stat"], "change over time is a shape, not a list of values"),
    "part-to-whole": (["chart-bar", "stat"], ["paragraph", "table"], "a share reads as a proportion"),
    "status": (["badge", "inline-alert"], ["paragraph", "card-grid"], "a state is one word and an icon, not a sentence"),
    "sequence": (["stepper", "numbered-list", "timeline"], ["paragraph", "card-grid"], "steps are followed in order"),
    "list": (["list", "table"], ["paragraph"], "items are scanned, not read"),
    "records": (["table", "list"], ["card-grid", "paragraph"], "many items with the same fields compare in columns"),
    "explanation": (["helper-text", "tooltip", "disclosure", "link"], ["paragraph", "card-grid"],
                    "the interface should explain itself; the rest waits until asked for"),
    "reference": (["disclosure", "link", "secondary-page"], ["paragraph", "card-grid"], "rarely needed, so out of the way"),
    "choice-few": (["radio-group", "segmented-control"], ["select", "paragraph"], "up to 5 options are compared visibly"),
    "choice-many": (["select", "combobox"], ["radio-group", "segmented-control"], "many options would crowd the screen"),
    "toggle": (["switch", "checkbox"], ["select", "radio-group"], "on or off is one control"),
    "action": (["button", "link"], ["paragraph"], "an action is a control, not a sentence about one"),
    "input": (["form-field"], ["paragraph"], "people type into a field"),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("brief")
    args = ap.parse_args()
    b = yaml.safe_load(open(args.brief)) or {}
    fails, notes = [], []
    key = b.get("ticketKey", "brief")

    if not (b.get("purpose") or "").strip():
        fails.append("No purpose: say in one sentence what's true once the user leaves this page.")

    tasks = [t for t in b.get("coreTasks", []) or [] if (t.get("statement") or "").strip()]
    elements = b.get("requiredElements", []) or []
    doing = [e for e in elements if e.get("targetCategory") in ("action", "input")]
    arrives = (b.get("connections", {}) or {}).get("arrivesFrom", []) or []
    where = f"'{arrives[0]}'" if arrives else "the page it's reached from"
    if not b.get("pageJustification"):
        if not tasks and not doing:
            fails.append(f"Information only, with no task: this is probably not a page. Better as a section of {where}, "
                         "a panel or drawer, a tooltip, or a notification. Keep it a page only with a pageJustification "
                         "(people come back to it on its own, or other pages link to it).")
        elif len(elements) <= 2 and len(tasks) <= 1 and len(arrives) == 1:
            notes.append(f"Small, and reached from one place: it may fit inside {where} as a section, dialog or drawer, "
                         "saving the trip. Keep it a page with a pageJustification.")

    ranked = {p.get("id") for p in b.get("priorities", []) or []}
    for e in elements:
        what = (e.get("description") or "an element")[:70]
        if not e.get("linkedPriority") or e["linkedPriority"] not in ranked:
            fails.append(f"'{what}' serves no ranked priority: cut it, or move it to the page where it's used.")
        t, form = e.get("infoType"), e.get("form")
        if t and t in FORMS:
            good, bad, why = FORMS[t]
            if not form:
                notes.append(f"'{what}' ({t}): show it as {' or '.join(good)}.")
            elif form in bad or form not in good:
                sev = fails if form in bad else notes
                sev.append(f"'{what}' is {t} information shown as {form}: show it as {' or '.join(good)} ({why}).")
        elif t:
            notes.append(f"'{what}': unknown infoType '{t}' (one of {', '.join(FORMS)}).")

    print(f"{key} purpose: " + ("fails" if fails else "suggestions" if notes else "pass"))
    for f in fails:
        print("  ✗", f)
    for n in notes:
        print("  ·", n)
    return 2 if fails else 1 if notes else 0


if __name__ == "__main__":
    sys.exit(main())

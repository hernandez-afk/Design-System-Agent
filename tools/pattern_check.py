#!/usr/bin/env python3
"""Recognize what kind of page a brief describes, and what that kind of page implies.

Usage: python3 tools/pattern_check.py <ticket-brief.yaml>

A "build a questionnaire" page is a builder. A builder implies more than its brief
usually says: whose it is (one per what?), adding, editing in place, reordering,
duplicating, deleting with undo, previewing, saving and publishing, and what happens
to answers already collected when it changes. Each pattern below lists what it
implies. The brief names its pattern (pagePattern) and decides each implied
capability in patternDecisions: in-scope, out-of-scope, new-brief (another page's job),
or question.

With no pagePattern, the brief's words suggest one. Capabilities the brief already
mentions are pre-marked as likely in scope. Prints a patternDecisions block to paste.
Exit 0 = pass, 1 = suggestions, 2 = undecided capabilities. Patterns and their
layouts: skills/design-agent/reference/page-patterns.md.
"""
import argparse
import re
import sys

import yaml

# pattern → (words that suggest it, {capability: (what to decide, words that show the brief covers it)})
PATTERNS = {
    "builder": (r"\b(build|builder|create (?:a|your|their)|editor|compose|composer|questionnaire|survey|quiz|form builder|template|designer)\b", {
        "ownership": ("Whose is it: one per what (each edition, event, team, user)? Who can edit it?", r"\b(each|per|own|their own|belongs)\b"),
        "add-items": ("Add an item (question, field, block), at the end or between two", r"\badd\b"),
        "edit-in-place": ("Edit an item where it is, not on another screen", r"\bedit|inline|in place\b"),
        "reorder": ("Reorder items: drag, plus move up / move down for keyboard and touch (WCAG 2.5.7)", r"\b(reorder|re-order|drag|move|rearrange|order)\b"),
        "duplicate": ("Duplicate an item", r"\b(duplicate|copy|clone)\b"),
        "delete-undo": ("Delete an item, with undo", r"\b(delete|remove|undo)\b"),
        "item-types": ("Which item types (short answer, choice, scale…), and changing an item's type", r"\b(type|types|multiple choice|short answer|scale|checkbox)\b"),
        "required": ("Mark an item required or optional", r"\b(required|optional|mandatory)\b"),
        "preview": ("Preview it as the person answering will see it, on a phone", r"\b(preview|as (?:a )?respondent)\b"),
        "save-publish": ("Autosave, draft vs published, and when respondents see changes", r"\b(save|autosave|draft|publish)\b"),
        "after-responses": ("Editing after answers are collected: what happens to existing answers", r"\b(responses|answers) (?:already|exist|collected)|after (?:responses|answers)\b"),
        "start-from": ("Start from blank, a template, or a copy of a previous one", r"\b(template|copy of|previous|from scratch|blank)\b"),
        "empty-state": ("The empty builder: the first item one tap away", r"\b(empty|first question|no questions)\b"),
        "limits": ("Limits: how many items, how long a text", r"\b(limit|maximum|max|up to)\b"),
    }),
    "voting": (r"\b(vote|voting|poll|ballot|rank)\b", {
        "eligibility": ("Who can vote, and how it's checked", r"\b(who can|eligib|attendee|sign in)\b"),
        "vote-limits": ("How many votes per person", r"\b(\d+ votes|one person|per person|limit)\b"),
        "change-vote": ("Changing or withdrawing a vote", r"\b(change|withdraw|undo)\b"),
        "closing": ("When voting opens and closes, and what voters see after", r"\b(close|closes|closing|deadline|opens)\b"),
        "results": ("Who sees results, and when", r"\b(results|winner|leaderboard)\b"),
    }),
    "wizard": (r"\b(onboarding|sign ?up|checkout|setup|step[- ]by[- ]step|application|wizard)\b", {
        "progress": ("Where you are: step n of m", r"\b(progress|step \d|of \d)\b"),
        "back-keeps-data": ("Going back keeps what was entered", r"\bback\b"),
        "resume": ("Leaving and coming back later", r"\b(resume|save and|later)\b"),
        "validation": ("Errors shown at each step, not at the end", r"\b(error|valid)\b"),
        "review": ("Review everything before submitting", r"\b(review|summary|confirm)\b"),
    }),
    "list": (r"\b(browse|list|directory|catalog|catalogue|library|search results)\b", {
        "find": ("Search or filter, once there are more than a screenful", r"\b(search|filter)\b"),
        "sort": ("Sort order, and the default", r"\bsort\b"),
        "scale": ("Many items: pagination or loading more", r"\b(paginat|load more|\d+ (?:items|games|rows))\b"),
        "empty": ("No items yet, and no results", r"\b(empty|no results|none)\b"),
        "to-detail": ("What opening an item shows", r"\b(open|detail|view)\b"),
    }),
    "settings": (r"\b(settings|preferences|notifications|account|configure)\b", {
        "current-value": ("Every setting shows its current value", r"\b(current|on|off)\b"),
        "save-model": ("Applies instantly, or on save: one model for the page", r"\b(instant|save|apply)\b"),
        "defaults": ("Resetting to defaults", r"\b(default|reset)\b"),
        "permission": ("Who can change each setting", r"\b(admin|permission|who can|locked)\b"),
    }),
    "dashboard": (r"\b(dashboard|overview|analytics|metrics|kpi)\b", {
        "range": ("Which period it covers, and changing it", r"\b(date|range|period|days)\b"),
        "freshness": ("How current the numbers are", r"\b(updated|as of|live|real[- ]time)\b"),
        "no-data": ("No data yet, and loading", r"\b(empty|no data|loading)\b"),
        "drill-down": ("What a number opens", r"\b(drill|detail|open)\b"),
    }),
}


def text_of(b):
    parts = [b.get("title", ""), b.get("purpose", ""), b.get("rawDescription", ""), " ".join(b.get("scopeTerms", []) or [])]
    for k in ("priorities", "coreTasks", "requiredElements", "acceptanceCriteria", "edgeCases"):
        for x in b.get(k, []) or []:
            parts += [str(v) for v in x.values() if isinstance(v, str)]
    parts += [str(x) for x in b.get("outOfScope", []) or []]
    return " ".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("brief")
    args = ap.parse_args()
    b = yaml.safe_load(open(args.brief)) or {}
    key, text = b.get("ticketKey", "brief"), text_of(b)
    named = b.get("pagePattern")
    head = f"{b.get('title', '')} {b.get('purpose', '')} {' '.join(b.get('scopeTerms', []) or [])}"
    guessed = [p for p, (rx, _) in PATTERNS.items() if re.search(rx, head, re.I)]
    patterns = [p for p in (named if isinstance(named, list) else [named]) if p] if named else guessed
    if not patterns:
        print(f"{key} pattern: none recognized (set pagePattern if it's one of {', '.join(PATTERNS)})")
        return 0
    decisions = b.get("patternDecisions", {}) or {}
    undecided, lines = [], []
    for p in patterns:
        if p not in PATTERNS:
            print(f"  ✗ unknown pagePattern '{p}' (one of {', '.join(PATTERNS)})")
            return 2
        for cap, (what, rx) in PATTERNS[p][1].items():
            d = decisions.get(cap)
            if d not in ("in-scope", "out-of-scope", "new-brief", "question"):
                hint = "in-scope" if re.search(rx, text, re.I) else "?"
                undecided.append((cap, what, hint))
            elif d == "question":
                lines.append(f"  ? {cap}: {what}")
    print(f"{key} pattern: {', '.join(patterns)}" + ("" if named else " (suggested from the brief's words: set pagePattern)")
          + (f"; {len(undecided)} implied capability(ies) undecided" if undecided else ""))
    for cap, what, hint in undecided:
        print(f"  ✗ {cap}: {what}" + ("  (the brief mentions it: likely in-scope)" if hint == "in-scope" else ""))
    for l in lines:
        print(l)
    if undecided:
        print("Paste into the brief and decide each (in-scope | out-of-scope | new-brief | question):")
        print(f"pagePattern: {patterns[0] if len(patterns) == 1 else patterns}")
        print("patternDecisions:")
        for cap, _, hint in undecided:
            print(f"  {cap}: {'in-scope' if hint == 'in-scope' else '?'}")
    return 2 if undecided or not named else 1 if lines else 0


if __name__ == "__main__":
    sys.exit(main())

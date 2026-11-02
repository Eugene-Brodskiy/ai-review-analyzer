"""Scores a real run against the planted ground truth.

Usage: python score.py <ground-truth.csv> <tagged.csv> <insights.csv>
(tagged.csv and insights.csv = the sheet tabs downloaded as CSV after the run)
"""
import csv
import sys

sys.stdout.reconfigure(encoding="utf-8")
load = lambda p: [r for r in csv.DictReader(open(p, encoding="utf-8")) if any(r.values())]
truth, tagged, insights = (load(p) for p in sys.argv[1:4])

tags = {r["review_id"]: {t.strip() for t in r["themes"].split("|") if t.strip()} for r in tagged}
top = [r for r in insights if r["top_issue"] == "yes"]

print("== Planted issues: found as a top issue? ==")
found, matched_top = 0, set()
for t in (t for t in truth if t["type"] == "planted_issue"):
    themes = t["accepted_themes"].split("|")
    hits = [r for r in top if r["sku"] == t["sku"] and r["theme"] in themes]
    ids = t["review_ids"].split("|")
    tagged_ok = sum(any(f"{th}:negative" in tags.get(i, set()) for th in themes) for i in ids)
    found += bool(hits)
    matched_top.update((r["sku"], r["theme"]) for r in hits)
    print(f"{t['id']} {'FOUND' if hits else 'MISSED':6} {t['sku']} {t['description']}"
          f" | planted reviews tagged correctly: {tagged_ok}/{len(ids)}")

print("\n== Traps (should NOT be top issues) ==")
trap_hits = 0
for t in (t for t in truth if t["type"] == "trap"):
    hit = any(r["sku"] == t["sku"] and r["theme"] in t["accepted_themes"].split("|") for r in top)
    trap_hits += hit
    print(f"{t['id']} {'FALSE ALARM' if hit else 'ok':11} {t['description']}")

extra = [r for r in top if (r["sku"], r["theme"]) not in matched_top]
planted_ids = [i for t in truth if t["type"] == "planted_issue" for i in t["review_ids"].split("|")]
recall = sum(any(f"{th}:negative" in tags.get(i, set())
                 for t in truth if i in t["review_ids"].split("|")
                 for th in t["accepted_themes"].split("|")) for i in planted_ids)
missing = sum(r["tag_status"] == "missing" for r in tagged)

print("\n== Summary ==")
print(f"Planted issues found: {found} of {sum(t['type'] == 'planted_issue' for t in truth)}")
print(f"Planted complaints tagged correctly: {recall} of {len(planted_ids)}")
print(f"Traps raised as issues: {trap_hits} of {sum(t['type'] == 'trap' for t in truth)}")
print(f"Other top issues not planted: {len(extra)} {[(r['sku'], r['theme'], r['mentions']) for r in extra]}")
print(f"Reviews the AI skipped: {missing} of {len(tagged)}")

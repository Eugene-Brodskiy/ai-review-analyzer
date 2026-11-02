"""Static checks on the built workflow: valid JSON, every $('Node') reference and connection
points to an existing node, every AI chain has a model and a parser, no secrets inside."""
import json
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
wf = json.load(open(sys.argv[1], encoding="utf-8"))
names = {n["name"] for n in wf["nodes"]}
problems = []

for n in wf["nodes"]:
    for ref in re.findall(r"\$\('([^']+)'\)", n["parameters"].get("jsCode", "")):
        if ref not in names:
            problems.append(f"{n['name']}: references missing node '{ref}'")

for src, outs in wf["connections"].items():
    if src not in names:
        problems.append(f"connection from missing node '{src}'")
    for links in outs.values():
        for group in links:
            for link in group:
                if link["node"] not in names:
                    problems.append(f"{src} -> missing node '{link['node']}'")

for n in wf["nodes"]:
    if n["type"].endswith("chainLlm"):
        kinds = {k for src, outs in wf["connections"].items() for k, links in outs.items()
                 for g in links for l in g if l["node"] == n["name"]}
        for need in ("ai_languageModel", "ai_outputParser"):
            if need not in kinds:
                problems.append(f"{n['name']}: no {need} connected")

raw = json.dumps(wf)
for marker in ("AIza", "sk-", "docs.google.com", "credentials", "@gmail"):
    if marker in raw:
        problems.append(f"secret-like marker found: {marker}")

print("nodes:", len(names), "| problems:", problems or "none")
sys.exit(1 if problems else 0)

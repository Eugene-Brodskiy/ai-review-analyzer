"""Assembles the importable n8n workflow from code/*.js and prompts/*.md.

Usage: python build_workflow.py <project folder>
Writes workflow/AI-Review-Analyzer.json (no credentials, sheet id placeholder).
"""
import json
import sys
import uuid
from pathlib import Path

root = Path(sys.argv[1])
SHEET_ID = "YOUR_GOOGLE_SHEET_ID"
MODEL = "models/gemini-3.5-flash-lite"

code = lambda name: (root / "code" / f"{name}.js").read_text(encoding="utf-8")
prompt = lambda name: "=" + (root / "prompts" / f"{name}.md").read_text(encoding="utf-8").strip()
header = lambda name: (root / "data" / f"{name}.csv").read_text(encoding="utf-8").splitlines()[0].split(",")


def node(name, type_, version, position, parameters, **extra):
    return {"parameters": parameters, "type": type_, "typeVersion": version, "position": position,
            "id": str(uuid.uuid4()), "name": name, **extra}


def sheet(tab):
    return {"documentId": {"__rl": True, "value": SHEET_ID, "mode": "id"},
            "sheetName": {"__rl": True, "value": tab, "mode": "name"}}


def read_sheet(name, tab, position, **extra):
    return node(name, "n8n-nodes-base.googleSheets", 4.7, position, {**sheet(tab), "options": {}}, **extra)


def append_sheet(name, tab, position):
    schema = [{"id": c, "displayName": c, "required": False, "defaultMatch": False, "display": True,
               "type": "string", "canBeUsedToMatch": True, "removed": False} for c in header(tab)]
    return node(name, "n8n-nodes-base.googleSheets", 4.7, position, {
        "operation": "append", **sheet(tab),
        "columns": {"mappingMode": "autoMapInputData", "value": {}, "matchingColumns": [], "schema": schema},
        "options": {}})


def llm_chain(name, prompt_name, position, delay_ms):
    return node(name, "@n8n/n8n-nodes-langchain.chainLlm", 1.9, position, {
        "promptType": "define", "text": prompt(prompt_name), "hasOutputParser": True,
        "batching": {"batchSize": 1, "delayBetweenBatches": delay_ms}},
        retryOnFail=True, maxTries=3, waitBetweenTries=5000)


def gemini(name, position):
    return node(name, "@n8n/n8n-nodes-langchain.lmChatGoogleGemini", 1.2, position,
                # One tagger call returns up to 40 reviews, so the default output limit is too small.
                {"modelName": MODEL, "options": {"maxOutputTokens": 8192, "temperature": 0}})


def parser(name, example, position):
    return node(name, "@n8n/n8n-nodes-langchain.outputParserStructured", 1.3, position,
                {"jsonSchemaExample": json.dumps(example, indent=2, ensure_ascii=False)})


def code_node(name, file, position):
    return node(name, "n8n-nodes-base.code", 2, position, {"jsCode": code(file)})


# Examples use a product that is NOT in the dataset, so they can't hint at the planted answers.
TAG_EXAMPLE = {"reviews": [{
    "review_id": "R001", "sentiment": "mixed",
    "themes": [{"theme": "noise", "polarity": "negative", "detail": "pump hums loudly at night"},
               {"theme": "pet_acceptance", "polarity": "positive", "detail": "cat drinks more water"}],
    "quote": "she drinks way more now, but the hum keeps me awake"}]}
ADVICE_EXAMPLE = {
    "actions": [{"issue_id": "ISSUE 1", "summary": "The water fountain pump is loud at night.",
                 "page_fix": "Replace the claim 'whisper-quiet' with the real noise level and add a tip to place it away from bedrooms.",
                 "product_or_ops_fix": "Ask the supplier for a quieter pump or test a batch for noise before shipping.",
                 "priority": "medium"}],
    "highlights": [{"sku": "PS-XXX-000", "copy_suggestion": "Cats drink more thanks to the moving water"}]}

nodes = [
    node("When clicking ‘Execute workflow’", "n8n-nodes-base.manualTrigger", 1, [0, 300], {}),
    read_sheet("Get Products", "products", [220, 300]),
    read_sheet("Get Reviews", "reviews", [440, 300], executeOnce=True),
    code_node("Build Batches", "build-batches", [660, 300]),
    llm_chain("AI Tagger", "ai-tagger", [880, 300], 4000),
    gemini("Gemini Tagger Model", [860, 520]),
    parser("Tagger Output Parser", TAG_EXAMPLE, [1020, 520]),
    code_node("Flatten Tags", "flatten-tags", [1240, 300]),
    append_sheet("Save Tagged", "tagged", [1460, 120]),
    code_node("Aggregate", "aggregate", [1460, 400]),
    append_sheet("Save Insights", "insights", [1680, 220]),
    code_node("Build Advisor Input", "build-advisor-input", [1680, 520]),
    llm_chain("AI Advisor", "ai-advisor", [1900, 520], 0),
    gemini("Gemini Advisor Model", [1880, 740]),
    parser("Advisor Output Parser", ADVICE_EXAMPLE, [2040, 740]),
    code_node("Flatten Actions", "flatten-actions", [2260, 520]),
    append_sheet("Save Actions", "actions", [2480, 520]),
]


def main_link(*targets):
    return {"main": [[{"node": t, "type": "main", "index": 0} for t in targets]]}


connections = {
    "When clicking ‘Execute workflow’": main_link("Get Products"),
    "Get Products": main_link("Get Reviews"),
    "Get Reviews": main_link("Build Batches"),
    "Build Batches": main_link("AI Tagger"),
    "AI Tagger": main_link("Flatten Tags"),
    "Flatten Tags": main_link("Save Tagged", "Aggregate"),
    "Aggregate": main_link("Save Insights", "Build Advisor Input"),
    "Build Advisor Input": main_link("AI Advisor"),
    "AI Advisor": main_link("Flatten Actions"),
    "Flatten Actions": main_link("Save Actions"),
    "Gemini Tagger Model": {"ai_languageModel": [[{"node": "AI Tagger", "type": "ai_languageModel", "index": 0}]]},
    "Tagger Output Parser": {"ai_outputParser": [[{"node": "AI Tagger", "type": "ai_outputParser", "index": 0}]]},
    "Gemini Advisor Model": {"ai_languageModel": [[{"node": "AI Advisor", "type": "ai_languageModel", "index": 0}]]},
    "Advisor Output Parser": {"ai_outputParser": [[{"node": "AI Advisor", "type": "ai_outputParser", "index": 0}]]},
}

wf = {"name": "AI Review Analyzer", "nodes": nodes, "connections": connections,
      "settings": {"executionOrder": "v1"}}
out = root / "workflow" / "AI-Review-Analyzer.json"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(wf, indent=2, ensure_ascii=False), encoding="utf-8")
print("written:", out, "| nodes:", len(nodes))

# AI Review Analyzer

An n8n workflow that reads 250 customer reviews and tells a store owner what to fix: which problems come up again and again, how many customers mention them, and what to change on the product page.

```
products + reviews (Google Sheets)
        |
        v
AI Tagger (1 call per product) ──> every review gets themes, polarity, detail, quote
        |
        v
Code: Aggregate ──> counts mentions per product × theme, decides what is a real issue
        |
        v
AI Advisor (1 call) ──> page fix + product/ops fix + priority for each issue
        |
        v
Google Sheets: tagged | insights | actions
```

## Why

Reading reviews is easy. Counting them honestly is not. A summary like "some customers find it small" doesn't tell you whether it's 2 people or 20, and whether it's worth changing the size chart.

So the work is split:

- **AI reads.** It tags every review with themes from a fixed list, so results can be counted.
- **Code counts.** A theme becomes an issue only if at least 4 reviews and at least 10% of the product's reviews mention it. One angry review doesn't make an action item.
- **AI advises.** Only for the issues code has confirmed, with the real numbers attached.

## How it was tested

The 250 reviews are **synthetic**, written for this demo (a fictional pet store, 8 products). Six problems were planted on purpose, for example a harness size chart that runs small and a bed cover that shrinks in the wash. Seven "traps" were planted too: real complaints that appear only twice and should not become action items.

The labels are in [`data/ground-truth.csv`](data/ground-truth.csv). The workflow never sees them. After the run, [`tools/score.py`](tools/score.py) compares the output with them.

## Results

One run on Google Gemini Flash-Lite, scored with `tools/score.py` ([`examples/score.txt`](examples/score.txt)):

| | |
|---|---|
| Planted issues found | **6 of 6** |
| Planted complaints tagged correctly | 43 of 44 |
| Traps raised as issues | 0 of 7 |
| Top issues that were not planted | 0 |
| Reviews the AI skipped | 0 of 250 |
| AI calls | 9 (8 tagger + 1 advisor) |
| Run time | about 3 minutes |
| API cost | $0 (Google Gemini Flash-Lite, free tier) |

The one miss: *"Too tight under the legs even on the loosest setting. Left red marks after a walk."* was planted as a sizing complaint, and the AI tagged it as comfort. Fair enough, it reads as both. The issue was still found with the other 8 reviews.

What could be better: the advisor marked all six issues as high priority, so the ranking between them is still a human call.

## Example output

From [`examples/actions.csv`](examples/actions.csv):

| Product | Evidence | Fix on the product page |
|---|---|---|
| Clumping Cat Litter | 8 of 34 reviews, avg 2.8 | Correct the claim '99% dust-free' to state that some dust may occur when pouring. |
| Orthopedic Dog Bed | 6 of 31 reviews, avg 2.5 | Correct the claim 'machine washable at 30 °C' by advising hand wash or cool wash to prevent cover shrinkage. |
| No-Pull Dog Harness | 8 of 35 reviews, avg 2.8 | Correct the size chart claims; state that sizes run snug and customers should order a size up. |

## Run it yourself

1. Create a Google Sheet with five tabs from `data/`: `products`, `reviews`, `tagged`, `insights`, `actions` (do not import `ground-truth.csv`).
2. Import `workflow/AI-Review-Analyzer.json` into n8n.
3. Connect your Google Gemini and Google Sheets credentials, and put your sheet ID into the five Google Sheets nodes.
4. Execute the workflow. Before running it again, clear the `tagged`, `insights` and `actions` tabs (rows are appended).
5. Optional: download the `tagged` and `insights` tabs as CSV and run
   `python tools/score.py data/ground-truth.csv tagged.csv insights.csv`

## Files

- `workflow/` – the n8n workflow (no credentials)
- `prompts/` – the two AI prompts
- `code/` – the JavaScript inside the Code nodes
- `data/` – products, reviews, sheet headers, ground truth
- `examples/` – the real output of the demo run: tagged reviews, insights, actions and the score
- `tools/` – dataset builder, local pipeline test, scoring script

Stack: n8n · Google Gemini Flash-Lite · Google Sheets · JavaScript · Python

Built by [Yevhenii Brodskyi](https://www.linkedin.com/in/yevhenii-brodskyi).

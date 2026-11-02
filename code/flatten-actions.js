// One sheet row per action: fixes for each top issue, then copy ideas from what customers praise.
const PRIORITY = { high: 1, medium: 2, low: 3 };

const parse = o => (typeof o === 'string' ? JSON.parse(o) : o);
const input = $('Build Advisor Input').first().json;
const products = Object.fromEntries($('Get Products').all().map(i => [i.json.sku, i.json]));
const advice = parse($input.first().json.output ?? $input.first().json);

const issues = Object.fromEntries(input.issues.map(r => [r.issue_id, r]));

const fixes = (advice.actions ?? [])
  .filter(a => issues[a.issue_id]) // ignore anything the AI invented
  .map(a => {
    const r = issues[a.issue_id];
    return {
      type: 'fix',
      priority: PRIORITY[a.priority] ? a.priority : 'medium',
      sku: r.sku,
      product_name: r.product_name,
      theme: r.theme,
      evidence: `${r.mentions} of ${r.reviews_total} reviews (${r.share_pct}%), avg rating ${r.avg_rating}`,
      summary: a.summary,
      page_fix: a.page_fix,
      product_or_ops_fix: a.product_or_ops_fix,
    };
  })
  .sort((a, b) => PRIORITY[a.priority] - PRIORITY[b.priority]);

const highlights = (advice.highlights ?? [])
  .filter(h => products[h.sku])
  .map(h => ({
    type: 'highlight',
    priority: 'low',
    sku: h.sku,
    product_name: products[h.sku].product_name,
    theme: '',
    evidence: '',
    summary: 'What customers praise most',
    page_fix: String(h.copy_suggestion ?? '').replace(/^\s*[-•*]\s*/, ''), // the model sometimes adds a bullet
    product_or_ops_fix: '',
  }));

// An issue the AI skipped still gets a row, so nothing found by code silently disappears.
const skipped = input.issues
  .filter(r => !fixes.some(f => f.sku === r.sku && f.theme === r.theme))
  .map(r => ({
    type: 'fix',
    priority: 'high',
    sku: r.sku,
    product_name: r.product_name,
    theme: r.theme,
    evidence: `${r.mentions} of ${r.reviews_total} reviews (${r.share_pct}%), avg rating ${r.avg_rating}`,
    summary: `Not analysed by the AI Advisor. What customers say: ${r.example_details}`,
    page_fix: '',
    product_or_ops_fix: '',
  }));

return [...fixes, ...skipped, ...highlights].map(json => ({ json }));

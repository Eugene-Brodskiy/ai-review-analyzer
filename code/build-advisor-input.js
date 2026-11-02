// One item for the AI Advisor: the top issues found by code, plus what customers praise most.
const MAX_HIGHLIGHTS_PER_PRODUCT = 1;
const MIN_PRAISE_MENTIONS = 5;
// Themes that make useful product-page copy (not delivery speed, price or "other").
const COPY_THEMES = new Set([
  'sizing_fit', 'comfort', 'build_quality', 'durability', 'cleaning_washing', 'odor_control', 'clumping',
  'ease_of_use', 'app_connectivity', 'noise', 'pet_acceptance', 'health_effect',
]);

const products = Object.fromEntries($('Get Products').all().map(i => [i.json.sku, i.json]));
const insights = $input.all().map(i => i.json);

const issues = insights
  .filter(r => r.top_issue === 'yes')
  .map((r, i) => ({ ...r, issue_id: `ISSUE ${i + 1}`, page_claims: products[r.sku]?.page_claims ?? '' }));

const highlights = [];
for (const sku of Object.keys(products)) {
  insights
    .filter(r => r.sku === sku && r.polarity === 'positive' && r.mentions >= MIN_PRAISE_MENTIONS && COPY_THEMES.has(r.theme))
    // Don't praise what is also a top issue for the same product.
    .filter(r => !issues.some(i => i.sku === sku && i.theme === r.theme))
    .sort((a, b) => b.mentions - a.mentions)
    .slice(0, MAX_HIGHLIGHTS_PER_PRODUCT)
    .forEach(r => highlights.push(r));
}

const issueLine = r =>
  `${r.issue_id} | ${r.sku} | ${r.product_name} | theme: ${r.theme} | ${r.mentions} of ${r.reviews_total} reviews (${r.share_pct}%), avg rating ${r.avg_rating} | what customers say: ${r.example_details} | quotes: ${r.example_quotes} | product page says: ${r.page_claims}`;
const praiseLine = r =>
  `${r.sku} | ${r.product_name} | theme: ${r.theme} | ${r.mentions} of ${r.reviews_total} reviews | what customers say: ${r.example_details}`;

return [{
  json: {
    issue_count: issues.length,
    issues,
    issues_text: issues.map(issueLine).join('\n') || 'none',
    highlights_text: highlights.map(praiseLine).join('\n') || 'none',
  },
}];

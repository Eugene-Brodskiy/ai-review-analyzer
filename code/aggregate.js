// Code does the counting, not the AI: mentions per product × theme, and which ones are real issues.
const MIN_MENTIONS = 4;   // a top issue needs at least 4 reviews...
const MIN_SHARE = 0.10;   // ...and at least 10% of that product's reviews

const products = Object.fromEntries($('Get Products').all().map(i => [i.json.sku, i.json]));
const rows = $input.all().map(i => i.json);

const total = {};
const groups = {};
for (const r of rows) {
  total[r.sku] = (total[r.sku] ?? 0) + 1;
  const themes = r.themes ? r.themes.split(' | ') : [];
  const details = r.details ? r.details.split(' | ') : [];
  themes.forEach((t, i) => {
    const [theme, polarity] = t.split(':');
    const key = `${r.sku}|${theme}|${polarity}`;
    const g = (groups[key] ??= { sku: r.sku, theme, polarity, ids: [], ratings: [], details: [], quotes: [] });
    if (g.ids.includes(r.review_id)) return; // a review counts once per theme
    g.ids.push(r.review_id);
    g.ratings.push(Number(r.rating));
    if (details[i]) g.details.push(details[i]);
    if (r.quote) g.quotes.push(r.quote);
  });
}

const unique = arr => [...new Set(arr.map(s => s.toLowerCase()))];

return Object.values(groups)
  .map(g => {
    const share = g.ids.length / total[g.sku];
    // 'other' is a catch-all of unrelated complaints, so it never counts as one issue.
    const top = g.polarity === 'negative' && g.theme !== 'other' && g.ids.length >= MIN_MENTIONS && share >= MIN_SHARE;
    return {
      sku: g.sku,
      product_name: products[g.sku]?.product_name ?? '',
      theme: g.theme,
      polarity: g.polarity,
      mentions: g.ids.length,
      reviews_total: total[g.sku],
      share_pct: Math.round(share * 100),
      avg_rating: Math.round((g.ratings.reduce((a, b) => a + b, 0) / g.ratings.length) * 10) / 10,
      top_issue: top ? 'yes' : 'no',
      example_details: unique(g.details).slice(0, 4).join(' | '),
      example_quotes: g.quotes.slice(0, 3).map(q => q.replace(/\|/g, '/')).join(' | '),
      review_ids: g.ids.join(' '),
    };
  })
  .sort((a, b) => a.sku.localeCompare(b.sku) || (a.top_issue === 'yes' ? -1 : 0) - (b.top_issue === 'yes' ? -1 : 0) || b.mentions - a.mentions)
  .map(json => ({ json }));

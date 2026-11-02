// One AI call per product: all of its reviews in one compact list (split if a product has more than 40).
const MAX_PER_BATCH = 40;

const products = $('Get Products').all().map(i => i.json);
const reviews = $input.all().map(i => i.json);

const batches = [];
for (const p of products) {
  const own = reviews.filter(r => r.sku === p.sku);
  for (let i = 0; i < own.length; i += MAX_PER_BATCH) {
    const chunk = own.slice(i, i + MAX_PER_BATCH);
    batches.push({
      json: {
        sku: p.sku,
        product_name: p.product_name,
        page_claims: p.page_claims,
        review_count: chunk.length,
        review_ids: chunk.map(r => r.review_id),
        reviews_text: chunk.map(r => `${r.review_id} | ${r.rating}/5 | ${r.title} | ${r.text}`).join('\n'),
      },
    });
  }
}
return batches;

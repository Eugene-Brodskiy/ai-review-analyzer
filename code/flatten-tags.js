// One row per review. Checks that the AI returned every review once and used only allowed themes.
const THEMES = new Set([
  'sizing_fit', 'comfort', 'build_quality', 'durability', 'cleaning_washing', 'dust', 'smell',
  'odor_control', 'clumping', 'ease_of_use', 'app_connectivity', 'noise', 'pet_acceptance',
  'health_effect', 'value_for_money', 'delivery', 'packaging', 'description_accuracy', 'other',
]);
const POLARITY = new Set(['positive', 'negative', 'neutral']);
const clean = s => String(s ?? '').trim().toLowerCase();

// A broken AI answer must not crash the run: that batch's reviews just come out as "missing".
const parse = o => {
  try { return (typeof o === 'string' ? JSON.parse(o) : o) ?? {}; } catch (e) { return {}; }
};
const batches = $('Build Batches').all().map(i => i.json);
const reviews = Object.fromEntries($('Get Reviews').all().map(i => [i.json.review_id, i.json]));

const rows = [];
$input.all().forEach((item, idx) => {
  const batch = batches[idx];
  const answer = parse(item.json.output ?? item.json);
  const tagged = Array.isArray(answer.reviews) ? answer.reviews.filter(Boolean) : [];
  const byId = Object.fromEntries(tagged.map(t => [String(t.review_id).trim().toUpperCase(), t]));

  for (const id of batch.review_ids) {
    const r = reviews[id];
    const t = byId[id];
    const themes = (Array.isArray(t?.themes) ? t.themes.filter(Boolean) : []).map(th => ({
      theme: THEMES.has(clean(th.theme)) ? clean(th.theme) : 'other',
      // An unclear polarity is not counted as a complaint.
      polarity: POLARITY.has(clean(th.polarity)) ? clean(th.polarity) : 'neutral',
      detail: String(th.detail ?? '').replace(/\|/g, '/').trim(),
    }));
    rows.push({
      json: {
        review_id: id,
        sku: r.sku,
        rating: Number(r.rating),
        sentiment: t?.sentiment ?? '',
        themes: themes.map(x => `${x.theme}:${x.polarity}`).join(' | '),
        details: themes.map(x => x.detail).join(' | '),
        quote: t?.quote ?? '',
        tag_status: t ? 'ok' : 'missing',
      },
    });
  }
});
return rows;

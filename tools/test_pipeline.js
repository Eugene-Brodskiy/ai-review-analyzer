// Runs every Code node of the workflow on the real dataset, with mock AI answers built from the
// ground truth (a "perfect tagger"). Checks the plumbing and the thresholds, not the AI quality.
// Usage: node test_pipeline.js <project folder>
const fs = require('fs');
const path = require('path');
const assert = require('assert');

const root = process.argv[2];
const read = p => fs.readFileSync(path.join(root, p), 'utf8');

function parseCsv(text) {
  const rows = []; let row = []; let cell = ''; let q = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (q) {
      if (c === '"' && text[i + 1] === '"') { cell += '"'; i++; }
      else if (c === '"') q = false;
      else cell += c;
    } else if (c === '"') q = true;
    else if (c === ',') { row.push(cell); cell = ''; }
    else if (c === '\n' || c === '\r') {
      if (c === '\r' && text[i + 1] === '\n') i++;
      row.push(cell); rows.push(row); row = []; cell = '';
    } else cell += c;
  }
  if (cell || row.length) { row.push(cell); rows.push(row); }
  const [head, ...body] = rows.filter(r => r.some(Boolean));
  return body.map(r => Object.fromEntries(head.map((h, i) => [h, r[i] ?? ''])));
}

const items = arr => arr.map(json => ({ json }));
const outputs = {};
function runNode(name, file, input) {
  const $ = n => ({ all: () => outputs[n], first: () => outputs[n][0] });
  const $input = { all: () => input, first: () => input[0] };
  outputs[name] = new Function('$', '$input', read(file))($, $input);
  return outputs[name];
}

const products = parseCsv(read('data/products.csv'));
const reviews = parseCsv(read('data/reviews.csv'));
const truth = parseCsv(read('data/ground-truth.csv'));
outputs['Get Products'] = items(products);
outputs['Get Reviews'] = items(reviews);

const label = {};
for (const t of truth) for (const id of t.review_ids.split('|')) label[id] = t;

// 1. Build Batches
const batches = runNode('Build Batches', 'code/build-batches.js', outputs['Get Reviews']);
assert.strictEqual(batches.length, 8, 'one batch per product');
assert.strictEqual(batches.reduce((s, b) => s + b.json.review_count, 0), 250);

// Mock AI Tagger: planted/trap reviews get their theme; others get a generic theme by rating.
// One batch drops a review and one invents an id and a theme, to test the checks.
const tagOut = batches.map((b, bi) => {
  const list = b.json.review_ids.map(id => {
    const r = reviews.find(x => x.review_id === id);
    const t = label[id];
    const themes = t
      ? [{ theme: t.accepted_themes.split('|')[0], polarity: 'negative', detail: t.description.slice(0, 40) }]
      : [{ theme: Number(r.rating) >= 4 ? 'comfort' : 'other', polarity: Number(r.rating) >= 4 ? 'positive' : 'negative', detail: r.title }];
    return { review_id: id, sentiment: Number(r.rating) >= 4 ? 'positive' : 'negative', themes, quote: r.text.slice(0, 50) };
  });
  if (bi === 7) list.pop();
  if (bi === 6) list.push({ review_id: 'R999', sentiment: 'negative', themes: [{ theme: 'made_up', polarity: 'bad', detail: 'x' }], quote: '' });
  if (bi === 5) list[0].themes.push({ theme: 'made_up_theme', polarity: 'meh', detail: 'x' });
  if (bi === 4) { list[0].themes = [{ theme: ' Durability ', polarity: 'Negative', detail: 'case test' }]; list[1].themes = null; list[2].review_id = list[2].review_id.toLowerCase(); }
  return { json: { output: { reviews: list } } };
});

// 2. Flatten Tags
const tagged = runNode('Flatten Tags', 'code/flatten-tags.js', tagOut);
assert.strictEqual(tagged.length, 250, 'every review gets a row, invented ids are dropped');
assert.strictEqual(tagged.filter(r => r.json.tag_status === 'missing').length, 1, 'dropped review is marked missing');
assert.ok(!tagged.some(r => r.json.review_id === 'R999'));
assert.ok(!tagged.some(r => /made_up/.test(r.json.themes)), 'unknown themes become other');
assert.ok(tagged.some(r => r.json.themes.split(' | ').includes('other:neutral')),'unknown polarity becomes neutral, not a complaint');
assert.ok(tagged.some(r => r.json.themes === 'durability:negative' && r.json.details === 'case test'), 'theme/polarity case is normalised');
assert.strictEqual(tagged.filter(r => r.json.tag_status === 'missing').length, 1, 'lowercase id still matched');

// A completely broken AI answer must not crash Flatten Tags.
const broken = runNode('Flatten Tags', 'code/flatten-tags.js', tagOut.map((t, i) => (i === 0 ? { json: { output: 'not json {' } } : t)));
assert.strictEqual(broken.filter(r => r.json.tag_status === 'missing').length, 1 + batches[0].json.review_count);
outputs['Flatten Tags'] = tagged;

// 3. Aggregate
const insights = runNode('Aggregate', 'code/aggregate.js', tagged);
const top = insights.filter(r => r.json.top_issue === 'yes').map(r => `${r.json.sku}:${r.json.theme}`);
const planted = truth.filter(t => t.type === 'planted_issue').map(t => `${t.sku}:${t.accepted_themes.split('|')[0]}`);
const traps = truth.filter(t => t.type === 'trap').map(t => `${t.sku}:${t.accepted_themes.split('|')[0]}`);
console.log('top issues:', top);
assert.deepStrictEqual([...top].sort(), [...planted].sort(), 'exactly the 6 planted issues are top issues');
assert.ok(!traps.some(t => top.includes(t)), 'no trap becomes a top issue');

// 4. Build Advisor Input
const adv = runNode('Build Advisor Input', 'code/build-advisor-input.js', insights);
assert.strictEqual(adv.length, 1);
assert.strictEqual(adv[0].json.issue_count, 6);
console.log('\nadvisor issues_text sample:\n' + adv[0].json.issues_text.split('\n')[0]);
console.log('highlights:\n' + adv[0].json.highlights_text);

// Mock AI Advisor: answers 5 of 6 issues, invents one, adds highlights.
const advice = {
  actions: adv[0].json.issues.slice(0, 5).map((r, i) => ({ issue_id: r.issue_id, summary: 's', page_fix: 'p', product_or_ops_fix: 'o', priority: ['high', 'medium', 'low', 'urgent', 'high'][i] })),
  highlights: [{ sku: 'PS-HAR-001', copy_suggestion: 'c' }, { sku: 'PS-XXX', copy_suggestion: 'x' }],
};
advice.actions.push({ issue_id: 'ISSUE 99', summary: 'made up' });

// 5. Flatten Actions
const actions = runNode('Flatten Actions', 'code/flatten-actions.js', [{ json: { output: JSON.stringify(advice) } }]);
const fixes = actions.filter(a => a.json.type === 'fix');
assert.strictEqual(fixes.length, 6, '5 answered + 1 skipped issue still listed');
assert.ok(fixes.some(f => f.json.summary.startsWith('Not analysed')), 'skipped issue is visible');
assert.ok(!actions.some(a => a.json.summary === 'made up'), 'invented issue dropped');
assert.strictEqual(actions.filter(a => a.json.type === 'highlight').length, 1, 'unknown sku highlight dropped');
assert.ok(fixes.every(f => ['high', 'medium', 'low'].includes(f.json.priority)), 'priority normalised');

// Columns must match the sheet headers exactly.
const header = f => read(f).split(/\r?\n/)[0].split(',');
assert.deepStrictEqual(Object.keys(tagged[0].json), header('data/tagged.csv'));
assert.deepStrictEqual(Object.keys(insights[0].json), header('data/insights.csv'));
assert.deepStrictEqual(Object.keys(actions[0].json), header('data/actions.csv'));

// Optional: write the mock tabs as CSV, to test score.py end to end.
if (process.argv[3]) {
  const esc = v => { const s = String(v ?? ''); return /[",\n\r]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s; };
  const toCsv = rows => [Object.keys(rows[0].json).join(','), ...rows.map(r => Object.values(r.json).map(esc).join(','))].join('\n') + '\n';
  fs.writeFileSync(path.join(process.argv[3], 'tagged.csv'), toCsv(tagged));
  fs.writeFileSync(path.join(process.argv[3], 'insights.csv'), toCsv(insights));
}

console.log('\nALL CHECKS PASSED | batches', batches.length, '| tagged', tagged.length, '| insights', insights.length, '| actions', actions.length);

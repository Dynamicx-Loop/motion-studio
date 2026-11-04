// Run the generated search script with a small DOM stub: no browser or network.
// CHECK_INPUTS: ["docs.html"]
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '../..');
const selected = process.argv.indexOf('--output');
const edition = process.argv.indexOf('--edition');
const requested = selected >= 0 ? process.argv[selected + 1] :
  process.env.MOTION_STUDIO_DOCS_EDITION ||
  (edition >= 0 ? path.join(root, 'outputs/docs-site', process.argv[edition + 1]) : null);
function publishedBundle() {
  const landing = fs.readFileSync(path.join(root, 'docs.html'), 'utf8');
  const link = landing.match(/href="([^"#]+\/supporting-records\.html)"/);
  assert.ok(link, 'Build a docs edition before testing the published library.');
  return path.dirname(path.resolve(root, link[1]));
}
const bundle = requested ? path.resolve(requested) : publishedBundle();
const html = fs.readFileSync(path.join(bundle, 'supporting-records.html'), 'utf8');
const data = html.match(/<script id="search-data" type="application\/json">([\s\S]*?)<\/script>/)[1];
class Element {
  constructor() { this.children = []; this.listeners = {}; this.value = ''; }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this.children = children; }
  addEventListener(event, fn) { this.listeners[event] = fn; }
}
const elements = Object.fromEntries(['search-data','search-controls','doc-search','doc-filter','doc-results','result-count'].map(id => [id, new Element()]));
elements['search-controls'].hidden = true;
elements['search-data'].textContent = data;
elements['doc-filter'].value = 'all';
const context = {
  document: {
    getElementById: id => elements[id],
    createElement: () => new Element(),
    createTextNode: text => ({textContent: text}),
  },
};
const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]);
assert.equal(scripts.length, 1);
vm.runInNewContext(scripts[0], context, {timeout: 1000});
assert.equal(elements['search-controls'].hidden, false);
const records = JSON.parse(data);
assert.equal(elements['doc-results'].children.length, records.length);
for (const row of elements['doc-results'].children) {
  const href = row.children[2].href;
  assert.ok(href.startsWith('documentation/pages/'));
  assert.ok(fs.existsSync(path.join(bundle, href)), href);
}
elements['doc-search'].value = 'sOmA';
elements['doc-search'].listeners.input();
assert.ok(elements['doc-results'].children.length > 1);
elements['doc-filter'].value = 'baseline';
elements['doc-filter'].listeners.change();
assert.deepEqual(elements['doc-results'].children.map(row => row.children[2].href),
  records.filter(record => record.state === 'baseline' &&
    [record.title, record.description, record.text].join(' ').toLowerCase().includes('soma'))
    .map(record => record.url));
elements['doc-search'].value = 'zzzz-no-match';
elements['doc-search'].listeners.input();
assert.match(elements['result-count'].textContent, /^0 documents/);
elements['doc-search'].value = '';
elements['doc-filter'].value = 'all';
elements['doc-filter'].listeners.change();
assert.equal(elements['doc-results'].children.length, records.length);
// Initialization failure must retain the static library and leave controls hidden.
const staticRows = [{textContent: 'Existing authored document link'}];
elements['doc-results'].children = staticRows;
elements['search-data'].textContent = 'invalid JSON';
elements['search-controls'].hidden = true;
vm.runInNewContext(scripts[0], context, {timeout: 1000});
assert.equal(elements['doc-results'].children, staticRows);
assert.equal(elements['search-controls'].hidden, true);
console.log(JSON.stringify({documents: records.length, test: 'generated supporting-record search, relative destinations, failed initialization preserves static links', cases: 6, browser_file_open_test: false}));

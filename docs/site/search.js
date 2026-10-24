'use strict';
// All document text is embedded at build time; there is no fetch or service worker.
(() => {
const controls = document.getElementById('search-controls');
try {
const searchData = JSON.parse(document.getElementById('search-data').textContent);
const searchBox = document.getElementById('doc-search');
const filter = document.getElementById('doc-filter');
const results = document.getElementById('doc-results');
const count = document.getElementById('result-count');
function search() {
  const words = searchBox.value.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
  const hits = searchData.filter(doc => (filter.value === 'all' || filter.value === doc.state)
    && words.every(word => `${doc.title} ${doc.path} ${doc.text}`.toLocaleLowerCase().includes(word)));
  results.replaceChildren(...hits.map(doc => {
    const row = document.createElement('li');
    const a = document.createElement('a'); a.href = doc.url; a.textContent = doc.title;
    const badge = document.createElement('span'); badge.className = 'badge ' + doc.state; badge.textContent = doc.stateLabel;
    const path = document.createElement('p'); path.className = 'path'; path.textContent = doc.path;
    const excerpt = document.createElement('p'); excerpt.className = 'small'; excerpt.textContent = doc.description;
    row.append(badge, document.createTextNode(' '), a, excerpt, path); return row;
  }));
  count.textContent = `${hits.length} document${hits.length === 1 ? '' : 's'}${hits.length ? '' : ' — try a broader search or another status'}.`;
}
// Initialize completely before replacing the static library or revealing controls.
search();
searchBox.addEventListener('input', search); filter.addEventListener('change', search);
controls.hidden = false;
} catch (error) {
  // The authored page and original library remain readable if search cannot start.
  controls.hidden = true;
}
})();

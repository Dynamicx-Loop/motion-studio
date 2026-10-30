const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
(async () => {
  const source = fs.readFileSync(path.join(__dirname, '../motion_studio/integrations/_umr_binding_viewer/human-motion.js'));
  const {humanMotion} = await import('data:text/javascript;base64,' + source.toString('base64'));
  const meta = {chunk_size: 2, frame_count: 8, vertex_count: 1,
    chunks: Array.from({length: 4}, (_, i) => ({file: String(i), start: i * 2, count: 2}))};
  let calls = 0;
  const cache = humanMotion(meta, async (file, Type, count) => {calls++; assert.equal(Type, Int16Array); assert.equal(count, 6); return new Int16Array([+file, 2, 3, 4, 5, 6]);});
  await cache.load(0); await cache.load(1);
  assert.equal(calls, 1); assert.deepEqual([...cache.vertices(1)], [4, 5, 6]);
  await cache.load(2); await cache.load(4); await cache.load(6);
  assert.ok(cache.vertices(0)); assert.equal(cache.vertices(2), null);
  cache.pin(6); await cache.load(2); assert.equal(cache.vertices(0), null);
  assert.ok(cache.vertices(6));
  await assert.rejects(cache.load(8), /out of range/);
  let fail = true;
  const retry = humanMotion(meta, async () => {if (fail) throw Error('missing chunk'); return new Int16Array(6);});
  await assert.rejects(retry.load(0), /missing chunk/); fail = false;
  await retry.load(0); assert.ok(retry.vertices(0));
  console.log('Human chunk cache: frame slices, bounded eviction, displayed-frame pin and error recovery passed');
})().catch(error => {console.error(error); process.exitCode = 1;});

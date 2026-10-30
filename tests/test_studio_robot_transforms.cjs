const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
(async () => {
  const source = fs.readFileSync(path.join(__dirname, '../motion_studio/studio/web/robot-motion.js'));
  const {transformArrayType} = await import('data:text/javascript;base64,' + source.toString('base64'));
  assert.equal(transformArrayType({}), Float32Array, 'historical bundles remain readable');
  assert.equal(transformArrayType({transform_schema:2, transform_dtype:'<f8'}), Float64Array);
  for (const meta of [{transform_schema:2}, {transform_dtype:'<f8'}, {transform_schema:2,transform_dtype:'<f4'}, {transform_schema:3,transform_dtype:'<f8'}]) {
    assert.throws(() => transformArrayType(meta), /encoding/);
  }
  const values = new Float64Array([100.123456, 50.123456]);
  const decoded = new (transformArrayType({transform_schema:2, transform_dtype:'<f8'}))(values.buffer);
  assert.deepEqual([...decoded], [100.123456, 50.123456]);
  console.log('Explicit float64 and historical float32 replay encodings passed');
})().catch(error => {console.error(error); process.exitCode = 1;});

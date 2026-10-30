// Encoding is explicit for new bundles; original saved bundles predate dtype metadata.
export function transformArrayType(meta) {
  if (meta.transform_schema === undefined && meta.transform_dtype === undefined) return Float32Array;
  if (meta.transform_schema === 2 && meta.transform_dtype === '<f8') return Float64Array;
  throw Error('Unsupported robot transform encoding');
}

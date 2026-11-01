const sampleNames={
  'hiphi-quick':'Get up · short excerpt',
  'hiphi-get-up':'Get up · full sequence',
  'adapt-tennis':'Tennis practice'
};
export function motionLabel(item){
  if(sampleNames[item.id])return sampleNames[item.id];
  return (item.asset?.name||item.name||'Imported motion').replace(/\.[^.]+$/,'').replace(/[_-]+/g,' ').replace(/\s+/g,' ').trim();
}
export function motionSummary(item){
  const asset=item.asset||item;
  if(Number.isFinite(asset.frame_count)&&Number.isFinite(asset.fps)&&asset.fps>0){
    const seconds=asset.frame_count/asset.fps;
    const duration=seconds<10?`${seconds.toFixed(1)}s`:`${Math.round(seconds)}s`;
    return `${duration} · ${Math.round(asset.fps)} FPS`;
  }
  return item.id==='hiphi-quick'?'2.0s · HiPHI':item.id==='adapt-tennis'?'Full clip · ADAPT':'Full clip · HiPHI';
}
export function motionItems(state){
  const motions=state.motions||[],catalog=state.catalog?.motions||[];
  const used=new Set(catalog.map(item=>item.asset_id).filter(Boolean));
  return [...catalog.map(item=>({...item,sample:true,asset:motions.find(asset=>asset.asset_id===item.asset_id)})),
    ...motions.filter(asset=>!used.has(asset.asset_id)).map(asset=>({id:asset.asset_id,name:asset.name,asset,available:true,sample:false}))];
}

// Derived inspection builds are explicit; selecting a stage never launches work.
export function renderInspection({run, selectedStage, api, refresh, failure}) {
  const host = document.getElementById('inspection-tools');
  host.replaceChildren();
  host.dataset.identity = `${run?.run_id}/${run?.revision_id}/${selectedStage}`;
  if (!run || run.read_only || !['sampling','training','binding','retargeting','motion'].includes(selectedStage)) return;
  const stage = run.stages.find(value => value.stage === selectedStage);
  if (stage?.status !== 'available') return;
  const button = document.createElement('button');
  button.textContent = stage.inspection_url ? 'Build a fresh standalone inspection' : 'Build inspection + standalone bundle';
  const message = document.createElement('span'); message.setAttribute('role','status');
  button.onclick = async () => {
    button.disabled = true; message.textContent = 'Building a fresh CPU inspection; native computation continues independently…';
    try {
      const result = await api(`/api/runs/${run.run_id}/inspections/${selectedStage}`, {revision_id: run.revision_id});
      await refresh();
      if (host.dataset.identity === `${run.run_id}/${run.revision_id}/${selectedStage}`) {
        const location = document.createElement('p'); location.textContent = `Standalone HTTP bundle: ${result.path}`; host.append(location);
      }
    } catch (error) {failure(error); message.textContent = error.message;} finally {button.disabled = false;}
  };
  host.append(button, message);
  if (stage.inspection_url) {
    for (const [label,file] of [['Open standalone viewer','index.html'], ['Native outputs, config, logs','files.html'], ['Export provenance','provenance.json']]) {
      const link = document.createElement('a'); link.textContent = label;
      link.href = stage.inspection_url.replace('index.html',file); link.target = '_blank'; link.rel = 'noopener';
      host.append(document.createTextNode(' · '),link);
    }
  }
}

"""Render current saved bindings with the established six-row report vocabulary."""
import hashlib
import json
from pathlib import Path
import plot_report as plot

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
plot.NAMES['astro']='Fist Astro + Dex3-1'
plot.NAMES['g1']='G1 reused control'
columns=[(s,n) for n in ['human','astro','g1'] for s in ['smplx','soma']]
for center in ['spine1','bbox50']:
    plot.plot('astro-fist-static-v1',columns,f'canonical-{center}.png',center,
              f'Fist Astro d207095 / {center} / fresh seed 0, 500 epochs; G1 slots reused')
plot.plot('astro-fist-static-v1',[('smplx','human','bbox50'),('smplx','astro','bbox50'),('smplx','g1','spine1')],
          'canonical-selected.png','mixed','Selected SMPL-X illustrations / source, Astro bbox50, G1 spine1 / different centering')
plot.plot('astro-fist-static-v1',[(s,r,c) for c in ['spine1','bbox50'] for r in ['astro','g1'] for s in ['smplx']],
          'canonical-matched.png','mixed','SMPL-X matched-centering companions / spine1 pair, then bbox50 pair')
plot.read(Path(__file__))
(HERE/'canonical-figure-provenance.json').write_text(json.dumps({
    'figure_language':'en','inputs':plot.INPUTS,'source_mask_checks':plot.CHECKS,
    'outputs':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
               for p in plot.OUT.glob('canonical-*.png')}},indent=2)+'\n')

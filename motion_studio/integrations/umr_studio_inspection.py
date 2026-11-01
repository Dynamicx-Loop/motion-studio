"""Offline inspection derivatives of explicitly verified native stage artifacts."""
from dataclasses import dataclass
import html
import json
from pathlib import Path
import shutil
import subprocess

from .umr_stages import CHECKOUT, PIN, native_environment
from motion_studio.studio._history import confined_file, digest

_WEB = Path(__file__).parents[1] / 'studio/web'


@dataclass(frozen=True)
class InspectionInputs:
    """JSON receipts plus registered paths; paths map receipt-relative names to files.

    Callers verify receipt/dependency identity. This adapter verifies every file
    again before and after export; no native solver/trainer is called. Motion
    reconstruction alone requires the receipt's exact model file/hash.
    """
    run_id: str
    revision_id: str
    stage: str
    receipts: dict
    artifacts: dict[str, dict[str, Path]]


def artifact(inputs, stage, suffix):
    matches = [p for name, p in inputs.artifacts[stage].items()
               if name == suffix or name.endswith('/' + suffix)]
    if len(matches) != 1:
        raise ValueError(f'Expected one {stage} artifact: {suffix}')
    return matches[0]


def _verify(inputs):
    for stage, receipt in inputs.receipts.items():
        if set(receipt['artifacts']) != set(inputs.artifacts[stage]):
            raise ValueError('Inspection artifact set differs from receipt')
        for name, expected in receipt['artifacts'].items():
            if digest(inputs.artifacts[stage][name]) != expected:
                raise ValueError(f'Changed stage artifact: {stage}/{name}')


def export_inspection(inputs: InspectionInputs, destination: Path, *,
                      checkout: Path = CHECKOUT, python: Path | None = None) -> Path:
    """Create a fresh standalone HTTP folder with all native results and local vendor.

    Never writes through inputs or aliases. Failed fresh directories retain logs
    but are not returned/published. Returns the absolute bundle folder.
    """
    destination = Path(destination)
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(destination)
    destination = destination.resolve()
    for paths in inputs.artifacts.values():
        if any(p.resolve().is_relative_to(destination) or destination.is_relative_to(p.resolve().parent)
               for p in paths.values()):
            raise ValueError('Inspection destination overlaps its native input')
    _verify(inputs)
    if inputs.stage != 'binding':
        revision = subprocess.check_output(['git','-C',str(checkout),'rev-parse','HEAD'],text=True).strip()
        if revision != PIN or subprocess.check_output(['git','-C',str(checkout),'diff','--name-only','HEAD'],text=True).strip():
            raise ValueError('Inspection requires unchanged pinned native source')
        for name, expected in inputs.receipts[inputs.stage].get('environment',{}).get('native_files',{}).items():
            if digest(confined_file(checkout,name)) != expected:
                raise ValueError('Native reference source changed: '+name)
    vendor = json.loads((_WEB/'vendor-manifest.json').read_text())
    for name, info in vendor['resources'].items():
        if digest(_WEB/'inspection/vendor'/name) != info['sha256']:
            raise ValueError('Changed independently vendored resource: ' + name)
    destination.mkdir(parents=True, exist_ok=False)
    try:
        for stage, paths in inputs.artifacts.items():
            for name, source in paths.items():
                # Reuse the same confinement rules as reads; never trust receipt names.
                if Path(name).is_absolute() or '..' in Path(name).parts or '\\' in name:
                    raise ValueError('Invalid native artifact path')
                target = destination/'native'/stage/name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
                if digest(target) != inputs.receipts[stage]['artifacts'][name]:
                    raise ValueError('Copied native artifact differs from receipt: '+name)
        (destination/'receipts.json').write_text(json.dumps(inputs.receipts, indent=2)+'\n')
        if inputs.stage == 'binding':
            for name in ('bindings.json','human-vertices.bin','human-faces.bin','robot-vertices.bin','robot-faces.bin'):
                source = artifact(inputs, 'binding', name)
                relative = next(n for n,p in inputs.artifacts['binding'].items() if p == source)
                shutil.copyfile(destination/'native/binding'/relative, destination/name)
        else:
            worker = Path(__file__).with_name('_umr_studio_inspection_worker.py')
            request = {'run_id':inputs.run_id,'revision_id':inputs.revision_id,'stage':inputs.stage,
                       'receipts':inputs.receipts,
                       'artifacts':{s:{n:str(destination/'native'/s/n) for n in paths} for s,paths in inputs.artifacts.items()}}
            (destination/'inspection-request.json').write_text(json.dumps(request, indent=2))
            with (destination/'export.log').open('x') as log:
                subprocess.run([str(python or checkout/'.venv/bin/python'), '-B', '-u', str(worker),
                                str(checkout), str(destination/'inspection-request.json'), str(destination)],
                               env=native_environment(), stdout=log, stderr=subprocess.STDOUT,
                               check=True, timeout=7200)
        for name in ('index.html','app.js','playback.js','bridge.js','THIRD_PARTY_NOTICES.md',
                     'vendor/three.module.js','vendor/OrbitControls.js'):
            target = destination/name; target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(_WEB/'stage-inspection'/name, target) if not name.startswith('vendor/') else shutil.copyfile(_WEB/'inspection'/name, target)
        for name in ('human-motion.js', 'robot-motion.js'):
            shutil.copyfile(_WEB/name, destination/name)
        shutil.copyfile(_WEB/'vendor-manifest.json', destination/'vendor-manifest.json')
        _verify(inputs)
        implementation = [Path(__file__), *Path(__file__).parent.glob('_umr_studio_*.py'),
                          *(_WEB/'stage-inspection').glob('*'), _WEB/'robot-motion.js', _WEB/'human-motion.js']
        record = {'run_id':inputs.run_id, 'revision_id':inputs.revision_id,'stage':inputs.stage,
                  'umr_revision':PIN, 'source_receipts':'receipts.json',
                  'scope':'Fresh read-only derivative; no training or retarget solve; source labels, paired slot identity and target ownership remain separate',
                  'implementation_sha256':{str(p):digest(p) for p in implementation if p.is_file()}}
        (destination/'provenance.json').write_text(json.dumps(record,indent=2)+'\n')
        (destination/'preservation.json').write_text(json.dumps({'stage_artifacts_unchanged':True})+'\n')
        files = {str(p.relative_to(destination)):digest(p) for p in sorted(destination.rglob('*')) if p.is_file()}
        links = ''.join(f'<li><a href="{html.escape(name, quote=True)}">{html.escape(name)}</a></li>' for name in files)
        (destination/'files.html').write_text('<!doctype html><meta charset="utf-8"><title>Inspection files</title><h1>Native outputs and provenance</h1><p>Standalone bundle: serve this directory over local HTTP. No UMR runtime is needed for viewing. Original asset/model terms apply separately; licensed weights are excluded.</p><ul>'+links+'</ul>')
        files['files.html'] = digest(destination/'files.html')
        (destination/'files.json').write_text(json.dumps(files,indent=2)+'\n')
        return destination
    except Exception as error:
        (destination/'failure.json').write_text(json.dumps({'error':str(error)})+'\n')
        raise

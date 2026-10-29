"""Stage complete documentation before publishing any compatibility entry."""
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import shutil
import tempfile

from ._builder import Bundle, digest
from .portable import root_entry
from ._verify import validate_staged_reading

REPORT = Path('outputs/umr-binding-report')
ENTRIES = ('docs.html', 'docs-basic.html', 'docs/site/home.html')


@dataclass(frozen=True)
class BuildResult:
    output: Path
    documents: int
    manifest: Path


def _copy_report(source, destination):
    inputs, outputs, links = {}, {}, {}
    for path in sorted(source.rglob('*')):
        if path.is_symlink():
            link = os.readlink(path)
            if Path(link).is_absolute() or not path.resolve().is_relative_to(source.resolve()):
                raise ValueError(f'Report link escapes its portable closure: {path}')
            target = destination / path.relative_to(source)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.symlink_to(link, target_is_directory=path.is_dir())
            links[str(path.relative_to(source))] = link
            continue
        if not path.is_file():
            continue
        relative = path.relative_to(source)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        # Copy, never hard-link: decoration must not mutate research input bytes.
        shutil.copyfile(path, target)
        value = {'sha256': digest(target.read_bytes()), 'bytes': target.stat().st_size}
        if digest(path.read_bytes()) != value['sha256']:
            raise ValueError(f'Research input changed while copying: {path}')
        inputs[str(REPORT / relative)] = {**value, 'root': 'evidence'}
        outputs[str(relative)] = value
    return inputs, outputs, links


def build_edition(source_root: Path, evidence_root: Path, *, edition='current',
                  output: Path | None = None, saved_edition: Path | None = None) -> BuildResult:
    """Build and publish an edition; missing/changed required inputs raise.

    source_root owns catalog/templates/records and compatibility entries.
    evidence_root owns recorded outputs, including the existing research bundle.
    saved_edition explicitly enables missing-source fallback from hash-checked
    snapshots. A new edition is required even when reusing saved sources.
    """
    source_root, evidence_root = Path(source_root).resolve(), Path(evidence_root).resolve()
    if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9._-]*', edition):
        raise ValueError('Edition must be a single safe directory name')
    output = Path(output).absolute() if output else source_root / 'outputs/docs-site' / edition
    report = evidence_root / REPORT
    if output.exists() or output.is_symlink():
        raise FileExistsError(f'Edition must be fresh: {output}')
    if output.resolve().is_relative_to(report.resolve()) or report.resolve().is_relative_to(output.resolve()):
        raise ValueError('Edition output must be separate from research input')
    if not (report / 'index.html').is_file():
        raise FileNotFoundError(f'Existing research viewer required at {report}')
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='.docs-stage-', dir=output.parent))
    originals = {name: (source_root / name).read_bytes() if (source_root / name).exists() else None
                 for name in ENTRIES}
    published = []
    try:
        # Resolve catalog first so missing canonical sources do not copy a large bundle.
        bundle = Bundle(source_root, evidence_root, stage,
                        Path(saved_edition).resolve() if saved_edition else None)
        for doc in bundle.docs:
            bundle.read(source_root / doc['path'])
        copied_inputs, copied_outputs, copied_links = _copy_report(report, stage)
        # Existing decoration is unwound against its own byte-checked originals.
        prior = json.loads((stage / 'documentation/manifest.json').read_text()) if (stage / 'documentation/manifest.json').exists() else {}
        bundle.preserved = prior.get('preserved_originals', {})
        manifest = bundle.build()
        manifest['inputs'] = {**copied_inputs, **manifest['inputs']}
        manifest['outputs'] = {**copied_outputs, **manifest['outputs']}
        manifest['source_root'] = str(source_root)
        manifest['evidence_root'] = str(evidence_root)
        manifest['edition'] = edition
        manifest['portable_links'] = copied_links
        manifest['edition_output'] = str(output)
        prefix = os.path.relpath(output, source_root).replace(os.sep, '/') + '/'
        documents = [root_entry((stage / 'docs.html').read_text(), prefix),
                     root_entry((stage / 'docs-basic.html').read_text(), prefix),
                     root_entry((stage / 'docs.html').read_text(), '../../' + prefix, '../../')]
        manifest['preserved_entries'] = {}
        for name, data in originals.items():
            if data is not None:
                archive = 'history/entry-pages/' + digest(data) + '/' + name
                bundle.write(archive, data)
                manifest['preserved_entries'][name] = {'archive': archive, 'original_sha256': digest(data)}
        for key, name, document in zip(('root_entry', 'plain_entry', 'compatibility_entry'), ENTRIES, documents):
            manifest[key] = {'path': name, 'sha256': digest(document.encode()), 'bytes': len(document.encode())}
        manifest['outputs'].update(bundle.outputs)
        validate_staged_reading(stage, output.resolve(), source_root, dict(zip(ENTRIES, documents)))
        # A copied old verification receipt describes a different edition.
        receipt = stage / 'documentation/verification.json'
        receipt.unlink(missing_ok=True)
        manifest['outputs'].pop('documentation/verification.json', None)
        # The manifest describes itself through its schema, not a recursive hash.
        manifest['outputs'].pop('documentation/manifest.json', None)
        (stage / 'documentation/manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')
        # Each staged file has now been produced. Compatibility pages are published
        # only after all rendering, copying and original checks have succeeded.
        os.replace(stage, output)
        for name, document in zip(ENTRIES, documents):
            target = source_root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_name(target.name + '.publishing')
            temporary.write_text(document)
            os.replace(temporary, target)
            published.append(name)
        return BuildResult(output, manifest['documents'], output / 'documentation/manifest.json')
    except BaseException:
        for name in published:
            target = source_root / name
            if originals[name] is None:
                target.unlink(missing_ok=True)
            else:
                target.write_bytes(originals[name])
        if output.exists():
            shutil.rmtree(output)
        raise
    finally:
        shutil.rmtree(stage, ignore_errors=True)

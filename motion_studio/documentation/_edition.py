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

ENTRIES = ('docs.html', 'docs-basic.html', 'docs/site/home.html')


@dataclass(frozen=True)
class BuildResult:
    output: Path
    documents: int
    manifest: Path


def build_edition(source_root: Path, evidence_root: Path, *, edition='current',
                  output: Path | None = None, saved_edition: Path | None = None) -> BuildResult:
    """Build and publish an edition; missing/changed required inputs raise.

    source_root owns catalog/templates/records and compatibility entries.
    evidence_root supplies local artifacts referenced by the catalog.
    saved_edition explicitly enables missing-source fallback from hash-checked
    snapshots. A new edition is required even when reusing saved sources.
    """
    source_root, evidence_root = Path(source_root).resolve(), Path(evidence_root).resolve()
    if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9._-]*', edition):
        raise ValueError('Edition must be a single safe directory name')
    output = Path(output).absolute() if output else source_root / 'outputs/docs-site' / edition
    if output.exists() or output.is_symlink():
        raise FileExistsError(f'Edition must be fresh: {output}')
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
        manifest = bundle.build()
        manifest['source_root'] = str(source_root)
        manifest['evidence_root'] = str(evidence_root)
        manifest['edition'] = edition
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

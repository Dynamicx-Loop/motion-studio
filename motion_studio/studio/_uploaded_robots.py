"""Rebase browser-uploaded MJCF dependencies within the uploaded bundle only."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import xml.etree.ElementTree as ET

from ._contracts import StudioError


def portable_upload(root, entry, names):
    """Return portable main XML and original files; accept no outside references.

    MuJoCo includes and asset paths are relative to the original main XML parent.
    Parent components are supported only while resolving within this explicit
    uploaded boundary. The ordinary absolute-path importer remains unchanged.
    """
    base = (root / entry).parent
    active = set()
    originals = {'provenance/original/' + name:root / name for name in names}
    def locate(name):
        path = (base / name).resolve()
        if (not path.is_relative_to(root) or not path.is_file() or path.is_symlink()
                or str(name).startswith('/') or '\\' in str(name)):
            raise StudioError('invalid_upload', f'Missing or escaping uploaded dependency: {name}')
        return path
    def expand(name):
        path=locate(name)
        if path in active:
            raise StudioError('invalid_upload', 'Cyclic uploaded MJCF include')
        if any(token in path.read_bytes().upper() for token in (b'<!DOCTYPE', b'<!ENTITY')):
            raise StudioError('invalid_upload', 'XML declarations/entities are unsupported')
        active.add(path)
        try:
            tree=ET.parse(path).getroot()
            for parent in list(tree.iter()):
                for child in list(parent):
                    if child.tag=='include':
                        expanded=expand(child.attrib['file']);index=list(parent).index(child);parent.remove(child)
                        for offset,node in enumerate(expanded):parent.insert(index+offset,copy.deepcopy(node))
            return tree
        except (ET.ParseError, KeyError) as error:
            raise StudioError('invalid_upload', f'Invalid uploaded XML: {error}') from error
        finally:active.remove(path)
    tree=expand(Path(entry).name)
    directories={}
    for compiler in tree.findall('compiler'):directories.update(compiler.attrib)
    stage=Path(tempfile.mkdtemp(prefix='.portable-',dir=root))
    assets=stage / 'files';assets.mkdir()
    index=0
    for node in tree.iter():
        for field,name in list(node.attrib.items()):
            if field not in ('file','fileleft','fileright','fileup','filedown','filefront','fileback'):continue
            directory=directories.get('assetdir','')
            if node.tag in ('mesh','hfield'):directory=directories.get('meshdir',directory)
            elif node.tag=='texture':directory=directories.get('texturedir',directory)
            if directories.get('strippath')=='true':name=Path(name).name
            original=locate(str(Path(directory)/name));relative=f'files/{index:04d}-{original.name}'
            shutil.copyfile(original,stage / relative);node.set(field,relative);index+=1
    for compiler in tree.findall('compiler'):
        for field in ('assetdir','meshdir','texturedir','strippath'):compiler.attrib.pop(field,None)
    source=stage / Path(entry).name;source.write_bytes(ET.tostring(tree))
    receipt=stage / 'derivation.json'
    receipt.write_text(json.dumps({'conversion':'Rebased uploaded MJCF references within explicit uploaded bundle',
        'source_entry':entry,'original_hashes':{name:hashlib.sha256(path.read_bytes()).hexdigest() for name,path in originals.items()}},indent=2))
    originals['provenance/derivation.json']=receipt
    return source,originals

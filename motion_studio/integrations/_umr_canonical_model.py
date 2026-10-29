"""Run-local MJCF derivation; original model/include/mesh bytes remain copied intact."""
from pathlib import Path
import xml.etree.ElementTree as ET


def materialize_pose(model, destination, selection, run):
    """Expand includes and rebase asset paths inside run, then encode root pose.

    Scalar pose remains named in UMR tpose_qpos. Root body pos/quat establishes
    explicit free-root qpos0. No keyframe, geometry, joint or inertia is selected or
    regenerated. Generated model has a separate filename beside the copied model.
    """
    from .umr_canonical import CanonicalPreparationError

    def inside(path):
        path = path.resolve()
        if not path.is_relative_to(run) or not path.is_file():
            raise CanonicalPreparationError(f'Run-local XML dependency unavailable: {path}')
        return path

    def expand(path, active=()):
        path = inside(path)
        if path in active:
            raise CanonicalPreparationError('Cyclic run-local include')
        document = ET.parse(path).getroot()
        for parent in list(document.iter()):
            for child in list(parent):
                if child.tag == 'include':
                    included = expand(path.parent/child.attrib['file'], (*active, path))
                    index = list(parent).index(child)
                    parent.remove(child)
                    for offset, node in enumerate(list(included)):
                        parent.insert(index+offset, node)
        return document

    document = expand(model)
    compiler = document.find('compiler')
    dirs = compiler.attrib.copy() if compiler is not None else {}
    for node in document.iter():
        if node.tag in ('mesh', 'texture', 'hfield') and node.get('file'):
            directory = dirs.get('meshdir' if node.tag == 'mesh' else 'texturedir', '')
            node.set('file', str(inside(model.parent/directory/node.attrib['file'])))
    if compiler is not None:
        compiler.attrib.pop('meshdir', None)
        compiler.attrib.pop('texturedir', None)
    body = document.find('worldbody/body')
    if body is None or body.get('name') != selection.conventions.root_frame:
        raise CanonicalPreparationError('Derived model root differs from selection')
    if selection.root_kind != 'free':
        raise CanonicalPreparationError('Canonical UMR preparation requires a native free MJCF root')
    for key in ('euler', 'axisangle', 'xyaxes', 'zaxis'):
        body.attrib.pop(key, None)
    body.set('pos', ' '.join(format(v, '.17g') for v in selection.root_pose.translation))
    body.set('quat', ' '.join(format(v, '.17g') for v in selection.root_pose.quaternion))
    with destination.open('xb') as stream:
        ET.ElementTree(document).write(stream, encoding='utf-8', xml_declaration=True)

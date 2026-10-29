"""Inspect the selected XML closure without importing a simulator."""
import math
from pathlib import Path
import xml.etree.ElementTree as ET

from . import Joint, RobotSelectionError


def numbers(value, width, context):
    result = tuple(float(v) for v in value.split())
    if len(result) != width or not all(math.isfinite(v) for v in result):
        raise RobotSelectionError(f'Expected {width} finite numbers for {context}')
    return result


def inspect_model(root, model, representation, required, safe_path):
    """Return native scalar joints, root name/kind and exact dependency paths."""
    required = set(required)
    seen = set()
    active = set()

    def dependency(relative):
        relative = Path(relative).as_posix()
        safe_path(root, relative)
        if relative not in required:
            raise RobotSelectionError(f'Required closure omits referenced file: {relative}')
        seen.add(relative)
        return relative

    def xml(relative):
        relative = dependency(relative)
        if relative in active:
            raise RobotSelectionError(f'Cyclic XML include: {relative}')
        active.add(relative)
        try:
            tree = ET.parse(safe_path(root, relative)).getroot()
        except ET.ParseError as error:
            raise RobotSelectionError(f'Invalid XML in {relative}: {error}') from error
        # Includes are expanded in memory only, preserving source traversal order.
        for parent in list(tree.iter()):
            for child in list(parent):
                if child.tag == 'include':
                    included = xml(Path(relative).parent / child.attrib['file'])
                    index = list(parent).index(child)
                    parent.remove(child)
                    for offset, node in enumerate(list(included)):
                        parent.insert(index + offset, node)
        active.remove(relative)
        return tree

    tree = xml(model)
    model_dir = Path(model).parent
    compiler = tree.find('compiler')
    compiler = compiler.attrib if compiler is not None else {}
    if representation == 'mjcf' and compiler.get('angle', 'degree') != 'radian':
        raise RobotSelectionError('Static MJCF selection requires explicit compiler angle="radian"')
    for element in tree.iter():
        if element.tag not in ('mesh', 'texture', 'hfield'):
            continue
        filename = element.get('filename') if representation == 'urdf' else element.get('file')
        if filename:
            directory = '' if representation == 'urdf' else compiler.get(
                'meshdir' if element.tag == 'mesh' else 'texturedir', '')
            relative = dependency(model_dir / directory / filename)
            if relative.endswith('.obj'):
                for line in safe_path(root, relative).read_text().splitlines():
                    if line.startswith('mtllib '):
                        for material in line.split()[1:]:
                            dependency(Path(relative).parent / material)
    if seen != required:
        raise RobotSelectionError(f'Required closure contains unreferenced files: {sorted(required - seen)}')
    joints = []
    if representation == 'urdf':
        children = set()
        for element in tree.findall('joint'):
            children.add(element.find('child').attrib['link'])
            kind = element.attrib['type']
            if kind == 'fixed':
                continue
            if kind != 'revolute':
                raise RobotSelectionError(f'Unsupported URDF scalar joint type: {kind}')
            limits = element.find('limit').attrib
            axis = element.find('axis')
            joints.append(Joint(element.attrib['name'], kind,
                numbers(axis.get('xyz', '1 0 0') if axis is not None else '1 0 0', 3, 'axis'),
                float(limits['lower']), float(limits['upper'])))
        roots = {e.attrib['name'] for e in tree.findall('link')} - children
        if len(roots) != 1:
            raise RobotSelectionError(f'Expected one URDF root link, found {sorted(roots)}')
        root_name, root_kind = roots.pop(), 'unencoded'
    else:
        world = tree.find('worldbody')
        bodies = world.findall('body') if world is not None else []
        if len(bodies) != 1:
            raise RobotSelectionError('Expected one MJCF root body')
        root_name = bodies[0].attrib['name']
        free = list(world.iter('freejoint')) + [e for e in world.iter('joint') if e.get('type') == 'free']
        if len(free) > 1 or (free and free[0] not in list(bodies[0])):
            raise RobotSelectionError('Free root must be the single joint on the root body')
        root_kind = 'free' if free else 'fixed'
        for element in world.iter('joint'):
            kind = element.get('type', 'hinge')
            if kind == 'free':
                continue
            if kind != 'hinge':
                raise RobotSelectionError(f'Unsupported MJCF scalar joint type: {kind}')
            lower, upper = numbers(element.attrib['range'], 2, 'joint range')
            joints.append(Joint(element.attrib['name'], 'revolute',
                                numbers(element.get('axis', '0 0 1'), 3, 'axis'), lower, upper))
    names = [joint.name for joint in joints]
    if len(names) != len(set(names)):
        raise RobotSelectionError('Duplicate native scalar joint names')
    for joint in joints:
        if (not math.isfinite(joint.lower) or not math.isfinite(joint.upper)
                or joint.lower > joint.upper or not math.isclose(
                    sum(v*v for v in joint.axis), 1.0, abs_tol=1e-9)):
            raise RobotSelectionError(f'Invalid limits or unit axis for joint {joint.name}')
    return tuple(joints), root_name, root_kind


def validate_joints(model, order, actual):
    names = [j.name for j in actual]
    if not isinstance(order, list) or len(order) != len(set(order)) or set(order) != set(names):
        raise RobotSelectionError('joint_order must name every native scalar joint exactly once')
    declared = model['joints']
    if [j['name'] for j in declared] != names:
        raise RobotSelectionError('Representation joints must follow actual native model joint order')
    for expected, joint in zip(declared, actual):
        for field, value in (('kind', joint.kind), ('axis', list(joint.axis)),
                             ('lower', joint.lower), ('upper', joint.upper)):
            if expected[field] != value:
                raise RobotSelectionError(f'{joint.name} {field} differs from selected model')
    mapping = {j.name: j for j in actual}
    return tuple(mapping[name] for name in order)

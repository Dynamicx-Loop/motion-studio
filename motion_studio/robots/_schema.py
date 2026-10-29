"""Small concrete JSON and pose contracts for the owned robot catalog."""
import json
import math

from . import Conventions, RobotSelectionError, RootPose


def read_json(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise RobotSelectionError(f'Duplicate JSON field {key!r} in {path}')
            result[key] = value
        return result
    result = json.loads(path.read_text(), object_pairs_hook=unique)
    if not isinstance(result, dict) or type(result.get('schema_version')) is not int or result['schema_version'] != 1:
        raise RobotSelectionError(f'Unsupported schema_version in {path}; expected 1')
    return result


def conventions(value):
    result = Conventions(**value)
    if (result.length_unit != 'metre' or result.angle_unit != 'radian'
            or result.root_translation_unit != 'metre' or result.root_quaternion_order != 'wxyz'):
        raise RobotSelectionError('Supported conventions require metres, radians and wxyz root quaternion')
    basis = {'+X': (1, 0, 0), '-X': (-1, 0, 0), '+Y': (0, 1, 0),
             '-Y': (0, -1, 0), '+Z': (0, 0, 1), '-Z': (0, 0, -1)}
    try:
        x, y, z = (basis[a] for a in (result.forward_axis, result.left_axis, result.up_axis))
    except (KeyError, TypeError) as error:
        raise RobotSelectionError('Axes must be signed X/Y/Z directions') from error
    cross = (x[1]*y[2]-x[2]*y[1], x[2]*y[0]-x[0]*y[2], x[0]*y[1]-x[1]*y[0])
    if cross != z or not isinstance(result.root_frame, str) or not result.root_frame:
        raise RobotSelectionError('Axes must form a right-handed frame and root_frame must be named')
    return result


def _finite(value, context):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise RobotSelectionError(f'{context} must be a finite numeric scalar')
    return float(value)


def resolve_pose(document, name, representation, joints):
    if document['angle_unit'] != 'radian':
        raise RobotSelectionError('Pose angle_unit must be radian')
    definitions = document['poses']
    active = set()
    names = {j.name for j in joints}

    def expand(current):
        if current in active:
            raise RobotSelectionError(f'Cyclic pose base: {current}')
        if current not in definitions:
            raise RobotSelectionError(f'Unknown pose {current!r}; choose from {sorted(definitions)}')
        active.add(current)
        selected = definitions[current]
        allowed = {'base', 'joints', 'root_translation', 'root_quaternion',
                   'root_handling', 'representations', 'description', 'provenance'}
        if set(selected) - allowed:
            raise RobotSelectionError(f'Unknown pose fields: {sorted(set(selected) - allowed)}')
        if representation not in selected.get('representations', [representation]):
            raise RobotSelectionError(f'Pose {current} does not support {representation}')
        values = selected['joints']
        if not isinstance(values, dict) or set(values) - names:
            raise RobotSelectionError(f'Pose {current} has unknown joints: {sorted(set(values) - names)}')
        if 'base' in selected:
            result = expand(selected['base'])
            result = {**result, **selected, 'joints': {**result['joints'], **values}}
        else:
            result = dict(selected)
        active.remove(current)
        return result

    selected = expand(name)
    values = selected['joints']
    if set(values) != names:
        raise RobotSelectionError(f'Pose {name} missing joints: {sorted(names - set(values))}')
    ordered = tuple(_finite(values[j.name], f'Pose {name} joint {j.name}') for j in joints)
    for joint, value in zip(joints, ordered):
        if not joint.lower <= value <= joint.upper:
            raise RobotSelectionError(f'Pose {name} joint {joint.name}={value} outside '
                                      f'[{joint.lower}, {joint.upper}] radian')
    root_values = []
    for key, width in (('root_translation', 3), ('root_quaternion', 4)):
        vector = selected.get(key)
        if not isinstance(vector, list) or len(vector) != width:
            raise RobotSelectionError(f'Pose {name} needs {width} values for {key}')
        root_values.append(tuple(_finite(v, f'Pose {name} {key}') for v in vector))
    if not math.isclose(sum(v*v for v in root_values[1]), 1.0, abs_tol=1e-9, rel_tol=0):
        raise RobotSelectionError('Pose root needs a unit wxyz quaternion')
    handling = selected.get('root_handling')
    if not isinstance(handling, str) or not handling:
        raise RobotSelectionError('Pose root_handling must describe the root origin/placement')
    return ordered, RootPose(*root_values, handling), selected

"""Read-only, content-verified robot selection without simulator dependencies.

``resolve_robot(id, representation, pose, source_roots)`` selects an owned
versioned definition. Paths are local; identity is independent of their location.
Pose arrays use application joint order, radians and separate XYZ/wxyz root data.
Resolution never creates writable model copies; concrete adapters own that step.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


class RobotSelectionError(ValueError):
    """A required source, definition or pose is missing or incompatible."""


@dataclass(frozen=True)
class SourceFile:
    relative_path: str
    path: Path
    sha256: str
    role: str


@dataclass(frozen=True)
class Joint:
    name: str
    kind: str
    axis: tuple[float, float, float]
    lower: float
    upper: float


@dataclass(frozen=True)
class RootPose:
    translation: tuple[float, float, float]
    quaternion: tuple[float, float, float, float]
    handling: str


@dataclass(frozen=True)
class Conventions:
    length_unit: str
    angle_unit: str
    up_axis: str
    forward_axis: str
    left_axis: str
    root_frame: str
    root_translation_unit: str
    root_quaternion_order: str


@dataclass(frozen=True)
class Provenance:
    license_coverage: str
    license_note: str
    modifications: tuple[str, ...]


@dataclass(frozen=True)
class RobotSelection:
    definition_id: str
    version: int
    representation: str
    pose_name: str
    source_key: str
    source_revision: str
    source_repository: str
    provenance: Provenance
    source_root: Path
    model_path: Path
    files: tuple[SourceFile, ...]
    joints: tuple[Joint, ...]
    native_joint_names: tuple[str, ...]
    pose_values: tuple[float, ...]
    root_pose: RootPose
    root_kind: str
    conventions: Conventions
    identity: str
    findings: tuple[str, ...]
    static_validation: str = 'validated'
    runtime_validation: str = 'unverified'

    @property
    def joint_names(self) -> tuple[str, ...]:
        return tuple(joint.name for joint in self.joints)


def resolve_robot(definition_id: str, representation: str, pose: str,
                  source_roots: Mapping[str, Path | str], *,
                  definitions_root: Path | str | None = None) -> RobotSelection:
    """Validate a named selection, returning only immutable data and local paths.

    ``source_roots`` maps the definition's source key (e.g. ``menagerie_x``) to
    an existing checkout. ``definitions_root`` selects an explicit catalog, useful
    for isolated fixtures. Missing/drifted inputs raise ``RobotSelectionError``.
    Static validity does not assert URDF/MJCF equivalence or dynamic feasibility.
    """
    from ._resolve import resolve
    try:
        return resolve(definition_id, representation, pose, source_roots,
                       Path(definitions_root) if definitions_root is not None else
                       Path(__file__).resolve().parents[2] / 'robots')
    except RobotSelectionError:
        raise
    except (OSError, KeyError, TypeError, ValueError, AttributeError, IndexError) as error:
        raise RobotSelectionError(f'{definition_id}/{representation}/{pose}: {error}') from error


__all__ = ['resolve_robot', 'RobotSelection', 'RobotSelectionError',
           'SourceFile', 'Joint', 'RootPose', 'Conventions', 'Provenance']

# The optional concrete worker is imported only in its own interpreter.
from ._consistency import (compare_representations, ConsistencyReport,
                           ConsistencyFinding)
__all__ += ['compare_representations', 'ConsistencyReport', 'ConsistencyFinding']

"""Application-owned contracts; no upstream or scientific types cross this seam."""
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class StudioError(ValueError):
    """An expected user-actionable failure, exposed by HTTP as {code, message}."""
    def __init__(self, code: str, message: str, status: int = 400):
        super().__init__(message)
        self.code, self.status = code, status


class Stage(StrEnum):
    PREPARATION = 'preparation'
    SAMPLING = 'sampling'
    TRAINING = 'training'
    BINDING = 'binding'
    RETARGETING = 'retargeting'
    MOTION = 'motion'


@dataclass(frozen=True)
class StageState:
    stage: Stage
    status: str = 'unavailable'
    inspection_url: str | None = None


@dataclass(frozen=True)
class RunRecord:
    run_id: str
    revision_id: str
    name: str
    kind: str
    read_only: bool
    created_at: str
    stages: tuple[StageState, ...]
    inspection_path: str | None = None
    motion_asset_id: str | None = None


@dataclass(frozen=True)
class StorageRoots:
    """Writable application roots. Historical inputs always live outside these."""
    state: Path
    assets: Path
    runs: Path
    exports: Path


@dataclass(frozen=True)
class StageArtifact:
    """Adapter result reference: confined relative path plus verified SHA-256 bytes."""
    relative_path: str
    sha256: str
    media_type: str


@dataclass(frozen=True)
class StageResult:
    """Transport envelope for verified outputs; constructing it does not publish completion.

    Artifact paths are relative to runs/<run_id>/<revision_id>/<stage>/.
    The owning execution operation must verify identity, confinement and hashes
    before accepting a result. Upstream objects must not appear in this envelope.
    """
    run_id: str
    revision_id: str
    stage: Stage
    artifacts: tuple[StageArtifact, ...]

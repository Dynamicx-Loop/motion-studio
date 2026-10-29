"""Build isolated, locally portable reading editions from recorded evidence.

No experiment runtime or network is used. Inputs are read-only; the destination
must be fresh. Compatibility entry pages publish only after staging succeeds.
"""
from ._edition import BuildResult, build_edition

__all__ = ['BuildResult', 'build_edition', 'verify_edition']


def verify_edition(output, *, source_root=None, evidence_root=None):
    """Verify selected edition hashes, file links, anchors and offline contracts."""
    from ._verify import verify_edition as verify
    return verify(output, source_root=source_root, evidence_root=evidence_root)

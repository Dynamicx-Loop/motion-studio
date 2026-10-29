"""Monotone lateral calibration for static T-pose slots.

All inputs are in the same source-frame axes (+X left,+Y up,+Z forward).
Source and predicted points remain in their respective physical metre scales.
This operation changes only predicted X; it neither reads semantic labels nor
projects to a restricted surface. It is not a motion mapping or finger mapping.
"""
from dataclasses import dataclass
import numpy as np

@dataclass(frozen=True)
class LandmarkCalibration:
    side_sign: int
    elbow_outward: float
    wrist_outward: float
    palm_start_outward: float
    tip_outward: float
    neighbor_count: int
    elbow_slot_ids: list[int]
    wrist_slot_ids: list[int]


def infer_calibration(source_points, predicted_points, elbow, wrist,
                      side_sign, palm_start, tip, neighbor_count=32):
    """Estimate output landmarks from the k closest source surface samples.

Distances are Euclidean in the source canonical template, before any model-side
    normalization. Source centering translates both joints and samples equally.
    The corresponding output X mean estimates the learned map at each joint.
    """
    source=np.asarray(source_points,dtype=float)
    predicted=np.asarray(predicted_points,dtype=float)
    if source.shape!=predicted.shape or source.ndim!=2 or source.shape[1]!=3:
        raise ValueError('Source and predicted slots must both be N x 3')
    if not np.isfinite(source).all() or not np.isfinite(predicted).all():
        raise ValueError('Coordinates must be finite')
    if side_sign not in (-1,1) or not 1<=neighbor_count<=len(source):
        raise ValueError('Invalid side or neighbor count')
    ids=[np.argsort(np.sum((source-p)**2,axis=1),kind='stable')[:neighbor_count] for p in [elbow,wrist]]
    e,w=[float(side_sign*predicted[i,0].mean()) for i in ids]
    if not 0<e<w<tip or not e<palm_start<tip:
        raise ValueError(f'Nonmonotone calibration knots: {e,w,palm_start,tip}')
    return LandmarkCalibration(side_sign,e,w,float(palm_start),float(tip),neighbor_count,ids[0].tolist(),ids[1].tolist())


def calibrate_slots(predicted_points, calibrations):
    """Return new N x 3 points, preserving originals and both other coordinates.

Knots: (0,0), (inferred elbow,inferred elbow), (inferred wrist,palm start),
    (tip,tip). Values beyond the target tip remain unchanged. The elbow and tip
    are fixed boundaries, and each interval has positive slope. Both sides are
    calibrated independently by the same rule. No source label is inspected.
    """
    points=np.asarray(predicted_points)
    result=points.copy()
    if len({c.side_sign for c in calibrations})!=len(calibrations):
        raise ValueError('Duplicate side')
    for c in calibrations:
        x=c.side_sign*points[:,0]
        mask=(x>c.elbow_outward)&(x<c.tip_outward)
        result[mask,0]=c.side_sign*np.interp(x[mask],
            [c.elbow_outward,c.wrist_outward,c.tip_outward],
            [c.elbow_outward,c.palm_start_outward,c.tip_outward])
    return result

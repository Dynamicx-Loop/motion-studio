"""Measure static source geometry/pose controls without a model or motion solve."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
from motion_data_paths import canonical_motion_path
import hashlib
import json

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
DIAGNOSTICS = ROOT / "outputs/soma-correspondence-audit/human-weight-diagnostics.npz"


def sha(path):
    return hashlib.sha256(canonical_motion_path(path).read_bytes()).hexdigest()


def segment(start, end, height, side):
    delta = end - start
    outward = delta[0] * (1 if side == "left" else -1)
    horizontal = float(np.hypot(delta[0], delta[2]))
    return {
        "delta_xyz_m": delta.tolist(),
        "delta_xyz_per_height": (delta / height).tolist(),
        "length_m": float(np.linalg.norm(delta)),
        "length_per_height": float(np.linalg.norm(delta) / height),
        "outward_span_m": float(outward),
        "vertical_slope_per_outward_span": float(delta[1] / outward),
        "forward_slope_per_outward_span": float(delta[2] / outward),
        "elevation_degrees": float(np.degrees(np.arctan2(delta[1], horizontal))),
    }


def main():
    weights = np.load(DIAGNOSTICS, allow_pickle=False)
    report = {
        "purpose": "Static source pose and centering controls, not motion or retargeting",
        "coordinates": "meters; +X body left, +Y up, +Z forward; joint positions before/after recorded source centering",
        "height_definition": "max(vertex Y)-min(vertex Y), same as per_sample_height normalization here",
        "angle_definition": "Elevation of distal-minus-proximal joint segment relative to XZ plane; negative means distal joint lower",
        "joint_mapping_note": "Explicit semantic comparison, not a claim that joint locations or rig definitions coincide",
        "diagnostics_sha256": sha(DIAGNOSTICS),
        "sources": {},
    }
    for source in ("smplx", "soma"):
        configs = {center: json.loads((HERE / f"{source}_astro_{center}.json").read_text())
                   for center in ("spine1", "bbox50")}
        datasets = {center: np.load(config["correspondence"]["dataset"]["out"], allow_pickle=True)
                    for center, config in configs.items()}
        ds = datasets["spine1"]
        vertices = weights[source + "_vertices"]
        joints = weights[source + "_joints"]
        names = list(weights[source + "_joint_names"])
        height = float(np.ptp(vertices[:, 1]))
        lo, hi = vertices.min(0), vertices.max(0)
        offset = ds["root_offsets"][0]
        np.testing.assert_allclose(vertices - offset, ds["mesh_vertices_0"], rtol=0, atol=1e-7)
        center_info = {}
        for center, dataset in datasets.items():
            origin = dataset["root_offsets"][0]
            center_info[center] = {
                "source_native_xyz_m": origin.tolist(),
                "height_fraction_from_mesh_bottom": float((origin[1] - lo[1]) / height),
                "offset_from_spine1_m": (origin - offset).tolist(),
                "offset_from_spine1_per_height": ((origin - offset) / height).tolist(),
                "dataset_sha256": sha(configs[center]["correspondence"]["dataset"]["out"]),
            }
        item = {
            "native_bounds_m": [lo.tolist(), hi.tolist()],
            "spine1_centered_bounds_m": [(lo - offset).tolist(), (hi - offset).tolist()],
            "height_m": height, "axis_spans_m": (hi - lo).tolist(),
            "axis_spans_per_height": ((hi - lo) / height).tolist(),
            "centers": center_info,
            "joints": {name: {
                "native_xyz_m": joints[index].tolist(),
                "spine1_centered_xyz_m": (joints[index] - offset).tolist(),
                "spine1_centered_xyz_per_height": ((joints[index] - offset) / height).tolist(),
                "height_fraction_from_mesh_bottom": float((joints[index, 1] - lo[1]) / height),
            } for index, name in enumerate(names)},
            "arms": {},
        }
        for side, short in (("left", "L"), ("right", "R")):
            selected = ([f"{short}_Shoulder", f"{short}_Elbow", f"{short}_Wrist"]
                        if source == "smplx" else
                        [side.title() + suffix for suffix in ("Arm", "ForeArm", "Hand")])
            a, b, c = [joints[names.index(name)] for name in selected]
            item["arms"][side] = {
                "proximal_elbow_wrist_joint_names": selected,
                "upper_arm": segment(a, b, height, side),
                "forearm": segment(b, c, height, side),
                "shoulder_to_wrist": segment(a, c, height, side),
            }
        report["sources"][source] = item
    report["interpretation"] = [
        "Source templates have different dimensions, actor shapes, joint semantics and canonical arm poses.",
        "Identical centering names and per-sample height normalization do not make these the same actor/pose.",
        "bbox50 changes all three source coordinates; within-source comparisons preserve geometry and samples by translation.",
        "These observations describe input differences and do not assign causality for any target mismatch.",
    ]
    (HERE / "source-template-comparison.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({source: {"height_m": item["height_m"], "centers": item["centers"],
                              "arms": item["arms"]}
                      for source, item in report["sources"].items()}, indent=2))


if __name__ == "__main__":
    main()

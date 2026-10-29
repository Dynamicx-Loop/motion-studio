"""CPU geometry gates; never imports or invokes a pipeline entry point."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
from motion_data_paths import canonical_motion_path
from types import SimpleNamespace

import mujoco
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "externals/UMR"
ISOLATED = ROOT / "externals/UMR-astro-surface-experiment"
CONFIG = ROOT / "configs/umr/astro_p2_29dof.json"
sys.path.insert(0, str(ISOLATED / "scripts"))
import build_correspondence_ae_dataset as build
import mujoco_geom_surface as geom
import retarget_smpl_to_humanoid_surface_vector as single
import retarget_smpl_to_humanoid_surface_vector_batch as batch
import smpl_surface_retarget_common as common


def checksum(path):
    return hashlib.sha256(canonical_motion_path(path).read_bytes()).hexdigest()


def independent_interior(points, owners, model, data, ids):
    """Independent native MuJoCo ray test inside shrunken analytic primitives.

    For a convex primitive, hits in both opposite directions imply the point is
    inside. Shrink by 10 micrometres, matching the declared strict interior margin.
    A bounding sphere only skips impossible candidates, never decides interiors.
    """
    buried = np.zeros(len(points), bool)
    other_body = np.zeros(len(points), bool)
    for gid in ids:
        kind = int(model.geom_type[gid])
        size = model.geom_size[gid].copy()
        if kind in (mujoco.mjtGeom.mjGEOM_SPHERE, mujoco.mjtGeom.mjGEOM_CAPSULE):
            size[0] -= 1e-5
        else:
            size -= 1e-5
        radius = (size[0] + size[1] if kind == mujoco.mjtGeom.mjGEOM_CAPSULE
                  else np.linalg.norm(size))
        candidates = np.flatnonzero((owners != gid) &
            (np.linalg.norm(points - data.geom_xpos[gid], axis=1) <= radius + 1e-5))
        for i in candidates:
            args = (data.geom_xpos[gid], data.geom_xmat[gid], size, points[i])
            forward = mujoco.mju_rayGeom(*args, np.array([1., 0., 0.]), kind)
            if forward <= 0:
                continue
            backward = mujoco.mju_rayGeom(*args, np.array([-1., 0., 0.]), kind)
            if backward > 0:
                buried[i] = True
                other_body[i] |= model.geom_bodyid[owners[i]] != model.geom_bodyid[gid]
    return {"count": int(buried.sum()), "cross_body_count": int(other_body.sum()),
            "fraction": float(buried.mean())}


def world_from_root(points, center_pos, center_rot):
    return np.asarray(points, dtype=float) @ center_rot.T + center_pos


def baseline_visual(out, count):
    script = r'''
import json, sys, numpy as np
sys.path.insert(0, sys.argv[1])
import build_correspondence_ae_dataset as b
import retarget_smpl_to_humanoid_surface_vector as r
import smpl_surface_retarget_common as c
import mujoco
cfg=json.load(open(sys.argv[2])); robot=cfg["robot"]
sample=b.build_robot_sample(robot["xml"], robot["name"], int(sys.argv[4]), 9000, 8, 0., 1., point_cloud_center_name=robot["point_cloud_center"], tpose_qpos=robot["tpose_qpos"])
m=mujoco.MjModel.from_xml_path(robot["xml"])
bound=r.bind_robot_slots(m, type("Args", (), {"config_data": cfg})(), sample["points"])
np.savez_compressed(sys.argv[3], **sample, bound_geom_ids=bound["geom_ids"], bound_local_pos=bound["local_pos"], bound_local_normals=bound["local_normals"])
'''
    subprocess.run([sys.executable, "-c", script, str(SOURCE / "scripts"), str(CONFIG),
                    str(out / "baseline-visual.npz"), str(count)], check=True)
    return np.load(out / "baseline-visual.npz")


def gates(out):
    out.mkdir(parents=True, exist_ok=True)
    config = json.loads((CONFIG.parents[2] / "experiments/astro-surface-geometry/visual.json").read_text())
    robot = config["robot"]
    xml = Path(robot["xml"])
    initial_hashes = {str(p): checksum(p) for p in (CONFIG, xml)}
    model = mujoco.MjModel.from_xml_path(str(xml))
    data = mujoco.MjData(model)
    build.apply_joint_qpos(model, data, robot["tpose_qpos"], required=True)
    mujoco.mj_forward(model, data)
    selected = geom.surface_geom_ids(model, "collision_primitives")
    visual = geom.surface_geom_ids(model)
    assert len(selected) == 55 and len(visual) == 35
    assert np.all(model.geom_group[selected] == 3)
    vertices, faces, owners, center, rotation, _ = single.collect_root_mesh(
        model, data, selected, robot["point_cloud_center"])
    metrics = {"canonical_sha256": initial_hashes, "mujoco_version": mujoco.__version__,
               "primitive_geoms": len(selected), "visual_geoms": len(visual),
               "primitive_vertices": len(vertices), "primitive_faces": len(faces),
               "tolerance_m": 1e-7, "interior_margin_m": 1e-5}
    invalid_faces = inward_faces = 0
    for gid in selected:
        v, f = geom.geom_local_mesh(model, gid)
        tri = v[f].astype(float)
        normal = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        invalid_faces += int((np.linalg.norm(normal, axis=1) <= 1e-12).sum())
        inward_faces += int((np.sum(normal * tri.mean(axis=1), axis=1) <= 0).sum())
    metrics["degenerate_faces"] = invalid_faces
    metrics["nonoutward_faces"] = inward_faces
    assert invalid_faces == inward_faces == 0
    # Original area distribution, no exterior filtering or FPS, independent audit.
    tri = vertices[faces].astype(float)
    area2 = np.linalg.norm(np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]), axis=1)
    rng = np.random.default_rng(0)
    picked = rng.choice(len(faces), 20000, p=area2 / area2.sum())
    raw = build.sample_points_on_triangles(tri[picked], rng)
    metrics["raw_area_samples"] = independent_interior(world_from_root(raw, center, rotation),
                                                       owners[picked], model, data, selected)
    # Default visual regression compares the unmodified repository in a process.
    baseline = baseline_visual(out, 512)
    visual_sample = build.build_robot_sample(xml, robot["name"], 512, 9000, 8, 0., 1.,
        point_cloud_center_name=robot["point_cloud_center"], tpose_qpos=robot["tpose_qpos"])
    visual_bound = single.bind_robot_slots(model, SimpleNamespace(config_data=config), visual_sample["points"])
    compare = {key: bool(np.array_equal(baseline[key], visual_sample[key]))
               for key in ("vertices", "faces", "points", "sample_face_ids")}
    compare.update({key: bool(np.array_equal(baseline["bound_" + key], visual_bound[key]))
                    for key in ("geom_ids", "local_pos", "local_normals")})
    assert all(compare.values()), compare
    metrics["default_visual_bitwise_regression"] = compare
    primitive_config = json.loads((ROOT / "experiments/astro-surface-geometry/primitive.json").read_text())
    assert primitive_config["robot"]["visual_geom_policy"] == "collision_primitives"
    assert primitive_config["robot"]["tpose_qpos"] == robot["tpose_qpos"]
    start = time.perf_counter()
    visual_full = build.build_robot_sample(xml, robot["name"], 4096, 9000, 8, 0., 1.,
        point_cloud_center_name=robot["point_cloud_center"], tpose_qpos=robot["tpose_qpos"])
    metrics["visual_4096_sampling_seconds"] = time.perf_counter() - start
    np.savez_compressed(out / "visual-4096.npz", **visual_full)
    args = SimpleNamespace(config_data=primitive_config)
    rows = []
    clouds = {"visual": visual_full["points"]}
    coverage = []
    for seed, count in ((9000, 512), (9001, 512), (9002, 512), (9000, 4096)):
        start = time.perf_counter()
        sample = build.build_robot_sample(xml, robot["name"], count, seed, 8, 0., 1.,
            point_cloud_center_name=robot["point_cloud_center"], tpose_qpos=robot["tpose_qpos"],
            visual_geom_policy="collision_primitives")
        sampling_seconds = time.perf_counter() - start
        root_points = single.smpl_frame_to_robot_root(sample["points"])
        expected_geom = sample["face_geom_ids"][sample["sample_face_ids"]]
        start = time.perf_counter()
        binding = single.bind_robot_slots(model, args, sample["points"])
        binding_seconds = time.perf_counter() - start
        actual = common.template_points_to_world(data, binding, np.arange(count))
        expected = world_from_root(root_points, center, rotation)
        errors = np.linalg.norm(actual - expected, axis=1)
        interior = independent_interior(actual, binding["geom_ids"], model, data, selected)
        body_changes = int((model.geom_bodyid[expected_geom] != model.geom_bodyid[binding["geom_ids"]]).sum())
        geom_changes = int((expected_geom != binding["geom_ids"]).sum())
        ties = [{"point": int(i), "source_geom": int(expected_geom[i]),
                 "bound_geom": int(binding["geom_ids"][i]), "distance_m": float(errors[i]),
                 "source_name": mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, int(expected_geom[i])),
                 "bound_name": mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, int(binding["geom_ids"][i]))}
                for i in np.flatnonzero(expected_geom != binding["geom_ids"])]
        assert errors.max() <= 1e-7 and body_changes == 0, (errors.max(), body_changes)
        if ties:
            print("Same-body coincident-geom ties: " + json.dumps(ties), flush=True)
        assert interior["count"] == 0, interior
        assert np.allclose(np.linalg.norm(binding["local_normals"], axis=1), 1, atol=1e-6)
        if count == 512 and seed == 9000:
            root_sample = build.build_robot_sample(xml, robot["name"], count, seed, 8, 0., 1.,
                point_cloud_center_name=robot["point_cloud_center"], tpose_qpos=robot["tpose_qpos"],
                visual_geom_policy="collision_primitives", to_smpl_frame=False)
            np.testing.assert_array_equal(root_sample["vertices"], single.smpl_frame_to_robot_root(sample["vertices"]))
            np.testing.assert_allclose(root_sample["points"], root_points, atol=1e-7, rtol=0)
            metrics["smpl_and_robot_frame_sampling_equivalent"] = True
            batch_binding = batch.bind_robot_slots(model, args, sample["points"])
            assert all(np.array_equal(binding[key], batch_binding[key]) for key in binding)
            metrics["single_batch_binding_identical"] = True
        if count == 4096:
            clouds["primitive"] = sample["points"]
            # Explicit independent face interpolation, transformed on its ORIGINAL
            # geom after synthetic joint offsets; catches cross-joint ownership.
            for name, offset in (("left_shoulder_roll_joint", .3), ("right_hip_yaw_joint", -.25)):
                changed = mujoco.MjData(model)
                changed.qpos[:] = data.qpos
                jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, name)
                changed.qpos[model.jnt_qposadr[jid]] += offset
                mujoco.mj_forward(model, changed)
                expected_moved = np.empty_like(expected)
                for gid in np.unique(expected_geom):
                    mask = expected_geom == gid
                    local = (expected[mask] - data.geom_xpos[gid]) @ data.geom_xmat[gid].reshape(3, 3)
                    expected_moved[mask] = local @ changed.geom_xmat[gid].reshape(3, 3).T + changed.geom_xpos[gid]
                moved = common.template_points_to_world(changed, binding, np.arange(count))
                assert np.max(np.linalg.norm(moved - expected_moved, axis=1)) <= 1e-7
            metrics["synthetic_joint_owner_transport_checked"] = True
            for gid in selected:
                body = int(model.geom_bodyid[gid])
                coverage.append({"geom_id": int(gid), "geom": mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, int(gid)),
                    "body_id": body, "body": mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, body),
                    "points": int((expected_geom == gid).sum())})
            np.savez_compressed(out / "primitive-4096.npz", **sample, **{"binding_" + k: v for k, v in binding.items()})
        rows.append({"seed": seed, "points": count, "interior": interior, "body_changes": body_changes,
                     "geom_changes": geom_changes, "coincident_same_body_ties": ties, "max_identity_error_m": float(errors.max()),
                     "p95_identity_error_m": float(np.percentile(errors, 95)),
                     "sampling_seconds": sampling_seconds, "binding_seconds": binding_seconds})
        print(json.dumps(rows[-1]), flush=True)
    metrics["primitive_runs"] = rows
    metrics["coverage"] = coverage
    metrics["covered_bodies"] = len({row["body_id"] for row in coverage if row["points"]})
    assert metrics["covered_bodies"] == len(set(model.geom_bodyid[selected])) == 19
    assert {str(p): checksum(p) for p in (CONFIG, xml)} == initial_hashes
    metrics["canonical_files_unchanged"] = True
    np.savez_compressed(out / "clouds.npz", **clouds)
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    return metrics

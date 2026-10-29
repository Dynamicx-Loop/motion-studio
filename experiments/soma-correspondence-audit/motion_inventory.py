"""Fetch and inspect the public pinned SOMA example; never run retargeting."""
from pathlib import Path
import hashlib
import importlib.metadata
import json
import urllib.request

import numpy as np
from soma.io import load_soma_animation, load_usd_animation_sequence

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/soma-correspondence-audit/motion-inventory"
REVISION = "f81a01796f652260ff930d5318d6c6b845a505ed"
REPOSITORY = "https://huggingface.co/nvidia/SOMA-X"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    tree_url = f"https://huggingface.co/api/models/nvidia/SOMA-X/tree/{REVISION}?recursive=false"
    with urllib.request.urlopen(tree_url) as response:
        tree = {item["path"]: item for item in json.load(response)}
    files = []
    for name in ("LICENSE", "README.md", "example_animation.usd"):
        url = f"{REPOSITORY}/resolve/{REVISION}/{name}"
        target = OUT / name
        if not target.exists():
            with urllib.request.urlopen(url) as response:
                target.write_bytes(response.read())
        payload = target.read_bytes()
        upstream = tree[name]
        if "lfs" in upstream:
            actual = hashlib.sha256(payload).hexdigest()
            expected = upstream["lfs"]["oid"]
            algorithm = "sha256"
        else:
            actual = hashlib.sha1(f"blob {len(payload)}\0".encode() + payload).hexdigest()
            expected = upstream["oid"]
            algorithm = "git-blob-sha1"
        if actual != expected or len(payload) != upstream["size"]:
            raise ValueError(f"Pinned upstream hash/size mismatch: {name}")
        files.append({"path": str(target), "source_url": url, "size": len(payload),
                      "sha256": hashlib.sha256(payload).hexdigest(),
                      "upstream_oid": expected, "upstream_hash_algorithm": algorithm})
    if "Apache License" not in (OUT / "LICENSE").read_text():
        raise ValueError("Unexpected license; inspect before using animation")
    motion = OUT / "example_animation.usd"
    data = load_usd_animation_sequence(motion)
    with np.load("/data/motions/human_models/soma-x/f81a01796f65/overlays/umr/SOMA_neutral.npz") as model:
        names = model["joint_names"].astype(str).tolist()
    transforms, fps = load_soma_animation(motion, names, world_space=False)
    world, world_fps = load_soma_animation(motion, names, world_space=True)
    assert fps == world_fps and transforms.shape == world.shape
    assert np.isfinite(transforms).all() and np.isfinite(world).all()
    rotation = transforms[..., :3, :3]
    orthogonal_error = float(np.max(np.abs(rotation @ rotation.swapaxes(-1, -2) - np.eye(3))))
    determinant_error = float(np.max(np.abs(np.linalg.det(rotation) - 1)))
    assert orthogonal_error < 1e-5 and determinant_error < 1e-5
    report = {
        "repository": REPOSITORY, "revision": REVISION, "files": files,
        "license": "Pinned repository Apache-2.0 LICENSE retained; public anonymous download; no gated agreement accepted",
        "py_soma_x": importlib.metadata.version("py-soma-x"),
        "source": "Official shipped example animation; not synthetic and not the HiPHI actor/clip",
        "source_stage_units_meters": data.meters_per_unit,
        "source_up_axis": data.up_axis,
        "fps": fps, "time_code_start": float(data.time_codes[0]),
        "time_code_end": float(data.time_codes[-1]), "frames": len(data.time_codes),
        "time_span_seconds": float((data.time_codes[-1] - data.time_codes[0]) / fps),
        "public_joint_names": names, "authored_joint_paths": data.joint_paths,
        "local_transforms_shape": list(transforms.shape),
        "world_transforms_shape": list(world.shape),
        "output_translation_units": "meters", "rotation_convention": "absolute parent-local; column-vector transforms",
        "all_finite": bool(np.isfinite(transforms).all() and np.isfinite(world).all()),
        "maximum_rotation_orthogonality_error": orthogonal_error,
        "maximum_rotation_determinant_error": determinant_error,
        "all_authored_scales_one": bool(np.allclose(data.scales, 1, atol=1e-5)),
        "validation": "Official CPU USD readers only; no mesh posing, conversion optimization, motion retargeting, solver rollout or robot execution",
        "umr_ready": False,
        "missing_for_matched_motion": "No matched HiPHI-to-SOMA actor/pose conversion validated. UMR's inspected motion adapter consumes SOMA BVH plus shape parameters; this USD requires a separately validated adapter/conversion.",
        "bones_seed": "Gated BVH and actor fit files remain absent; no dataset agreement accepted or files downloaded",
    }
    destination = Path(__file__).with_name("motion-inventory.json")
    destination.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: value for key, value in report.items()
                      if key not in {"public_joint_names", "authored_joint_paths", "files"}}, indent=2))


if __name__ == "__main__":
    main()

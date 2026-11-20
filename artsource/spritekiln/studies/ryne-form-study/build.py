"""Render Ryne with SpriteKiln, then publish full-size color and lighting atlases."""

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from PIL import Image, ImageChops


HERE = Path(__file__).resolve().parent
RAW = HERE / "out"
ATLAS = HERE / "atlases"
SETS = {
    "base": ("motion.yaml", ["idle", "run", "run_start", "run_stop", "jump", "slash", "wave", "interact"]),
    "awakened": ("awakened.yaml", ["transform", "launch", "hover", "air_turn"]),
}


def kiln(*args):
    env = os.environ.copy()
    env.setdefault("NUMBA_CACHE_DIR", str(RAW / "numba"))
    subprocess.run([sys.executable, "-m", "spritekiln", *args], cwd=HERE, env=env, check=True)


def render(group, jobs, size):
    spec, _ = SETS[group]
    kiln("validate", spec)
    kiln("render", spec, "--jobs", str(jobs), "--size", str(size), "-o", str(RAW / str(size) / group))


def rect_bounds(rect):
    return rect["x"], rect["y"], rect["x"] + rect["w"], rect["y"] + rect["h"]


def publish(group, size):
    raw = RAW / str(size) / group
    atlas_dir = ATLAS if size == 96 else ATLAS / str(size)
    metadata_path, = (p for p in raw.glob("*.json") if p.name != "qa.json" and
                      "frames" in json.loads(p.read_text(encoding="utf-8")))
    meta = json.loads(metadata_path.read_text(encoding="utf-8"))
    qa = json.loads((raw / "qa.json").read_text(encoding="utf-8"))
    if qa["errors"]:
        raise ValueError(f"SpriteKiln QA failed for {group}: {qa['errors']}")
    data = meta["spritekiln"]
    if (set(data["animations"]) != set(SETS[group][1]) or set(data["directions"]) != {"e", "w"}
            or data["frame_size"] != size):
        raise ValueError(f"Incomplete {size} px render of {group}")
    if group == "awakened":
        for name, expected in {"transform": 28, "hover": 8, "air_turn": 16}.items():
            for track in data["animations"][name]["directions"].values():
                if len(track["frames"]) != expected:
                    raise ValueError(f"{name} requires {expected} frames per direction")
    layers = [Image.open(raw / p).convert("RGBA") for p in
              (meta["meta"]["image"], data["normal_map"], data["emissive_map"])]

    if group == "awakened":
        from transform_fx import finish_layers

        for name, clip in data["animations"].items():
            for direction, track in clip["directions"].items():
                for i, key in enumerate(track["frames"]):
                    bounds = rect_bounds(meta["frames"][key]["frame"])
                    color, normal, emission = (layer.crop(bounds) for layer in layers)
                    result = finish_layers(color, normal, emission, name, i, direction)
                    for layer, frame in zip(layers, result):
                        layer.paste(frame, bounds[:2])

    alpha, normals, glow = (layer.getchannel("A") for layer in layers)
    if ImageChops.difference(alpha, normals).getbbox():
        raise ValueError(f"Normal coverage differs from the final color atlas: {group} at {size} px")
    if ImageChops.multiply(glow, alpha.point(lambda a: 0 if a else 255)).getbbox():
        raise ValueError(f"Emission outside the final silhouette: {group} at {size} px")
    # Check the final, composited pixels, including the wide attack and turn effects.
    for key, record in meta["frames"].items():
        cell = alpha.crop(rect_bounds(record["frame"]))
        bbox = cell.getbbox()
        if not bbox or min(bbox[:2]) < 1 or bbox[2] >= cell.width or bbox[3] >= cell.height:
            raise ValueError(f"Empty or edge-touching final frame: {key}, {bbox}")

    atlas_dir.mkdir(parents=True, exist_ok=True)
    base = "ryne_" + group
    filenames = [base + suffix + ".png" for suffix in ("", "_normal", "_emissive")]
    meta["meta"]["image"], data["normal_map"], data["emissive_map"] = filenames
    for layer, filename in zip(layers, filenames):
        layer.save(atlas_dir / filename)
    (atlas_dir / f"{base}.json").write_text(json.dumps(meta, separators=(",", ":")) + "\n", encoding="utf-8")
    shutil.copyfile(raw / "qa.json", atlas_dir / f"{base}_qa.json")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--render-only", choices=SETS)
    parser.add_argument("--publish-only", action="store_true")
    parser.add_argument("--size", type=int, choices=(48, 96), help="Build just one native cell size")
    parser.add_argument("--jobs", type=int, default=1)
    args = parser.parse_args()
    for size in [args.size] if args.size else [96, 48]:
        for group in [args.render_only] if args.render_only else SETS:
            if not args.publish_only:
                render(group, args.jobs, size)
            if not args.render_only:
                publish(group, size)
    if not args.render_only and args.size != 48:
        from preview import make_previews
        make_previews()


if __name__ == "__main__":
    main()

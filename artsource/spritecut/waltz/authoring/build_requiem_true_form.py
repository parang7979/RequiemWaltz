"""Bake the registered front artwork with the same SpriteCut mesh workflow as the weapons."""

import argparse
import json
import math
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import distance_transform_edt, gaussian_filter

from build_requiem_forms import mesh, write_json


CHARACTER = Path(__file__).resolve().parents[1]
MATERIAL = CHARACTER / "materials/v008"
CLIPS = ("requiem_true_idle", "requiem_true_exit", "requiem_true_vanish")
FLECK_TILE = 4


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def spritecut(*args):
    subprocess.run([sys.executable, "-m", "spritecut", *map(str, args)], check=True)


def load_front():
    character = read(MATERIAL / "character.json")
    views = (MATERIAL / character["views"]).resolve()
    view = read(views)
    path = views.parent / next(item["file"] for item in view["views"] if item["direction"] == "front")
    with Image.open(path) as image:
        return image.convert("RGBA"), views, view


def split_front(image, views, rig):
    masks = MATERIAL / "masks"
    masks.mkdir(exist_ok=True)
    remaining = np.asarray(image.getchannel("A")) > 0
    parts, definitions = {}, []
    for order, region in enumerate(rig["regions"]):
        name = region["id"]
        if "polygon" in region:
            area = Image.new("L", image.size)
            ImageDraw.Draw(area).polygon([tuple(point) for point in region["polygon"]], fill=255)
            owns = remaining & (np.asarray(area) != 0)
        else:
            owns = remaining.copy()
        assert owns.any(), name
        remaining &= ~owns
        Image.fromarray(owns.astype(np.uint8) * 255).save(masks / f"{name}.png")
        parts[name] = {
            "mask": f"masks/{name}.png",
            "pivot": region["pivot"],
            "landmarks": region["landmarks"],
            "order": order,
        }
        definitions.append({key: region[key] for key in ("id", "parent") if key in region})
    assert not remaining.any()
    manifest = MATERIAL / "split.json"
    write_json(manifest, {"version": 1, "parts": definitions, "views": {"front": {"parts": parts}}})
    spritecut("parts", manifest, MATERIAL / "parts", "--views", views)


def smooth(value):
    value = np.clip(value, 0.0, 1.0)
    return value * value * (3.0 - 2.0 * value)


def fields(rig, shape):
    """Extend nearby joint ownership through transparent mesh edges, then soften the shared seams."""
    owner = np.full(shape, -1, dtype=int)
    for i, region in enumerate(rig["regions"]):
        with Image.open(MATERIAL / "masks" / f"{region['id']}.png") as image:
            mask = np.asarray(image) != 0
        owner[mask] = i
    nearest = distance_transform_edt(owner < 0, return_distances=False, return_indices=True)
    filled = owner[tuple(nearest)]
    return {
        region["id"]: gaussian_filter((filled == i).astype(float), rig["joint_blend_px"])
        for i, region in enumerate(rig["regions"])
    }


def rotate(x, y, px, py, angle):
    dx, dy = x - px, y - py
    cos, sin = np.cos(angle), np.sin(angle)
    return px + dx * cos - dy * sin, py + dx * sin + dy * cos


def lagged(phase, delay):
    return np.sin(phase - delay) - np.sin(-delay)


def deform(points, surface, rig, clip, index):
    x, y = np.asarray(points, dtype=float).T
    height, width = surface["body"].shape
    coord = (np.clip(np.rint(y).astype(int), 0, height - 1), np.clip(np.rint(x).astype(int), 0, width - 1))
    w = {name: image[coord] for name, image in surface.items()}
    center_x, center_y = rig["fluid_center"]
    count = len(clip["timing_ms"])
    u = index / (count - 1)
    kind = clip["clip"]
    phase = math.tau * (index / count if clip["loop"] else u * .8)

    if kind == "requiem_true_idle":
        px = x.copy()
        py = y - clip["lift_px"] * np.sin(phase)
        belly = lagged(phase, (y - 50) * .096 + (x - center_x) * .027)
        px += (x - center_x) * belly * .026 * w["body"]
        py += belly * 1.25 * w["body"]
        px += clip["tail_sway_px"] * lagged(phase, (y - 78) * .078) * smooth((y - 70) / 48) * w["tail"]
        py += 1.5 * lagged(phase, (y - 72) * .074) * smooth((y - 73) / 32) * w["tail"]
        for side, phase_delay, direction in (("right_arm", .70, -1), ("left_arm", 1.04, 1)):
            region = next(item for item in rig["regions"] if item["id"] == side)
            shoulder = region["pivot"]
            elbow = region["landmarks"]["elbow"]
            ax, ay = rotate(x, y, *shoulder, direction * math.radians(4) * lagged(phase, phase_delay))
            flex = direction * math.radians(4.6) * lagged(phase, phase_delay + .54) * smooth((y - 59) / 27)
            bx, by = rotate(ax, ay, *elbow, flex)
            px += (bx - x) * w[side]
            py += (by - y) * w[side]
        px += lagged(phase, .18) * w["head"] * .9
        py += lagged(phase, .31) * w["head"] * .5
    elif kind == "requiem_true_exit":
        scale_x, scale_y = clip["extent"][index]
        angle = math.radians(clip["coils_deg"][index])
        k = np.sin(np.pi * u)
        tuck_x = x + 3.5 * k * (w["right_arm"] - w["left_arm"])
        tuck_y = y - 2.8 * k * (w["left_arm"] + w["right_arm"] + w["tail"])
        radius = np.hypot(tuck_x - center_x, tuck_y - center_y)
        # Twisting by distance from the core rolls the folds without flipping the mesh at a joint.
        twist = angle * (.72 + .37 * smooth((radius - 12) / 48))
        curled_x, curled_y = rotate(tuck_x, tuck_y, center_x, center_y, twist)
        px = center_x + (curled_x - center_x) * scale_x
        py = center_y + (curled_y - center_y) * scale_y
    else:
        peel = smooth(u)
        drift = lagged(phase, (y - 56) * .10)
        tail_lift = smooth((y - 67) / 43)
        px = x + drift * (1.0 + 3.5 * tail_lift) * peel - (x - center_x) * .14 * peel
        py = y - clip["rise_px"] * peel - 6.0 * tail_lift * peel + drift * 2.5 * peel
    return np.round(np.column_stack((px, py)), 4).tolist()


def pigments(base, surface, clip, index, atlas_width):
    y, x = np.indices(base.shape[:2], dtype=float)
    alpha = base[:, :, 3].astype(float) / 255
    rgb = base[:, :, :3].astype(float)
    value = rgb @ np.array([.50, .18, .32])
    crest = smooth((value - 71) / 91)
    count = len(clip["timing_ms"])
    u = index / (count - 1)
    phase = math.tau * (index / count if clip["loop"] else u * 1.15)
    phase_field = y * .163 + x * .038 + np.sin(x * .124) * 1.23
    passing = .5 * lagged(phase, phase_field)
    beam = 1.0 + clip["fold_light"] * passing * crest
    colored = rgb * beam[:, :, None]

    if clip["clip"] == "requiem_true_exit":
        core = smooth((u - .35) / .65)
        tint = np.array([163., 96., 202.])
        colored += (tint - colored) * (core * .52 * (.6 + .4 * crest))[:, :, None]
        alpha *= 1 - .13 * core
    elif clip["clip"] == "requiem_true_vanish":
        depth = distance_transform_edt(alpha >= .10)
        delay = .17 + .37 * smooth(depth / 13) + surface["head"] * .10 - surface["tail"] * .075
        breakup = .048 * np.sin(x * .80 + y * .22) + .036 * np.sin(y * .57 - x * .27)
        alpha *= 1.0 - smooth((u - delay - breakup) / .27)

    rgba = np.zeros((base.shape[0], atlas_width, 4), dtype=np.uint8)
    rgba[:, :base.shape[1], :3] = np.rint(np.clip(colored, 0, 255))
    rgba[:, :base.shape[1], 3] = np.rint(alpha * 255)
    emit = np.zeros_like(rgba)
    emit[:, :base.shape[1], :3] = (176, 104, 218)
    emit[:, :base.shape[1], 3] = np.rint(alpha * crest * (30 + 45 * smooth(passing + .28)))
    return rgba, emit


def fleck_vertices(color, emission, flecks, u, width):
    posed = []
    shape = np.array([[0, 0, .55, 0], [0, .38, 1, .29], [0, .77, .54, 0], [0, .27, 0, 0]])
    for i, (x, y, dx, dy, delay) in enumerate(flecks):
        t = np.clip((u - delay) / (1.0 - delay), 0, 1)
        a = smooth(t * 5) * (1.0 - smooth((t - .30) / .70))
        cx = x + dx * t + 2.0 * math.sin(t * math.pi)
        cy = y + dy * t - 4.0 * math.sin(t * math.pi)
        size = (2.9 if i % 3 else 3.6) * (1 - .42 * t)
        posed.extend([[cx, cy], [cx + size, cy], [cx, cy + size], [cx + size, cy + size]])
        tile_x = width + i * FLECK_TILE
        color[:FLECK_TILE, tile_x:tile_x + FLECK_TILE] = (182, 105 + i % 3 * 9, 227, 0)
        emission[:FLECK_TILE, tile_x:tile_x + FLECK_TILE] = (197, 133, 246, 0)
        color[:FLECK_TILE, tile_x:tile_x + FLECK_TILE, 3] = np.rint(shape * a * 224)
        emission[:FLECK_TILE, tile_x:tile_x + FLECK_TILE, 3] = np.rint(shape * a * 142)
    return np.round(posed, 4).tolist()


def bake_clip(image, view, rig, surface, spec, destination):
    source = np.asarray(image)
    uv, triangles = mesh(image, rig["mesh_step"])
    flecks = spec.get("flecks", [])
    for index in range(len(flecks)):
        x = image.width + index * FLECK_TILE
        a = len(uv)
        uv.extend([[x, 0], [x + FLECK_TILE, 0], [x, FLECK_TILE], [x + FLECK_TILE, FLECK_TILE]])
        triangles.extend(((a, a + 1, a + 3), (a, a + 3, a + 2)))

    paths = {}
    points = {
        f"{region['id']}_{name}": point for region in rig["regions"]
        for name, point in region["landmarks"].items()
    }
    names, anchors = list(points), list(points.values())
    frames, tracks = [], []
    with TemporaryDirectory(prefix="requiem-front-bake-") as temp:
        scratch = Path(temp)
        for index, duration in enumerate(spec["timing_ms"]):
            count = len(spec["timing_ms"])
            color, emission = pigments(source, surface, spec, index, image.width + len(flecks) * FLECK_TILE)
            body_vertices = uv[:len(uv) - 4 * len(flecks)]
            vertices = deform(body_vertices, surface, rig, spec, index)
            if flecks:
                vertices.extend(fleck_vertices(color, emission, flecks, index / (count - 1), image.width))
            maps = {}
            for channel, rgba in (("color", color), ("emissive", emission)):
                name = f"{channel}-{index:02d}.png"
                Image.fromarray(rgba).save(scratch / name)
                maps[channel] = name
            if not index:
                paths = maps
            frames.append({"ms": duration, "vertices": vertices, "materials": maps})
            tracks.append({"ms": duration, "landmarks": dict(zip(names, deform(anchors, surface, rig, spec, index)))})

        recipe = {
            "version": 1, "cell": view["cell"], "pivot": view["pivot"],
            "uv": uv, "triangles": triangles, "materials": paths,
            "clips": {spec["clip"]: {"loop": spec["loop"], "frames": frames}},
        }
        recipe_path = scratch / "bake.json"
        write_json(recipe_path, recipe, None)
        spritecut("bake", recipe_path, destination / "sheets")
    write_json(destination / "tracks.json", {
        "version": 1, "direction": "front", "pivot": view["pivot"],
        "rest": points, "frames": tracks,
    })


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=CHARACTER / "motions")
    parser.add_argument("--parts-only", action="store_true")
    parser.add_argument("--clip", choices=CLIPS)
    args = parser.parse_args()
    image, views, view = load_front()
    rig = read(MATERIAL / "regions.json")
    if not (MATERIAL / "parts/index.json").is_file():
        split_front(image, views, rig)
    if args.parts_only:
        return
    surface = fields(rig, (image.height, image.width))
    for name in ([args.clip] if args.clip else CLIPS):
        relative = Path(name) / "v001"
        spec = read(CHARACTER / "motions" / relative / "motion.json")
        bake_clip(image, view, rig, surface, spec, args.output_root / relative)


if __name__ == "__main__":
    main()

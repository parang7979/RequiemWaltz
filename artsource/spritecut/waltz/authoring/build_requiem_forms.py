"""Register directional art, author local mesh motion, and bake SpriteCut sheets."""

import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory

from PIL import Image
from spritecut.prepare.pixelate import extract_pose


CHARACTER = Path(__file__).resolve().parents[1]
PROJECT = CHARACTER.parents[2]
BASE_VIEWS = CHARACTER / "materials/v002/views"
VIEWS = CHARACTER / "materials/v003/views"
PREPARED = VIEWS.parent / "prepared"
VERSION = CHARACTER / "motions/forms/v003"
COMPILED = VERSION / "compiled"
RUNTIME = PROJECT / "assets/actors/requiem_forms"
DIRECTIONS = ("front_right", "back_right")
FORM_CELL, FORM_PIVOT = (112, 104), (56, 52)
WALTZ_CELL, WALTZ_PIVOT = (64, 64), (32, 58)
SWORD_CELL, SWORD_PIVOT = (68, 28), (12, 14)

# Per-frame exposure in ms, deformation amount, and recoil distance in px.
IDLE = [(125, 0.0, 0.0), (105, .10, 0.0), (100, .21, 0.0),
        (120, .23, 0.0), (105, .14, 0.0), (105, .06, 0.0)]
ACTIONS = {
    "hand": (4, [(38, 0, 0), (40, .32, 0), (32, .65, 0), (28, 1, 0), (22, .88, 0),
                  (33, .63, 0), (50, .33, 0), (67, .12, 0), (55, 0, 0)]),
    "bow": (5, [(40, 0, 0), (35, .23, 0), (35, .52, 0), (33, .78, 0), (40, 1, 0),
                 (24, -.23, 0), (26, .14, 0), (36, -.07, 0), (60, 0, 0)]),
    "cannon": (5, [(42, 0, 0), (35, .20, 0), (34, .51, 0), (39, .92, 0), (36, 1.16, 0),
                    (24, .62, 9), (31, .26, 7), (38, -.07, 4), (72, 0, 0)]),
}
ENTER = [(15, 0.0), (20, .22), (22, .48), (24, .78), (23, .99), (26, 1.0)]
EXIT = [(16, 1.0), (20, .78), (22, .52), (22, .25), (22, .08), (16, 0.0)]


def write_json(path, value, indent=2):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=indent, ensure_ascii=False) + "\n", encoding="utf-8")


def alpha_cutout(image, cutoff):
    image.putalpha(image.getchannel("A").point([255 if p >= cutoff else 0 for p in range(256)]))
    return image


def registered(sheet, spec, scale, cell, pivot):
    """Use a measured anchor and common scale for both SpriteCut views."""
    x0, y0, x1, y1 = spec["crop"]
    crop = sheet.crop((x0, y0, x1, y1))
    crop.putalpha(crop.getchannel("A").point([p if p >= 64 else 0 for p in range(256)]))
    bounds = crop.getchannel("A").getbbox()
    picture = extract_pose(crop)
    root_x, root_y = spec["root"]
    target = picture.resize(tuple(round(n * scale) for n in picture.size), Image.Resampling.LANCZOS)
    offset = (round(pivot[0] + (x0 + bounds[0] - root_x) * scale),
              round(pivot[1] + (y0 + bounds[1] - root_y) * scale))
    if min(offset) < 0 or any(offset[i] + target.size[i] > cell[i] for i in range(2)):
        raise ValueError("Registered source exceeds the output cell")
    tile = Image.new("RGBA", cell)
    tile.paste(alpha_cutout(target, 113), offset)
    points = {name: [round(pivot[i] + (source[i] - spec["root"][i]) * scale, 3) for i in range(2)]
              for name, source in spec.get("points", {}).items()}
    return tile, points


def make_sword(sheet, spec):
    """Rotate the one-handed sword into local +X with its center at the grip."""
    root_x, root_y = spec["root"]
    axis_x, axis_y = spec["tip"][0] - root_x, spec["tip"][1] - root_y
    length = math.hypot(axis_x, axis_y)
    axis_x, axis_y = axis_x / length, axis_y / length
    crop = sheet.crop(tuple(spec["crop"]))
    crop.putalpha(crop.getchannel("A").point([p if p >= 64 else 0 for p in range(256)]))
    root_x -= spec["crop"][0]
    root_y -= spec["crop"][1]
    scale = spec["scale"]
    x, y = SWORD_PIVOT
    transform = (axis_x / (scale * 3), -axis_y / (scale * 3),
                 root_x - (x * axis_x - y * axis_y) / scale,
                 axis_y / (scale * 3), axis_x / (scale * 3),
                 root_y - (x * axis_y + y * axis_x) / scale)
    turned = crop.transform(tuple(n * 3 for n in SWORD_CELL), Image.Transform.AFFINE,
                            transform, Image.Resampling.BICUBIC)
    sword = alpha_cutout(turned.resize(SWORD_CELL, Image.Resampling.LANCZOS), 116)
    emission = Image.new("RGBA", SWORD_CELL)
    for py in range(sword.height):
        for px in range(x + spec["edge_from"], sword.width):
            red, green, blue, alpha = sword.getpixel((px, py))
            if alpha:
                value = max(red, green, blue)
                emission.putpixel((px, py), (154, 82, 226, round(value * .62)))
    return sword, emission, [round(length * scale, 2), 0]


def smooth(value):
    t = max(0.0, min(1.0, value))
    return t * t * (3.0 - 2.0 * t)


def deform(form, vertex, grip_y, amount, recoil, extent):
    x, y = vertex[0] - FORM_PIVOT[0], vertex[1] - FORM_PIVOT[1]
    if form == "hand":
        finger = smooth((x - 3.0) / 32.0)
        x -= 5.1 * amount * finger
        y = grip_y + (y - grip_y) * (1.0 - .30 * amount * finger)
    elif form == "bow":
        limb = smooth((abs(y) - 6.0) / 28.0)
        x -= 11.0 * amount * limb
        y -= math.copysign(5.6, y) * amount * limb
    else:
        chamber = smooth((18.0 - x) / 42.0)
        x -= 7.0 * amount * chamber + recoil
        y *= 1.0 + .37 * amount * chamber
    width = extent + .35 * math.sin(math.pi * extent)
    height = extent ** 1.50
    return [round(FORM_PIVOT[0] + x * width, 4), round(FORM_PIVOT[1] + y * height, 4)]


def mesh(tile, step):
    """Mesh only rectangles that contain visible texels."""
    points, indices, triangles = [], {}, []
    alpha = tile.getchannel("A")

    def vertex(x, y):
        if (x, y) not in indices:
            indices[(x, y)] = len(points)
            points.append([x, y])
        return indices[(x, y)]

    for y in range(0, tile.height, step):
        for x in range(0, tile.width, step):
            right, bottom = min(tile.width, x + step), min(tile.height, y + step)
            if not alpha.crop((x, y, right, bottom)).getbbox():
                continue
            a, b = vertex(x, y), vertex(right, y)
            c, d = vertex(x, bottom), vertex(right, bottom)
            triangles.extend(((a, b, d), (a, d, c)))
    return points, triangles


def relative(path):
    return Path(os.path.relpath(path, COMPILED)).as_posix()


def form_recipe(form, side, tile, rest_points, asset, axis):
    vertices, triangles = mesh(tile, 6)
    grip_y = rest_points["socket"][1] - FORM_PIVOT[1]
    release_index, attack = ACTIONS[form]
    body_clips, tracks = {}, {}
    motions = {
        "idle": [(ms, amount, recoil, 1.0) for ms, amount, recoil in IDLE],
        "action": [(ms, amount, recoil, 1.0) for ms, amount, recoil in attack],
        "exit": [(ms, 0.0, 0.0, extent) for ms, extent in EXIT],
        "enter": [(ms, 0.0, 0.0, extent) for ms, extent in ENTER],
    }
    for name, samples in motions.items():
        name_id = f"{form}_{side}_{name}"
        frames, sockets = [], []
        for i, (ms, amount, recoil, extent) in enumerate(samples):
            posed = [deform(form, v, grip_y, amount, recoil, extent) for v in vertices] if extent else vertices
            frame = {"ms": ms, "vertices": posed}
            if extent == 0.0:
                frame["materials"] = {"color": relative(PREPARED / "empty.png")}
            if name == "action" and i == release_index:
                frame["events"] = ["release"]
            locations = {key: deform(form, v, grip_y, amount, recoil, extent)
                         for key, v in rest_points.items()}
            if form == "bow":
                locations["socket"][0] -= round(16.0 * amount * extent, 3)
            frames.append(frame)
            sockets.append({key: [round(value - FORM_PIVOT[index], 3) for index, value in enumerate(point)]
                            for key, point in locations.items()})
        body_clips[name_id] = {"loop": name == "idle", "frames": frames}
        tracks[name_id] = sockets
    return {"version": 1, "cell": FORM_CELL, "pivot": FORM_PIVOT, "uv": vertices,
            "triangles": triangles, "materials": {"color": relative(asset)}, "clips": body_clips}, {
                "axis_deg": axis, "tracks": tracks,
            }


def rest_recipe(name, asset, tile, pivot, emissive=None):
    vertices, triangles = mesh(tile, 12)
    materials = {"color": relative(asset)}
    if emissive is not None:
        materials["emissive"] = relative(emissive)
    return {"version": 1, "cell": tile.size, "pivot": pivot, "uv": vertices, "triangles": triangles,
            "materials": materials, "clips": {name: {"loop": False, "frames": [{"ms": 100, "vertices": vertices}]}}}


def bake(name, recipe, stage):
    recipe_path = COMPILED / f"{name}.json"
    write_json(recipe_path, recipe, None)
    bundle = stage / name
    subprocess.run([sys.executable, "-m", "spritecut", "bake", recipe_path, bundle], check=True)
    manifest = json.loads((bundle / "clips.json").read_text(encoding="utf-8"))
    for entry in manifest["clips"].values():
        entry["pivot"] = manifest["pivot"]
        for image in entry["maps"].values():
            shutil.copyfile(bundle / image, RUNTIME / image)
    return manifest["clips"]


def publish_chain(bundle):
    version = CHARACTER / "motions/requiem_chain/v001"
    sheets = version / "sheets"
    sheet = json.loads((sheets / "clips.json").read_text(encoding="utf-8"))
    tracks = json.loads((version / "tracks.json").read_text(encoding="utf-8"))
    for clip in sheet["clips"].values():
        for image in clip["maps"].values():
            shutil.copyfile(sheets / image, RUNTIME / image)
    links = CHARACTER / "materials/v009/prepared/chain_links.png"
    shutil.copyfile(links, RUNTIME / links.name)
    for side in DIRECTIONS:
        form = f"chain_{side}"
        points = {}
        for name, clip in sheet["clips"].items():
            alias = f"{form}_{name.removeprefix('chain_')}"
            bundle["clips"][alias] = {**clip, "pivot": sheet["pivot"]}
            points[alias] = tracks[name]
        bundle["forms"][form] = {"axis_deg": 0, "tracks": points}
    bundle["chain_cast"] = json.loads((version / "motion.json").read_text(encoding="utf-8"))["cast"]


def main():
    prepare = json.loads((BASE_VIEWS / "registration.json").read_text(encoding="utf-8"))
    prepare["forms"]["hand"] = json.loads((VIEWS / "hand-registration.json").read_text(encoding="utf-8"))
    PREPARED.mkdir(parents=True, exist_ok=True)
    COMPILED.mkdir(parents=True, exist_ok=True)
    RUNTIME.mkdir(parents=True, exist_ok=True)
    Image.new("RGBA", FORM_CELL).save(PREPARED / "empty.png")
    shape_atlas = Image.open(BASE_VIEWS / "requiem-directions.png")
    hand_atlas = Image.open(VIEWS / "requiem-hand-grip.png")
    hero_atlas = Image.open(CHARACTER / "materials/v001/views/waltz-and-sword.png")
    sword_atlas = Image.open(BASE_VIEWS / "waltz-and-sword.png")
    indexed, tracked = {}, {}
    with TemporaryDirectory(dir=VERSION, prefix=".forms-") as work:
        stage = Path(work)
        for form, specification in prepare["forms"].items():
            source = hand_atlas if form == "hand" else shape_atlas
            for side in DIRECTIONS:
                spec = specification[side]
                key = f"{form}_{side}"
                tile, points = registered(source, spec, specification["scale"], FORM_CELL, FORM_PIVOT)
                file = PREPARED / f"{key}.png"
                tile.save(file)
                recipe, track = form_recipe(form, side, tile, points, file, spec["axis"])
                indexed.update(bake(key, recipe, stage))
                tracked[key] = track
        for side in DIRECTIONS:
            spec = prepare["waltz"]
            key = f"waltz_{side}"
            tile, _ = registered(hero_atlas, spec[side], spec["scale"], WALTZ_CELL, WALTZ_PIVOT)
            file = PREPARED / f"{key}.png"
            tile.save(file)
            indexed.update(bake(key, rest_recipe(key, file, tile, WALTZ_PIVOT), stage))
        sword, emission, sword_tip = make_sword(sword_atlas, prepare["sword"])
        sword_file, mask = PREPARED / "sword.png", PREPARED / "sword_emissive.png"
        sword.save(sword_file)
        emission.save(mask)
        indexed.update(bake("sword", rest_recipe("sword", sword_file, sword, SWORD_PIVOT, mask), stage))

    info = {"version": 1, "clips": indexed.copy(), "forms": tracked, "sword_tip": sword_tip,
            "sword_edge_from": prepare["sword"]["edge_from"]}
    publish_chain(info)
    write_json(RUNTIME / "clips.json", info)
    sheets = VERSION / "sheets"
    sheets.mkdir(exist_ok=True)
    body_clips = {name: {k: v for k, v in clip.items() if k != "pivot"}
                  for name, clip in indexed.items() if name.split("_", 1)[0] in prepare["forms"]}
    for clip in body_clips.values():
        for image in clip["maps"].values():
            shutil.copyfile(RUNTIME / image, sheets / image)
    write_json(sheets / "clips.json", {"version": 1, "cell": FORM_CELL, "pivot": FORM_PIVOT,
                                      "clips": body_clips})


if __name__ == "__main__":
    main()

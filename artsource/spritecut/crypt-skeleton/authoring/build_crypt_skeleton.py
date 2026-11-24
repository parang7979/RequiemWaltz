"""Draw, rig and bake the chamber skeleton at the game's native pixel scale."""

import json
import os
import shutil
import subprocess
import sys
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image, ImageChops, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parents[2]
ORIGINALS = ROOT / "sources/v001/originals"
MATERIAL = ROOT / "materials/v001"
MOTION = ROOT / "motions/combat/v001"
RUNTIME = PROJECT / "assets/actors/crypt_skeleton"
CELL = (64, 64)
GROUND = (32, 58)
DIRECTIONS = ("front_right", "back_right")
OUTLINE, DARK, SHADE = "#30243a", "#655161", "#927982"
BONE, LIGHT = "#c7ab93", "#edd5ac"
CLOTH, TRIM = "#594563", "#876683"
SOCKET = "#3d2a41"


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def spritecut(*args):
    subprocess.run([sys.executable, "-m", "spritecut", *args], check=True)


def bone(draw, points, color, width=4):
    draw.line(points, fill=OUTLINE, width=width + 2)
    draw.line(points, fill=color, width=width)
    draw.line([(x, y - 1) for x, y in points], fill=SHADE if color == DARK else LIGHT, width=1)


def artwork(rear):
    layers = {}

    def layer(name):
        image = Image.new("RGBA", CELL)
        layers[name] = image
        return ImageDraw.Draw(image)

    far = layer("far_leg")
    bone(far, [(29, 40), (27, 47), (26, 52)], SHADE, 3)
    far.polygon([(24, 51), (27, 50), (29, 52), (32, 53), (31, 55), (23, 55)], DARK, OUTLINE)
    far.line([(24, 53), (29, 53)], SHADE)
    near = layer("near_leg")
    bone(near, [(34, 42), (34, 49), (35, 54)], BONE, 4)
    near.polygon([(32, 53), (36, 52), (37, 54), (41, 55), (41, 57), (32, 57)], SHADE, OUTLINE)
    near.line([(34, 54), (36, 54), (38, 56), (40, 56)], BONE)
    arm = layer("far_arm")
    bone(arm, [(27, 30), (23, 35), (24, 40)], DARK, 3)
    arm.polygon([(23, 38), (26, 38), (28, 42), (25, 44), (22, 42)], SHADE, OUTLINE)

    torso = layer("torso")
    torso.polygon([(29, 25), (34, 24), (38, 27), (37, 33), (36, 39),
                   (39, 42), (35, 46), (29, 44), (25, 42), (28, 38), (26, 31)], DARK, OUTLINE)
    torso.line([(32, 26), (31, 32), (32, 38), (32, 41)], BONE, 3)
    for y in (30, 33, 36):
        ribs = [(28, y - 1), (30, y), (33, y + 1), (36, y - 1)]
        torso.line(ribs, SHADE if rear else BONE, 2)
        if not rear:
            torso.point((35, y), LIGHT)
    if rear:
        torso.line([(32, 29), (32, 36), (33, 38)], LIGHT, 1)
        torso.line([(28, 29), (28, 33)], BONE, 1)
    torso.polygon([(27, 39), (30, 41), (35, 39), (38, 41), (35, 43),
                   (34, 45), (30, 44), (29, 47), (27, 45), (26, 42)], CLOTH, OUTLINE)
    torso.line([(27, 41), (31, 42), (36, 40)], TRIM, 1)
    torso.rectangle((32, 41, 34, 42), SHADE)

    head = layer("head")
    head.polygon([(27, 14), (30, 12), (36, 12), (40, 14), (42, 17), (42, 22),
                  (40, 24), (40, 27), (37, 29), (32, 28), (30, 26), (27, 24),
                  (25, 22), (25, 17)], SHADE, OUTLINE)
    head.polygon([(26, 18), (28, 15), (32, 13), (36, 13), (40, 15), (41, 19),
                  (40, 22), (36, 24), (31, 24), (28, 22), (26, 21)], BONE)
    head.line([(27, 18), (29, 15), (33, 14), (36, 14), (39, 16)], LIGHT, 2)
    if rear:
        head.polygon([(26, 22), (29, 23), (33, 24), (37, 23), (40, 21),
                      (39, 25), (36, 27), (31, 26), (28, 24)], SHADE)
        head.line([(36, 15), (35, 18), (36, 20), (35, 23), (35, 25)], SHADE)
        head.line([(31, 26), (34, 27), (37, 26)], DARK)
    else:
        head.polygon([(28, 19), (32, 18), (34, 20), (32, 23), (29, 22)], SOCKET)
        head.polygon([(37, 19), (40, 19), (41, 20), (40, 22), (37, 22)], SOCKET)
        head.point((32, 20), TRIM)
        head.point((39, 20), TRIM)
        head.polygon([(35, 22), (36, 24), (34, 24)], DARK)
        head.polygon([(32, 25), (35, 26), (39, 24), (39, 26), (37, 28), (33, 27)], BONE)
        for x, y in [(33, 26), (35, 27), (37, 26), (39, 25)]:
            head.point((x, y), LIGHT)

    arm = layer("near_arm")
    bone(arm, [(37, 29), (40, 34), (39, 38)], BONE, 3)
    arm.polygon([(38, 37), (41, 37), (44, 39), (43, 42), (40, 42), (38, 40)], SHADE, OUTLINE)
    arm.line([(40, 38), (42, 39), (42, 40)], LIGHT)
    return layers


PARTS = {
    "far_leg": ((29, 40), None, True),
    "near_leg": ((34, 41), None, True),
    "far_arm": ((27, 30), "torso", True),
    "torso": ((32, 41), None, False),
    "head": ((34, 26), "torso", False),
    "near_arm": ((37, 29), "torso", False),
}


def pose(ms, angles=None, translations=None):
    return {"ms": ms, "angles": angles or {}, "translations": translations or {}}


CLIPS = {
    "idle": (True, [pose(210), pose(240, {"head": -2}, {"torso": [0, 1]})]),
    "walk": (True, [
        pose(75, {"far_leg": -8, "near_leg": 11, "far_arm": 14, "near_arm": -11},
             {"near_leg": [-1, -2]}),
        pose(65, {"far_leg": -2, "near_leg": 3, "near_arm": -5}, {"torso": [0, 1]}),
        pose(80, {"far_leg": 11, "near_leg": -8, "far_arm": -10, "near_arm": 13},
             {"far_leg": [0, -2]}),
        pose(65, {"far_leg": 3, "near_leg": -2, "near_arm": 4}, {"torso": [0, 1]}),
        pose(65, {"far_leg": -6, "near_leg": 6, "far_arm": 9, "near_arm": -7}),
    ]),
    "windup": (False, [
        pose(65, {"torso": -4, "head": 5, "near_arm": -22}),
        pose(85, {"torso": -9, "head": 8, "near_arm": -57, "far_arm": -18}, {"torso": [-1, 1]}),
        pose(160, {"torso": -13, "head": 9, "near_arm": -105, "far_arm": -29},
             {"torso": [-2, 2]}),
        pose(50, {"torso": -4, "head": 0, "near_arm": -88, "far_arm": -32},
             {"torso": [-1, 0]}),
    ]),
    "recover": (False, [
        pose(82, {"torso": 15, "head": -5, "near_arm": -63, "far_arm": -28},
             {"torso": [3, 2], "near_leg": [2, 0]}),
        pose(104, {"torso": 12, "head": -4, "near_arm": -43, "far_arm": -18},
             {"torso": [2, 3], "near_leg": [1, 0]}),
        pose(124, {"torso": 5, "near_arm": -21}, {"torso": [1, 2]}),
        pose(210),
    ]),
    "hit": (False, [
        pose(60, {"torso": -16, "head": -11, "near_arm": 21, "far_arm": 24},
             {"torso": [-3, -1], "far_leg": [-2, -1]}),
        pose(85, {"torso": -12, "head": -3, "near_arm": 15, "far_arm": 14},
             {"torso": [-2, 1]}),
        pose(75, {"torso": -5, "head": 4, "near_arm": 8}, {"torso": [-1, 1]}),
        pose(70),
    ]),
    "collapse": (False, [
        pose(66, {"torso": -19, "head": -16, "near_arm": 23, "far_arm": 37},
             {"torso": [-4, -1], "far_leg": [-2, -2]}),
        pose(74, {"torso": -34, "head": -12, "near_arm": 17, "far_arm": 38,
                  "far_leg": -13, "near_leg": -23}, {"torso": [-3, 4]}),
        pose(75, {"torso": -61, "head": -12, "near_arm": 26, "far_arm": 44,
                  "far_leg": -47, "near_leg": -58}, {"torso": [0, 9], "far_leg": [0, 3]}),
        pose(75, {"torso": -81, "head": -3, "near_arm": 41, "far_arm": 43,
                  "far_leg": -75, "near_leg": -91}, {"torso": [5, 13], "far_leg": [1, 4], "near_leg": [5, 5]}),
        pose(270, {"torso": -87, "head": 1, "near_arm": 54, "far_arm": 60,
                   "far_leg": -84, "near_leg": -91}, {"torso": [5, 14], "far_leg": [2, 5], "near_leg": [5, 5]}),
    ]),
}


def prepare_originals():
    ORIGINALS.mkdir(parents=True, exist_ok=True)
    sources = {}
    for direction in DIRECTIONS:
        layers = artwork(direction == "back_right")
        original = Image.new("RGBA", CELL)
        for layer in layers.values():
            original.alpha_composite(layer)
        path = ORIGINALS / f"{direction}.png"
        original.save(path)
        sources[direction] = {"file": f"originals/{path.name}",
                              "sha256": sha256(path.read_bytes()).hexdigest()}
    write(ORIGINALS.parent / "source.json", {"version": 1, "origin": "Original pixel artwork",
                                           "files": sources})


def prepare_rigs():
    MATERIAL.mkdir(parents=True, exist_ok=True)
    views = []
    split_views = {}
    for direction in DIRECTIONS:
        source = ORIGINALS / f"{direction}.png"
        layer_art = artwork(direction == "back_right")
        with Image.open(source) as original:
            views.append({"direction": direction, "file": f"{direction}.png"})
            original.save(MATERIAL / f"{direction}.png")
            remaining = original.getchannel("A")
        split = {}
        for name, layer in reversed(layer_art.items()):
            mask = ImageChops.multiply(remaining, layer.getchannel("A"))
            split[name] = mask
            remaining = ImageChops.subtract(remaining, mask)
        parts = []
        for name, (pivot, parent, behind) in PARTS.items():
            mask_path = MATERIAL / f"{direction}_{name}.png"
            split[name].save(mask_path)
            entry = {"name": name, "mask": mask_path.name, "pivot": pivot, "behind_body": behind}
            if parent:
                entry["parent"] = parent
            parts.append(entry)
        write(MATERIAL / f"{direction}_parts.json", {
            "version": 1, "direction": direction, "parts": parts,
        })
        split_views[direction] = {"parts": {
            part["name"]: {"mask": part["mask"], "pivot": part["pivot"]} for part in parts
        }}
    views_file = MATERIAL / "views.json"
    write(views_file, {"version": 1, "cell": CELL, "pivot": GROUND, "views": views})
    order = [{"id": name, **({"parent": parent} if parent else {})}
             for name, (_, parent, _) in PARTS.items()]
    split_recipe = MATERIAL / "parts.json"
    repairs_recipe = MATERIAL / "repairs.json"
    write(split_recipe, {"version": 1, "parts": order, "views": split_views})
    write(repairs_recipe, {"version": 1, "views": {}})
    with TemporaryDirectory(dir=MATERIAL, prefix=".parts-") as directory:
        temporary = Path(directory)
        spritecut("parts", split_recipe, temporary / "observed", "--views", views_file)
        spritecut("parts-repair", temporary / "observed/index.json", repairs_recipe, temporary / "repaired")
        shutil.copytree(temporary / "repaired", MATERIAL / "parts", dirs_exist_ok=True)
    write(MATERIAL / "character.json", {
        "version": 1, "direction": "front_right", "views": "views.json", "parts": "parts/index.json",
    })


def sprite_frames(clips, destination=RUNTIME):
    lines = ['[gd_resource type="SpriteFrames" format=3]', '']
    atlases = []
    animations = []
    for name, clip in clips.items():
        lines.append(f'[ext_resource type="Texture2D" path="res://assets/actors/crypt_skeleton/'
                     f'{clip["maps"]["color"]}" id="{name}"]')
        frames = []
        for index, frame in enumerate(clip["frames"]):
            cel = f"{name}_{index}"
            rect = ", ".join(str(frame[key]) for key in ("x", "y", "w", "h"))
            atlases.extend(["", f'[sub_resource type="AtlasTexture" id="{cel}"]',
                            f'atlas = ExtResource("{name}")', f"region = Rect2({rect})"])
            frames.append(f'{{"duration": {frame["ms"] / 100}, "texture": SubResource("{cel}")}}')
        loop = str(clip["loop"]).lower()
        frame_list = ",\n".join(frames)
        animations.append(f'{{\n"frames": [{frame_list}],\n"loop": {loop},\n'
                          f'"name": &"{name}",\n"speed": 10.0\n}}')
    resource = ",\n".join(animations)
    (destination / "crypt_skeleton_frames.tres").write_text(
        "\n".join(lines + atlases + ["", "[resource]", f"animations = [{resource}]", ""]),
        encoding="utf-8",
    )


def bake():
    sheets = MOTION / "sheets"
    sheets.mkdir(parents=True, exist_ok=True)
    RUNTIME.mkdir(parents=True, exist_ok=True)
    clips = {}
    for direction in DIRECTIONS:
        parts = json.loads((MATERIAL / f"{direction}_parts.json").read_text(encoding="utf-8"))
        for part in parts["parts"]:
            part["mask"] = Path(os.path.relpath(MATERIAL / part["mask"], MOTION)).as_posix()
        parts["clips"] = {
            f"{name}_{direction}": {"loop": loop, "frames": frames}
            for name, (loop, frames) in CLIPS.items()
        }
        recipe = MOTION / f"{direction}.json"
        write(recipe, parts)
        with TemporaryDirectory(dir=MOTION, prefix=".bake-") as directory:
            temporary = Path(directory)
            spritecut("rig", MATERIAL / "views.json", recipe, temporary / "compiled")
            spritecut("bake", temporary / "compiled/recipe.json", temporary / "sheets")
            result = json.loads((temporary / "sheets/clips.json").read_text(encoding="utf-8"))
            for name, clip in result["clips"].items():
                for filename in clip["maps"].values():
                    shutil.copyfile(temporary / "sheets" / filename, sheets / filename)
                color = clip["maps"]["color"]
                shutil.copyfile(sheets / color, RUNTIME / color)
                clips[name] = clip
    write(sheets / "clips.json", {"version": 1, "cell": CELL, "pivot": GROUND, "clips": clips})
    sprite_frames(clips)


if __name__ == "__main__":
    if "--originals" in sys.argv:
        prepare_originals()
    else:
        prepare_rigs()
        bake()

"""Rebake the rear fall with the standing boot artwork planted through impact."""

import argparse
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
from PIL import Image, ImageDraw

from bake_combat_v002 import MATERIAL, compiler_character
from bake_combat_v004 import (
    LAYERS, VERSION as BASELINE, cells, pack, plane_recipe, read, read_frames, registered_landmarks,
)
from build_crypt_skeleton import GROUND, PROJECT, RUNTIME, spritecut, write


DIRECTION = "back_right"
CLIP = f"collapse_{DIRECTION}"
VERSION = BASELINE.with_name("v005")
SIDES = ("right", "left")
BOOTS = [f"{side}_boot" for side in SIDES]
FLOOR_LAYERS = ("left_leg", "right_leg", "body", "left_boot", "right_boot", "head")


def floor_materials(recipe, joints):
    size = tuple(recipe["cell"])
    padding = np.asarray(recipe["pivot"]) - GROUND
    spec = recipe["views"][DIRECTION]
    landmarks = registered_landmarks(spec, np.asarray(recipe["support"]))
    landmarks["soles"] = [np.asarray(joints[boot]["heel"]) + padding for boot in BOOTS]
    landmarks["planted_ankles"] = [np.asarray(joints[boot]["pivot"]) + padding for boot in BOOTS]

    parts = {}
    for part in LAYERS:
        if part in BOOTS:
            canvas = Image.new("RGBA", size)
            with Image.open(MATERIAL / "parts" / DIRECTION / f"{part}.png") as layer:
                canvas.paste(layer.convert("RGBA"), tuple(padding))
            parts[part] = canvas
        else:
            with Image.open(BASELINE / "contact-materials" / DIRECTION / f"{part}.png") as layer:
                parts[part] = layer.convert("RGBA")
    return parts, landmarks


def bake():
    recipe = read(BASELINE / "contact-poses.json")
    joints = read(MATERIAL / "joints.json")[DIRECTION]
    baseline = read(BASELINE / "sheets/clips.json")
    entry = read(BASELINE / "recipes" / f"entry_{DIRECTION}.json")
    for pose in entry["poses"]:
        pose["sole_targets"] = {side: {"offset_px": [0, 0], "angle_deg": 0} for side in SIDES}
        pose["contacts"] = BOOTS
    entry_path = VERSION / "recipes" / f"entry_{DIRECTION}.json"
    write(entry_path, entry)
    (VERSION / "sheets").mkdir(exist_ok=True)

    staging = PROJECT / ".local"
    staging.mkdir(exist_ok=True)
    with TemporaryDirectory(dir=staging, prefix="crypt-rear-plant-") as directory:
        work = Path(directory)
        character = compiler_character(DIRECTION, work)
        compiled, early = work / "compiled", work / "early"
        spritecut("animate", character, entry_path, compiled)
        spritecut("bake", compiled / "recipe.json", early)
        early_tracks = read(compiled / "tracks.json")["frames"]

        plane = work / "plane"
        plane.mkdir()
        parts, landmarks = floor_materials(recipe, joints)
        plane_path, floor_tracks = plane_recipe(
            parts, landmarks, recipe, recipe["views"][DIRECTION], plane, CLIP, layer_order=FLOOR_LAYERS,
        )
        late = work / "late"
        spritecut("bake", plane_path, late)
        clip = pack(CLIP, [read_frames(early, CLIP), read_frames(late, CLIP)], floor_tracks,
                    early_tracks, recipe, version=VERSION)

    clips = baseline["clips"].copy()
    front = clips["collapse_front_right"].copy()
    front["maps"] = {kind: f"../../{BASELINE.name}/sheets/{path}" for kind, path in front["maps"].items()}
    clips.update({CLIP: clip, "collapse_front_right": front})
    write(VERSION / "sheets/clips.json", {**baseline, "clips": clips})
    preview(baseline["clips"][CLIP], clip, parts)


def preview(before, after, parts):
    output = VERSION / "previews"
    output.mkdir(exist_ok=True)
    previous = cells(BASELINE / "sheets", before)
    current = cells(VERSION / "sheets", after)
    footprints = []
    for boot in BOOTS:
        alpha = np.asarray(parts[boot].getchannel("A"))
        rows, columns = np.where(alpha >= 192)
        bottom = rows.max()
        span = columns[rows == bottom]
        footprints.append((span.min(), span.max(), bottom))
    frames = []
    for old, new in zip(previous, current):
        panel = Image.new("RGBA", (192, 108), "#292334")
        pen = ImageDraw.Draw(panel)
        for x, label, sprite in ((0, "v004", old), (96, "v005", new)):
            pen.text((x + 4, 3), label, fill="#f3d2ba")
            pen.line((x + 10, 70, x + 85, 70), fill="#644c67")
            panel.alpha_composite(sprite, (x, 12))
            for first, last, bottom in footprints:
                pen.line((x + first, 14 + bottom, x + last, 14 + bottom), fill="#b1839e")
        frames.append(panel.convert("RGB").resize((768, 432), Image.Resampling.NEAREST))
    durations = [frame["ms"] for frame in after["frames"]]
    durations[-1] += 450
    frames[0].save(output / "rear-foot-comparison.gif", save_all=True, append_images=frames[1:],
                   duration=durations, disposal=2, loop=0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--publish", action="store_true")
    if parser.parse_args().publish:
        name = f"{CLIP}_color.png"
        shutil.copyfile(VERSION / "sheets" / name, RUNTIME / name)
    else:
        bake()


if __name__ == "__main__":
    main()

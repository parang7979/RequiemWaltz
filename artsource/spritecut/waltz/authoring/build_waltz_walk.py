"""Compile the two Waltz walk rigs and export their SpriteCut atlases."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory

from PIL import Image, ImageChops, ImageDraw


CHARACTER = Path(__file__).resolve().parents[1]
RIG_ROOT = CHARACTER / "materials/v004/rig"
VERSION = CHARACTER / "motions/walk/v001"
RUNTIME = CHARACTER.parents[2] / "assets/actors/waltz_walk"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def spritecut(*args):
    subprocess.run([sys.executable, "-m", "spritecut", *args], check=True)


def write_rig(direction, legs, settings, source, motion):
    name = "walk_" + direction
    parts, skins, tracks = [], [], {}
    with Image.open(source) as image:
        alpha = image.getchannel("A")
    for leg, settings_for_leg in legs.items():
        x0, y0, x1, y1 = settings_for_leg["rect"]
        mask = Image.new("L", tuple(settings["cell"]))
        ImageDraw.Draw(mask).rectangle((x0, y0, x1 - 1, y1 - 1), fill=255)
        mask_path = RIG_ROOT / f"{direction}_{leg}.png"
        ImageChops.multiply(mask, alpha).save(mask_path)
        parts.append({"name": leg, "mask": mask_path.name, "pivot": settings_for_leg["pivot"],
                      "behind_body": True})
        skins.append({"parts": [leg], "bands_y": [settings_for_leg["band"]], "spacing": 1})
        tracks[leg + "_sole"] = {"part": leg, "point": settings_for_leg["sole"]}

    depth = motion["depth_per_x"][direction]
    poses = []
    for key in motion["frames"]:
        translations, angles = {}, {}
        for leg in ("near", "far"):
            x, y, angle = key[leg]
            translations[leg + "_leg"] = [x, round(y + depth * x, 3)]
            angles[leg + "_leg"] = angle
        poses.append({"ms": key["ms"], "offset": [0, key["body_y"]], "translations": translations,
                      "angles": angles, "contacts": [leg + "_leg" for leg in key["ground"]]})

    path = RIG_ROOT / f"{direction}.json"
    write(path, {"version": 1, "direction": direction, "parts": parts, "skins": skins,
                 "clips": {name: {"cycle_advance_px": 0, "loop": motion["loop"], "frames": poses}}})
    tracks_path = RIG_ROOT / f"{direction}_tracks.json"
    write(tracks_path, {"tracks": tracks})
    return name, path, tracks_path


def main():
    setup = read(RIG_ROOT / "legs.json")
    motion = read(VERSION / "motion.json")
    views, sources = [], {}
    for direction in setup["views"]:
        source = (RIG_ROOT / setup["source"] / f"waltz_{direction}.png").resolve()
        views.append({"direction": direction, "file": Path(os.path.relpath(source, RIG_ROOT)).as_posix()})
        sources[direction] = source
    registered = RIG_ROOT / "views.json"
    header = {"version": 1, "cell": setup["cell"], "pivot": setup["pivot"]}
    write(registered, {**header, "views": views})

    sheets = VERSION / "sheets"
    sheets.mkdir(exist_ok=True)
    RUNTIME.mkdir(parents=True, exist_ok=True)
    clips = {}
    with TemporaryDirectory(dir=VERSION, prefix=".waltz-walk-") as work:
        for direction, source in sources.items():
            name, rig, tracks = write_rig(direction, setup["views"][direction], setup, source, motion)
            compiled = Path(work) / direction / "compiled"
            baked = Path(work) / direction / "sheets"
            spritecut("rig", registered, rig, compiled, "--motion", tracks)
            spritecut("bake", compiled / "recipe.json", baked)
            shutil.copytree(compiled, VERSION / "compiled" / direction, dirs_exist_ok=True)
            manifest = read(baked / "clips.json")
            clip = manifest["clips"][name]
            for filename in clip["maps"].values():
                shutil.copyfile(baked / filename, sheets / filename)
                shutil.copyfile(baked / filename, RUNTIME / filename)
            clips[name] = clip
    manifest = {**header, "clips": clips}
    write(sheets / "clips.json", manifest)
    write(RUNTIME / "clips.json", manifest)


if __name__ == "__main__":
    main()

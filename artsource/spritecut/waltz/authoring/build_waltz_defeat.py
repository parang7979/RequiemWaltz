"""Bake Waltz's seated collapse and Requiem's return to his original form."""

import os
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory

from PIL import Image, ImageChops, ImageDraw

from build_waltz_reactions import RIG as UPPER_RIG, SOURCE, make_pose, paint_reaction_details
from build_waltz_walk import CHARACTER, RIG_ROOT as LEG_RIG, read, spritecut, write


VERSION = CHARACTER / "motions/defeat/v001"
RIG = VERSION / "rig"
PROJECT = CHARACTER.parents[2]
RUNTIME = PROJECT / "assets/actors/waltz_defeat"


def relative(path):
    return Path(os.path.relpath(path, RIG)).as_posix()


def waltz_rig(direction, recipe):
    upper = read(UPPER_RIG / f"{direction}.json")
    legs = read(LEG_RIG / "legs.json")["views"][direction]
    parts = [{**part, "mask": relative(UPPER_RIG / part["mask"])} for part in upper["parts"]]
    skins = list(upper["skins"])
    for name, leg in legs.items():
        parts.append({"name": name, "mask": relative(LEG_RIG / f"{direction}_{name}.png"),
                      "pivot": leg["pivot"], "parent": "torso", "behind_body": True})
        skins.append({"parts": [name], "bands_y": [leg["band"]], "spacing": 1})
    frames = []
    for key in recipe["collapse"]:
        pose = make_pose(key, direction)
        leg_keys = key.get("views", {}).get(direction, {}).get("legs", key["legs"])
        for name, values in zip(("near_leg", "far_leg"), leg_keys):
            pose["translations"][name] = values[:2]
            pose["angles"][name] = values[2]
        frames.append(pose)
    return {"version": 1, "direction": direction, "parts": parts, "skins": skins,
            "clips": {f"collapse_{direction}": {"loop": False, "frames": frames}}}


def requiem_rig(recipe):
    spec = recipe["requiem"]
    with Image.open(PROJECT / "assets/waltz_combat/requiem.png") as source:
        sprite = source.convert("RGBA")
    draw = ImageDraw.Draw(sprite)
    for rect in spec["star_rects"]:
        draw.rectangle(tuple(rect), fill=(0, 0, 0, 0))
    draw.polygon([tuple(point) for point in spec["old_tail"]], fill=(0, 0, 0, 0))
    for polygon in spec["face"]:
        draw.polygon([tuple(point) for point in polygon["points"]], fill=polygon["color"])
    sprite.save(RIG / "requiem.png")
    alpha = sprite.getchannel("A")
    assigned = Image.new("L", sprite.size)
    for name, part in reversed(list(spec["parts"].items())):
        mask = Image.new("L", sprite.size)
        ImageDraw.Draw(mask).polygon([tuple(point) for point in part["polygon"]], fill=255)
        mask = ImageChops.subtract(mask, assigned)
        assigned = ImageChops.lighter(assigned, mask)
        ImageChops.multiply(alpha, mask).save(RIG / f"requiem_{name}.png")
    parts = [{"name": name, "mask": f"requiem_{name}.png", "pivot": part["pivot"]}
             for name, part in spec["parts"].items()]
    frames = [
        {"ms": key["ms"], "translations": {name: value[:2] for name, value in key["parts"].items()},
         "angles": {name: value[2] for name, value in key["parts"].items()}}
        for key in spec["frames"]
    ]
    views = {"version": 1, "cell": list(sprite.size), "pivot": spec["pivot"],
             "views": [{"direction": "front", "file": "requiem.png"}]}
    rig = {"version": 1, "direction": "front", "parts": parts,
           "clips": {"requiem_concern": {"loop": False, "frames": frames}}}
    return views, rig


def main():
    recipe = read(VERSION / "motion.json")
    setup = read(UPPER_RIG / "upper-body.json")
    RIG.mkdir(parents=True, exist_ok=True)
    header = {"version": 1, "cell": setup["cell"], "pivot": setup["pivot"]}
    waltz_views = RIG / "waltz_views.json"
    write(waltz_views, {**header, "views": [
        {"direction": direction, "file": relative(SOURCE / f"waltz_{direction}.png")}
        for direction in setup["views"]
    ]})
    jobs = {direction: (waltz_views, waltz_rig(direction, recipe), setup["pivot"])
            for direction in setup["views"]}
    spirit_views, spirit_rig = requiem_rig(recipe)
    write(RIG / "requiem_views.json", spirit_views)
    jobs["requiem"] = (RIG / "requiem_views.json", spirit_rig, spirit_views["pivot"])
    sheets = VERSION / "sheets"
    sheets.mkdir(exist_ok=True)
    RUNTIME.mkdir(parents=True, exist_ok=True)
    clips = {}
    with TemporaryDirectory(prefix="waltz-defeat-") as temp:
        for actor, (views, payload, pivot) in jobs.items():
            rig = RIG / f"{actor}.json"
            write(rig, payload)
            compiled = Path(temp) / actor / "compiled"
            baked = Path(temp) / actor / "baked"
            spritecut("rig", views, rig, compiled)
            spritecut("bake", compiled / "recipe.json", baked)
            shutil.copytree(compiled, VERSION / "compiled" / actor, dirs_exist_ok=True)
            for name, clip in read(baked / "clips.json")["clips"].items():
                details = recipe.get("details", {}).get(name)
                if details:
                    paint_reaction_details(baked, clip, details)
                clip["pivot"] = pivot
                for filename in clip["maps"].values():
                    shutil.copyfile(baked / filename, sheets / filename)
                    shutil.copyfile(baked / filename, RUNTIME / filename)
                clips[name] = clip
    waltz_clips = {name: clip for name, clip in clips.items() if name.startswith("collapse_")}
    write(sheets / "clips.json", {**header, "clips": waltz_clips})
    spirit_header = {key: spirit_views[key] for key in ("version", "cell", "pivot")}
    write(sheets / "requiem-clips.json", {**spirit_header, "clips": {"requiem_concern": clips["requiem_concern"]}})
    write(RUNTIME / "clips.json", {"version": 1, "clips": clips})


if __name__ == "__main__":
    main()

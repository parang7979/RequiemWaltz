"""Bake Waltz's directional upper-body reactions while retaining her walk legs."""

import argparse
import os
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory

from PIL import Image, ImageChops, ImageColor, ImageDraw

from build_waltz_walk import CHARACTER, read, spritecut, write


RIG = CHARACTER / "materials/v005/rig"
SOURCE = CHARACTER / "materials/v003/prepared"
MOTIONS = CHARACTER / "motions/upper_reactions"
RUNTIME = CHARACTER.parents[2] / "assets/actors/waltz_reactions"
REVISIONS = ("v001", "v002", "v003", "v004")


def make_parts(direction, parts, alpha):
    assigned = Image.new("L", alpha.size)
    masks = {}
    for name, spec in parts.items():
        if name == "torso":
            continue
        mask = Image.new("L", alpha.size)
        ImageDraw.Draw(mask).polygon([tuple(point) for point in spec["polygon"]], fill=255)
        mask = ImageChops.multiply(ImageChops.subtract(mask, assigned), alpha)
        assigned = ImageChops.lighter(assigned, mask)
        masks[name] = mask
    masks["torso"] = ImageChops.subtract(alpha, assigned)
    layers, skins = [], []
    for name, spec in parts.items():
        path = RIG / f"{direction}_{name}.png"
        masks[name].save(path)
        layer = {"name": name, "mask": path.name, "pivot": spec["pivot"]}
        if name != "torso":
            layer["parent"] = "torso"
        layers.append(layer)
        if "band" in spec:
            skins.append({"parts": [name], "bands_y": [spec["band"]], "spacing": 1})
    return layers, skins


def make_pose(key, direction):
    key = {**key, **key.get("views", {}).get(direction, {})}
    channels = {"torso": key["torso"], "head": key["head"]}
    near_sign = 1 if direction == "front_right" else -1
    px, py, turn = key["near"]
    channels["near_hand"] = [near_sign * px, py, near_sign * turn]
    if direction == "front_right":
        px, py, turn = key["far"]
        channels["far_hand"] = [-px, py, turn]
    return {"ms": key["ms"], "translations": {part: value[:2] for part, value in channels.items()},
            "angles": {part: value[2] for part, value in channels.items()}}


def paint_reaction_details(baked, clip, details):
    """Paint grip and expression cels at their baked pixel positions."""
    color_path = baked / clip["maps"]["color"]
    normal_path = baked / clip["maps"]["normal"]
    with Image.open(color_path) as sheet, Image.open(normal_path) as normals:
        color = sheet.convert("RGBA")
        normal = normals.convert("RGBA")
    for frame_number, key in details.items():
        frame = clip["frames"][int(frame_number)]
        origin = (frame["x"], frame["y"])
        for x, y, width, height in key.get("clear_rects", []):
            left, top = origin[0] + x, origin[1] + y
            box = (left, top, left + width, top + height)
            color.paste((0, 0, 0, 0), box)
            normal.paste((0, 0, 0, 0), box)
        source = color.crop((*origin, origin[0] + frame["w"], origin[1] + frame["h"]))
        cel = Image.new("RGBA", (frame["w"], frame["h"]))
        paint = ImageDraw.Draw(cel)
        for eye in key.get("closed_eyes", []):
            x, y = eye["iris"]
            # Lift out the pupil with adjacent cheek colors. Place the eyelid on
            # the original socket line, stepping up where the face turns away.
            cheek_left = source.getpixel((x - 1, y + 1))
            cheek_right = source.getpixel((x + 1, y + 1))
            cheek = tuple((left + right) // 2 for left, right in zip(cheek_left, cheek_right))
            paint.point((x, y + 1), fill=cheek)
            for [lid_x, lid_y], opacity in zip(eye["lid"], (0.50, 0.78, 0.44)):
                edge = source.getpixel((lid_x + 1, lid_y - 1))
                shade = ImageColor.getrgb("#784d61")
                pixel = tuple(round(sample * (1 - opacity) + pigment * opacity)
                              for sample, pigment in zip(edge[:3], shade))
                paint.point((lid_x, lid_y), fill=(*pixel, 255))
        for eye in key.get("peeking_eyes", []):
            x, y = eye["iris"]
            pupil_x, pupil_y = eye["pupil"]
            # Narrow the opening along the existing socket, leaving one iris
            # pixel toward the edge of the hood.
            left = source.getpixel((x - 1, y + 1))
            right = source.getpixel((x + 1, y + 1))
            cheek = tuple((a + b) // 2 for a, b in zip(left, right))
            brow = source.getpixel((x - 1, y - 1))
            shade = (120, 75, 92)
            lid = tuple((a + b) // 2 for a, b in zip(brow[:3], shade))
            paint.point((x, y + 1), fill=cheek)
            paint.point((x, y), fill=(*lid, 255))
            paint.point((pupil_x, pupil_y), fill="#92546a")
        for x, y, elbow_x, elbow_y in key.get("grips", []):
            # Let the darker sleeve fold merge back into the cloak at the elbow.
            sleeve = [(elbow_x, elbow_y), ((x + elbow_x) // 2, y + 3), (x, y + 1)]
            paint.line(sleeve, fill=(83, 37, 62, 195), width=4)
            paint.line(sleeve, fill=(133, 51, 76, 215), width=2)
            paint.point((x, y + 2), fill="#9b645e")
            paint.point((x - 1, y + 1), fill="#8e5661")
            paint.point((x, y + 1), fill="#bc8b79")
            paint.point((x - 1, y), fill="#bb8f7e")
            paint.point((x, y), fill="#dcb29a")
            paint.point((x + 1, y), fill="#ab7b72")
            paint.point((x, y - 1), fill="#c29680")
        for x, y, pigment in key.get("points", []):
            paint.point((x, y), fill=pigment)
        for shadow in key.get("face_shadows", []):
            mask = Image.new("L", cel.size)
            ImageDraw.Draw(mask).polygon([tuple(point) for point in shadow["polygon"]], fill=255)
            shade = Image.new("RGBA", cel.size, shadow["color"])
            shade = Image.blend(source, shade, shadow["opacity"])
            shade.putalpha(ImageChops.multiply(mask, source.getchannel("A")))
            cel.alpha_composite(shade)
        color.alpha_composite(cel, origin)
        flat = Image.new("RGBA", cel.size, (128, 128, 255, 255))
        flat.putalpha(cel.getchannel("A"))
        normal.alpha_composite(flat, origin)
    color.save(color_path)
    normal.save(normal_path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", choices=REVISIONS, default=REVISIONS[-1])
    revision = parser.parse_args().revision
    version = MOTIONS / revision
    publish = revision == REVISIONS[-1]
    rig = read(RIG / "upper-body.json")
    motions = {}
    details = {}
    for source in REVISIONS[:REVISIONS.index(revision) + 1]:
        recipe = read(MOTIONS / source / "motion.json")
        motions.update(recipe["clips"])
        if "hood_details" in recipe:
            details["hood_grab"] = recipe["hood_details"]
        details.update(recipe.get("details", {}))
    index = {"version": 1, "cell": rig["cell"], "pivot": rig["pivot"]}
    views = []
    sheets = version / "sheets"
    sheets.mkdir(exist_ok=True)
    if publish:
        RUNTIME.mkdir(parents=True, exist_ok=True)
    for direction, parts in rig["views"].items():
        with Image.open(SOURCE / f"waltz_{direction}.png") as original:
            upper = Image.new("RGBA", original.size)
            upper.paste(original.crop((0, 0, original.width, rig["hem_row"])), (0, 0))
        file = RIG / f"{direction}_upper.png"
        upper.save(file)
        views.append({"direction": direction, "file": file.name})
        layers, skins = make_parts(direction, parts, upper.getchannel("A"))
        clips = {f"{name}_{direction}": {"loop": False, "frames": [make_pose(key, direction) for key in poses]}
                 for name, poses in motions.items()}
        recipe_dir = RIG if revision == "v001" else version / "rig"
        for layer in layers:
            layer["mask"] = Path(os.path.relpath(RIG / layer["mask"], recipe_dir)).as_posix()
        write(recipe_dir / f"{direction}.json", {"version": 1, "direction": direction,
                                                 "parts": layers, "skins": skins, "clips": clips})
    registered = RIG / "views.json"
    write(registered, {**index, "views": views})

    clips = {}
    with TemporaryDirectory(dir=version, prefix=".waltz-reactions-") as work:
        for direction in rig["views"]:
            compiled = Path(work) / direction / "compiled"
            baked = Path(work) / direction / "sheets"
            spritecut("rig", registered, recipe_dir / f"{direction}.json", compiled)
            spritecut("bake", compiled / "recipe.json", baked)
            shutil.copytree(compiled, version / "compiled" / direction, dirs_exist_ok=True)
            for name, clip in read(baked / "clips.json")["clips"].items():
                motion = name.removesuffix("_" + direction)
                if motion in details:
                    paint_reaction_details(baked, clip, details[motion][direction])
                for filename in clip["maps"].values():
                    shutil.copyfile(baked / filename, sheets / filename)
                    if publish:
                        shutil.copyfile(baked / filename, RUNTIME / filename)
                clips[name] = clip
    manifest = {**index, "clips": clips, "hem_row": rig["hem_row"]}
    write(sheets / "clips.json", manifest)
    if publish:
        write(RUNTIME / "clips.json", manifest)


if __name__ == "__main__":
    main()

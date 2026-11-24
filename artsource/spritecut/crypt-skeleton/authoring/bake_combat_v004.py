"""Bake a planted backward fall from separately registered face-up surfaces."""

import argparse
import json
import math
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
from PIL import Image, ImageChops, ImageDraw

from bake_combat_v002 import MATERIAL, compiler_character, falling
from build_crypt_skeleton import DIRECTIONS, PROJECT, ROOT, RUNTIME, sprite_frames, spritecut, write


BASELINE = ROOT / "motions/combat/v003"
VERSION = ROOT / "motions/combat/v004"
SOURCE = ROOT / "sources/v003/originals/supine-contact.png"
EARLY_FRAMES = 4
LAYERS = ("left_leg", "right_leg", "left_boot", "right_boot", "body", "head")


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def screen_turn(degrees):
    angle = math.radians(degrees)
    cosine, sine = math.cos(angle), math.sin(angle)
    return np.array([[cosine, -sine], [sine, cosine]])


def unit(vector):
    return vector / np.linalg.norm(vector)


def register(direction, spec, size, support):
    crop = spec["crop"]
    scale = spec["scale"]
    feet = np.mean(spec["soles"], axis=0)
    origin = (np.asarray(crop[:2]) - feet) * scale + support
    with Image.open(SOURCE) as original:
        artwork = original.crop(crop).convert("RGBA")
    alpha = artwork.getchannel("A").point(lambda a: a if a >= 16 else 0)
    artwork.putalpha(alpha)
    owner = Image.new("L", artwork.size, 0)
    marks = ImageDraw.Draw(owner)
    assignment = ("left_leg", "right_leg", "left_boot", "right_boot", "head")
    for number, name in enumerate(assignment, 1):
        outline = [(x - crop[0], y - crop[1]) for x, y in spec["polygons"][name]]
        marks.polygon(outline, fill=number)
    width, height = (round(side * scale * 4) for side in artwork.size)
    registered = {}
    for number, name in enumerate(("body", *assignment)):
        matte = owner.point(lambda value: 255 if value == number else 0)
        part = artwork.copy()
        part.putalpha(ImageChops.multiply(alpha, matte))
        supersampled = Image.new("RGBA", (4 * size[0], 4 * size[1]))
        supersampled.paste(part.resize((width, height), Image.Resampling.LANCZOS),
                           tuple(round(value * 4) for value in origin))
        native = supersampled.resize(size, Image.Resampling.LANCZOS)
        native.putalpha(native.getchannel("A").point(lambda a: a if a >= 22 else 0))
        registered[name] = native
    output = VERSION / "contact-materials" / direction
    output.mkdir(parents=True, exist_ok=True)
    for name, layer in registered.items():
        layer.save(output / f"{name}.png")
    return registered, registered_landmarks(spec, support)


def registered_landmarks(spec, support):
    feet = np.mean(spec["soles"], axis=0)

    def point(source):
        return (np.asarray(source) - feet) * spec["scale"] + support

    return {
        "support": support,
        "soles": [point(mark) for mark in spec["soles"]],
        "ankles": [point(mark) for mark in spec["ankles"]],
        "hips": [point(mark) for mark in spec["hips"]],
        "neck": point(spec["neck"]),
        "crown": point(spec["axis_tip"]),
    }


def map_limb(vertices, start, end, posed, *, posed_start=None):
    """Place the original leg between its fixed ankle and its posed hip."""
    before = unit(end - start)
    if posed_start is None:
        posed_start = start
    span = posed - posed_start
    after = unit(span)
    before_perp = np.array([-before[1], before[0]])
    after_perp = np.array([-after[1], after[0]])
    offset = vertices - start
    along = np.outer(offset @ before, span / np.linalg.norm(end - start))
    across = np.outer(offset @ before_perp, after_perp)
    return posed_start + along + across


def entry_poses(baseline, recipe, landmarks, joints):
    """Guide the standing boots into the two registered support marks."""
    initial = []
    padding = np.asarray(recipe["pivot"]) - [32, 58]
    for index, (key, duration) in enumerate(zip(baseline["poses"][:EARLY_FRAMES], recipe["durations_ms"])):
        if index < 2:
            initial.append({**key, "ms": duration})
            continue
        feet = []
        for side, contact in zip(("right", "left"), landmarks["soles"]):
            boot = joints[side + "_boot"]
            center = np.mean([boot["heel"], boot["toe"]], axis=0)
            target = key["sole_targets"][side]
            angle = target["angle_deg"]
            old = center + target["offset_px"]
            sole = contact - padding + screen_turn(angle) @ (center - boot["heel"])
            position = old + (sole - old) * (0.35 if index == 2 else 1.0)
            feet.append((*position, angle))
        frame = falling(duration, key["angles"], key["translations"]["pelvis"], *feet, joints)
        if index == EARLY_FRAMES - 1:
            frame["contacts"] = ["right_boot", "left_boot"]
        initial.append(frame)
    return initial


def plane_recipe(part_images, landmarks, recipe, spec, work, name, *, layer_order=LAYERS):
    size = tuple(recipe["cell"])
    width, height = size
    atlas = Image.new("RGBA", (width * len(layer_order), height))
    quads, uv, triangles = {}, [], []
    for index, part in enumerate(layer_order):
        layer = part_images[part]
        atlas.paste(layer, (width * index, 0))
        x0, y0, x1, y1 = layer.getchannel("A").getbbox()
        quads[part] = np.array([[x0, y0], [x1, y0], [x1, y1], [x0, y1]], dtype=float)
        uv.extend((quads[part] + [width * index, 0]).tolist())
        start = index * 4
        triangles.extend([[start, start + 1, start + 2], [start, start + 2, start + 3]])
    atlas.save(work / "surfaces.png")
    support = landmarks["support"]
    axis = unit(landmarks["crown"] - support)
    planted_ankles = landmarks.get("planted_ankles", landmarks["ankles"])
    local = recipe["durations_ms"][EARLY_FRAMES:]
    frames, tracks = [], []
    for index, ms in enumerate(local):
        rotation = screen_turn(spec["roll"][index])
        scale = np.eye(2) + (recipe["depth_scales"][index] - 1) * np.outer(axis, axis)
        projection = rotation @ scale

        def torso(vertices):
            return support + (vertices - support) @ projection.T + spec["body_offsets"][index]

        neck = torso(landmarks["neck"])
        head_turn = screen_turn(spec["roll"][index] + recipe["head_turns"][index])
        head_at = neck + [0, spec["head_offsets"][index]]
        posed = {**quads, "body": torso(quads["body"]),
                 "head": head_at + (quads["head"] - landmarks["neck"]) @ head_turn.T}
        for side, ankle, hip, fixed_ankle in zip(("right", "left"), landmarks["ankles"],
                                               landmarks["hips"], planted_ankles):
            part = side + "_leg"
            posed[part] = map_limb(quads[part], ankle, hip, torso(hip), posed_start=fixed_ankle)
        vertices = np.concatenate([posed[part] for part in layer_order])
        frames.append({"ms": ms, "vertices": vertices.tolist(), "contacts": ["right_boot", "left_boot"]})
        points = {
            "right_foot": landmarks["soles"][0].tolist(),
            "left_foot": landmarks["soles"][1].tolist(),
            "support": support.tolist(),
            "neck": neck.tolist(),
            "head": head_at.tolist(),
            "crown": (head_at + (landmarks["crown"] - landmarks["neck"]) @ head_turn.T).tolist(),
        }
        tracks.append({"ms": ms, "contacts": ["right_boot", "left_boot"], "points": points,
                       "upper_scale": recipe["depth_scales"][index], "roll_deg": spec["roll"][index]})
    path = work / "recipe.json"
    write(path, {"version": 1, "cell": size, "pivot": recipe["pivot"],
                 "materials": {"color": "surfaces.png"}, "uv": uv, "triangles": triangles,
                 "clips": {name: {"frames": frames, "loop": False}}})
    return path, tracks


def read_frames(directory, name):
    clip = read(directory / "clips.json")["clips"][name]
    materials = {}
    for key, filename in clip["maps"].items():
        with Image.open(directory / filename) as sheet:
            materials[key] = [
                sheet.crop((f["x"], f["y"], f["x"] + f["w"], f["y"] + f["h"])).convert("RGBA")
                for f in clip["frames"]
            ]
    return materials


def pack(name, phases, floor_tracks, early_tracks, recipe, *, version=VERSION):
    size = tuple(recipe["cell"])
    width, height = size
    pivot = np.asarray(recipe["pivot"])
    delta = pivot - [32, 58]
    count = len(recipe["durations_ms"])
    sheets = version / "sheets"
    maps = {}
    for material in ("color", "normal", "emissive"):
        atlas = Image.new("RGBA", (width * count, height))
        early, late = (phase[material] for phase in phases)
        for index, frame in enumerate(early + late):
            x, y = (index * width + int(delta[0]), int(delta[1])) if index < len(early) else (index * width, 0)
            atlas.paste(frame, (x, y))
        filename = f"{name}_{material}.png"
        atlas.save(sheets / filename)
        maps[material] = filename
    frames = [{"ms": ms, "x": index * width, "y": 0, "w": width, "h": height,
               "contacts": track["contacts"]}
              for index, (ms, track) in enumerate(zip(recipe["durations_ms"], early_tracks + floor_tracks))]
    shifted = [{"ms": ms, "contacts": original["contacts"], "points": {
        part: (point + delta).tolist() for part, point in original["points"].items()
    }} for ms, original in zip(recipe["durations_ms"], early_tracks)]
    write(version / "tracks" / f"{name}.json", {
        "version": 1, "cell": size, "pivot": recipe["pivot"], "direction": name.removeprefix("collapse_"),
        "frames": shifted + floor_tracks,
    })
    return {"cell": size, "pivot": recipe["pivot"], "maps": maps, "loop": False,
            "cycle_advance_px": 0, "frames": frames}


def bake():
    recipe = read(VERSION / "contact-poses.json")
    for folder in ("sheets", "tracks", "recipes", "previews"):
        (VERSION / folder).mkdir(exist_ok=True)
    baseline = read(BASELINE / "sheets/clips.json")
    joints = read(MATERIAL / "joints.json")
    staging = PROJECT / ".local"
    staging.mkdir(exist_ok=True)
    clips = {}
    with TemporaryDirectory(dir=staging, prefix="crypt-contact-") as directory:
        work = Path(directory)
        for direction in DIRECTIONS:
            name = "collapse_" + direction
            spec = recipe["views"][direction]
            parts, landmarks = register(direction, spec, tuple(recipe["cell"]), np.asarray(recipe["support"]))
            original = read(BASELINE / "recipes" / f"{name}.json")
            early_recipe = VERSION / "recipes" / f"entry_{direction}.json"
            write(early_recipe, {**original, "poses": entry_poses(original, recipe, landmarks, joints[direction])})
            character = compiler_character(direction, work)
            compiled = work / f"entry_{direction}"
            early = work / f"early_{direction}"
            spritecut("animate", character, early_recipe, compiled)
            spritecut("bake", compiled / "recipe.json", early)
            early_tracks = read(compiled / "tracks.json")["frames"]

            plane = work / f"plane_{direction}"
            plane.mkdir()
            plane_file, tracks = plane_recipe(parts, landmarks, recipe, spec, plane, name)
            late = work / f"late_{direction}"
            spritecut("bake", plane_file, late)
            clips[name] = pack(name, [read_frames(early, name), read_frames(late, name)],
                               tracks, early_tracks, recipe)
    catalog = {**baseline["clips"], **clips}
    write(VERSION / "sheets/clips.json", {**baseline, "clips": catalog})
    return baseline, clips


def cells(directory, clip):
    with Image.open(directory / clip["maps"]["color"]) as image:
        return [image.crop((f["x"], f["y"], f["x"] + f["w"], f["y"] + f["h"])).convert("RGBA")
                for f in clip["frames"]]


def preview(baseline, clips):
    images = []
    new = [cells(VERSION / "sheets", clip) for clip in clips.values()]
    old = [cells(BASELINE / "sheets", baseline["clips"][name]) for name in clips]
    old_times = [f["ms"] for f in baseline["clips"]["collapse_front_right"]["frames"]]
    durations = [f["ms"] for f in clips["collapse_front_right"]["frames"]]
    timeline = sorted(set(np.cumsum([0, *old_times]).tolist() + np.cumsum([0, *durations]).tolist()))
    for time in timeline[:-1]:
        before = np.searchsorted(np.cumsum(old_times), time, side="right")
        after = np.searchsorted(np.cumsum(durations), time, side="right")
        frame = Image.new("RGBA", (204, 206), "#2c2337")
        pen = ImageDraw.Draw(frame)
        pen.text((7, 3), "v003  |  front / rear", fill="#e1c7b1")
        pen.text((7, 92), "v004  |  front / rear", fill="#e1c7b1")
        for col in range(2):
            x = 4 + col * 102
            pen.line((x, 72, x + 96, 72), fill="#6c546e")
            pen.line((x, 162, x + 96, 162), fill="#6c546e")
            frame.alpha_composite(old[col][before], (x + 16, 14))
            frame.alpha_composite(new[col][after], (x, 104))
        images.append(frame.convert("RGB").resize((612, 618), Image.Resampling.NEAREST))
    delays = np.diff(timeline).tolist()
    delays[-1] += 360
    previews = VERSION / "previews"
    images[0].save(previews / "fall-comparison.gif", save_all=True, append_images=images[1:],
                   duration=delays, loop=0, disposal=2)
    images[-1].save(previews / "ground-contact.png")
    panel = Image.new("RGBA", (6 * 100, 2 * 110), "#2c2337")
    pen = ImageDraw.Draw(panel)
    for row, frames in enumerate(new):
        for column, index in enumerate((0, 3, 4, 6, 8, 11)):
            x, y = 100 * column, 110 * row
            pen.text((x + 7, y + 1), f"{index + 1:02d}", fill="#e1c7b1")
            pen.line((x, y + 68, x + 96, y + 68), fill="#6c546e")
            panel.alpha_composite(frames[index], (x, y + 10))
    panel.convert("RGB").resize((1200, 440), Image.Resampling.NEAREST).save(previews / "pose-sheet-2x.png")


def publish(version=VERSION):
    sheets = version / "sheets"
    clips = read(sheets / "clips.json")["clips"]
    for direction in DIRECTIONS:
        clip = clips["collapse_" + direction]
        color = clip["maps"]["color"]
        shutil.copyfile(sheets / color, RUNTIME / color)
    for clip in clips.values():
        clip["maps"] = {kind: Path(path).name for kind, path in clip["maps"].items()}
    sprite_frames(clips)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--publish", action="store_true", help="apply the verified fall and timing to Godot")
    args = parser.parse_args()
    if args.publish:
        publish()
    else:
        preview(*bake())


if __name__ == "__main__":
    main()

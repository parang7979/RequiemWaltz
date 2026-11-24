"""Bake the new crypt skeleton's walk, strike, recoil and collapse."""

import argparse
import json
import math
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image, ImageDraw

from build_crypt_skeleton import CELL, DIRECTIONS, GROUND, PROJECT, ROOT, RUNTIME, sprite_frames, spritecut, write


MATERIAL = ROOT / "materials/v002"
VERSION = ROOT / "motions/combat/v002"
CLIP_NAMES = ("idle", "walk", "windup", "recover", "hit", "collapse")
GROUNDED = ["right_boot", "left_boot"]


def pose(ms, angles=None, translations=None, contacts=GROUNDED, feet=None):
    frame = {"ms": ms, "angles": angles or {}, "translations": translations or {}, "contacts": contacts}
    if feet is not None:
        frame["sole_targets"] = {
            side: {"offset_px": [x, y], "angle_deg": turn} for side, (x, y, turn) in feet.items()
        }
    return frame


def walk(back):
    travel = (
        (3.5, 0.0, 3), (1.8, 0.0, 0), (0.0, 0.0, 0), (-1.8, 0.0, 0),
        (-3.5, 0.0, -4), (-3.0, 1.6, -8), (-0.1, 3.0, -5), (2.6, 1.5, 6),
    )
    depth = -0.33 if back else 0.30
    projected_stride = 0.73 if back else 1.0
    poses = []
    for index in range(len(travel)):
        other = (index + 4) % len(travel)
        right_x, right_lift, right_tilt = travel[index]
        left_x, left_lift, left_tilt = travel[other]
        feet = {
            "right": (round(right_x * projected_stride, 2),
                      round(right_x * projected_stride * depth - right_lift, 2), right_tilt),
            "left": (round(left_x * projected_stride, 2),
                     round(left_x * projected_stride * depth - left_lift, 2), left_tilt),
        }
        contacts = [f"{side}_boot" for side, tick in (("right", index), ("left", other)) if tick < 5]
        sway = (right_x - left_x) / 2
        body_height = (2.0, 1.8, 1.2, 1.4)[index % 4] + (0.9 if back else 0.0)
        poses.append(pose(55, {
            "chest": round(sway * -1.3, 2),
            "head": round(sway * 0.9, 2),
            "right_upper_arm": round(sway * 5.0, 2),
            "left_upper_arm": round(sway * -4.0, 2),
            "right_forearm": round(sway * 1.9, 2),
            "left_forearm": round(sway * -1.5, 2),
            "cloth": round(sway * -2.3, 2),
        }, {"pelvis": [0, body_height]}, contacts, feet))
    return poses


def braced(ms, body, chest, head, arm, elbow, far_arm, cloth, lead=0):
    return pose(ms, {
        "chest": chest, "head": head, "right_upper_arm": arm,
        "right_forearm": elbow, "left_upper_arm": far_arm, "cloth": cloth,
    }, {"pelvis": body}, feet={"right": (lead, 0, 0), "left": (0, 0, 0)})


def rotate(vector, degrees):
    x, y = vector
    radians = math.radians(degrees)
    cosine, sine = math.cos(radians), math.sin(radians)
    return x * cosine - y * sine, x * sine + y * cosine


def falling(ms, angles, shift, right, left, joints):
    feet = {}
    pelvis_x, pelvis_y = joints["pelvis"]["pivot"]
    for side, (x, y, angle) in (("right", right), ("left", left)):
        hip = joints[f"{side}_thigh"]["pivot"]
        knee = joints[f"{side}_shin"]["pivot"]
        boot = joints[f"{side}_boot"]
        ankle_x, ankle_y = boot["pivot"]
        center_x = (boot["heel"][0] + boot["toe"][0]) / 2
        center_y = (boot["heel"][1] + boot["toe"][1]) / 2
        ankle_dx, ankle_dy = rotate((ankle_x - center_x, ankle_y - center_y), angle)
        hip_dx, hip_dy = rotate((hip[0] - pelvis_x, hip[1] - pelvis_y), angles["pelvis"])
        root_x, root_y = pelvis_x + shift[0] + hip_dx, pelvis_y + shift[1] + hip_dy
        dx, dy = x + ankle_dx - root_x, y + ankle_dy - root_y
        reach = math.dist(hip, knee) + math.dist(knee, boot["pivot"]) - 0.05
        factor = reach / max(reach, math.hypot(dx, dy))
        feet[side] = (round(root_x + dx * factor - ankle_dx - center_x, 4),
                      round(root_y + dy * factor - ankle_dy - center_y, 4), angle)
    return pose(ms, angles, {"pelvis": shift}, [], feet)


def reactions(back, joints):
    contact = -63 if back else -94
    strike = (braced(55, [2.0, 2.0], 13, -3, contact, -19, 25, 9, 2) if back
              else braced(55, [3.7, 3.2], 20, -13, contact, -4, 29, 12, 2.3))
    landing = (10.2, 9.0, 9.0) if back else (6.5, 5.6, 6.2)
    final_steps = ([(36, 57, 5), (43, 57, -4), (45, 57, -9), (48, 56, -20),
                    (50, 55, -23), (50, 56, -17)] if back else
                   [(28, 58, 4), (34, 58, -5), (40, 57, -13), (45, 57, -20),
                    (47, 57, -24), (48, 57, -20)])
    trailing_steps = ([(25, 56, -3), (30, 57, 3), (37, 57, 6), (43, 56, 11),
                       (46, 56, 10), (45, 57, 12)] if back else
                      [(38, 56, -2), (41, 56, -5), (45, 55, -9), (48, 54, -14),
                       (50, 54, -20), (50, 55, -18)])
    fall_keys = [
        (65, {"pelvis": -16, "chest": -19, "head": -18, "right_upper_arm": 31,
              "left_upper_arm": -24, "cloth": 12}, [0, 5.0]),
        (60, {"pelvis": -34, "chest": -17, "head": -14, "right_upper_arm": 28,
              "right_forearm": -15, "left_upper_arm": -18, "cloth": 18}, [1.4, 7.0]),
        (62, {"pelvis": -52, "chest": -14, "head": -9, "right_upper_arm": 26,
              "right_forearm": -26, "left_upper_arm": -12, "cloth": 20}, [3.0, 9.4 if back else 7.5]),
        (55, {"pelvis": -69, "chest": -14, "head": -3, "right_upper_arm": 38,
              "right_forearm": -34, "left_upper_arm": -6, "cloth": 14}, [5.0, landing[0]]),
        (56, {"pelvis": -80, "chest": -9, "head": 2, "right_upper_arm": 40,
              "right_forearm": -46, "left_upper_arm": -9, "cloth": 12}, [5.6, landing[1]]),
        (310, {"pelvis": -78, "chest": -12, "head": 0, "right_upper_arm": 37,
               "right_forearm": -51, "left_upper_arm": -10, "cloth": 10}, [5.5, landing[2]]),
    ]
    return {
        "idle": [
            pose(165), pose(130, {"head": 1, "chest": -1}), pose(175, {"head": 2, "chest": -2}),
            pose(170, {"head": -1, "chest": 1}), pose(160, {"head": -1}),
        ],
        "walk": walk(back),
        "windup": [
            braced(50, [0, 0.7], -3, 3, 4, 6, -8, -2),
            braced(55, [-0.5, 1.2], -6, 5, 22, 14, -16, -5),
            braced(60, [-1.0, 1.7], -9, 6, 49, 25, -20, -8),
            braced(65, [-1.5, 2.0], -11, 7, 71, 38, -20, -9),
            braced(65, [-1.5, 2.0], -12, 9, 74, 40, -21, -8),
            braced(65, [-1.0, 1.7], -8, 7, 53, 29, -17, -6),
        ],
        "recover": [
            strike,
            braced(55, [2.0, 3.0], 16, -7, contact + 14, -12, 21, 14, 2),
            braced(68, [1.5, 2.5], 12, -6, -42, 3, 14, 11, 1.5),
            braced(82, [1.0, 1.8], 7, -4, -24, 3, 8, 8, 1),
            braced(95, [0.6, 1.0], 3, -2, -11, 2, 4, 4, 0.5),
            braced(90, [0.2, 0.4], 1, -1, -4, 0, 1, 1),
            pose(75),
        ],
        "hit": [
            braced(35, [-0.8, 1.1], -13, -7, 21, -13, -26, -8),
            braced(40, [-1.9, 1.6], -21, -10, 36, -18, -37, -14, -1),
            braced(50, [-1.3, 2.4], -17, -3, 21, -7, -21, -12, -1),
            braced(60, [-0.7, 2.0], -10, 4, 12, 0, -11, -7, -0.5),
            braced(55, [-0.2, 0.8], -4, 2, 3, 0, -4, -3),
            pose(50),
        ],
        "collapse": [
            braced(50, [-1.0, 1.7], -14, -10, 24, -14, -22, -8),
            braced(62, [-1.4, 3.8], -20, -13, 32, -10, -28, -15, -1),
            *[falling(*key, right, left, joints)
              for key, right, left in zip(fall_keys, final_steps, trailing_steps)],
        ],
    }


def compiler_character(direction, work):
    source = MATERIAL / f"{direction}_character.json"
    if direction == "front_right":
        return source
    # This SpriteCut version accepts only a front_right slot for authored poses.
    # Register the rear drawing in that slot for compilation without mirroring it.
    destination = work / "rear_material"
    destination.mkdir()
    character = json.loads(source.read_text(encoding="utf-8"))
    index_path = MATERIAL / character["parts"]
    index = json.loads(index_path.read_text(encoding="utf-8"))
    registered = json.loads((MATERIAL / character["views"]).read_text(encoding="utf-8"))
    rear = next(view for view in registered["views"] if view["direction"] == direction)
    shutil.copyfile(MATERIAL / "prepared" / rear["file"], destination / rear["file"])
    shutil.copytree(index_path.parent / direction, destination / direction)
    write(destination / "views.json", {
        "version": 1, "cell": CELL, "pivot": GROUND,
        "views": [{"direction": "front_right", "file": rear["file"]}],
    })
    index["views"] = {"front_right": index["views"][direction]}
    write(destination / "parts.json", index)
    path = destination / "character.json"
    write(path, {"version": 1, "direction": "front_right", "views": "views.json", "parts": "parts.json"})
    return path


def bake():
    sheets = VERSION / "sheets"
    recipes = VERSION / "recipes"
    tracks = VERSION / "tracks"
    sheets.mkdir(exist_ok=True)
    tracks.mkdir(exist_ok=True)
    joints = json.loads((MATERIAL / "joints.json").read_text(encoding="utf-8"))
    clips = {}
    staging = PROJECT / ".local"
    staging.mkdir(exist_ok=True)
    with TemporaryDirectory(dir=staging, prefix="crypt-bake-") as scratch:
        work = Path(scratch)
        for direction in DIRECTIONS:
            character = compiler_character(direction, work)
            keys = reactions(direction == "back_right", joints[direction])
            for action in CLIP_NAMES:
                name = f"{action}_{direction}"
                recipe = recipes / f"{name}.json"
                write(recipe, {"version": 1, "clip": name, "loop": action in {"idle", "walk"},
                               "poses": keys[action]})
                compiled = work / f"{name}_compiled"
                output = work / name
                spritecut("animate", character, recipe, compiled)
                spritecut("bake", compiled / "recipe.json", output)
                clip = json.loads((output / "clips.json").read_text(encoding="utf-8"))["clips"][name]
                clips[name] = clip
                for filename in clip["maps"].values():
                    shutil.copyfile(output / filename, sheets / filename)
                landmarks = json.loads((compiled / "tracks.json").read_text(encoding="utf-8"))
                landmarks["direction"] = direction
                write(tracks / f"{name}.json", landmarks)
    write(sheets / "clips.json", {"version": 1, "cell": CELL, "pivot": GROUND, "clips": clips})
    return clips


def review(clips):
    preview = VERSION / "previews"
    preview.mkdir(exist_ok=True)
    sheets = VERSION / "sheets"
    samples = {}
    for name, clip in clips.items():
        with Image.open(sheets / clip["maps"]["color"]) as atlas:
            samples[name] = [atlas.crop((f["x"], f["y"], f["x"] + f["w"], f["y"] + f["h"])).convert("RGBA")
                             for f in clip["frames"]]
        for frame, cel in enumerate(samples[name]):
            bounds = cel.getchannel("A").getbbox()
            if not bounds or not (0 < bounds[0] < bounds[2] < CELL[0]
                                  and 0 < bounds[1] < bounds[3] < CELL[1]):
                raise ValueError(f"{name} frame {frame + 1}: invalid cell bounds {bounds}")
    columns = (("Idle", "idle", 0), ("Walk A", "walk", 0), ("Walk B", "walk", 4),
               ("Wind-up", "windup", 4), ("Contact", "recover", 0), ("Hit", "hit", 1),
               ("Knees", "collapse", 2), ("Fall", "collapse", 7))
    strip = Image.new("RGBA", (len(columns) * 66, 152), "#30253a")
    for row, direction in enumerate(DIRECTIONS):
        for index, (label, action, key) in enumerate(columns):
            x, y = 66 * index, 76 * row
            ImageDraw.Draw(strip).text((x + 6, y + 1), label, fill="#e8d2b5")
            ImageDraw.Draw(strip).line((x, y + 69, x + 65, y + 69), fill="#6c546e")
            strip.alpha_composite(samples[f"{action}_{direction}"][key], (x + 1, y + 11))
    strip.convert("RGB").resize((strip.width * 2, strip.height * 2),
                                Image.Resampling.NEAREST).save(preview / "motion-poses-2x.png")
    for name, actions in (("walk", ("walk", "walk")), ("attack", ("windup", "recover")),
                          ("hit", ("hit", "idle")), ("death", ("collapse",))):
        images, durations = [], []
        for action in actions:
            front, back = (samples[f"{action}_{direction}"] for direction in DIRECTIONS)
            times = clips[f"{action}_{DIRECTIONS[0]}"]["frames"]
            for a, b, frame in zip(front, back, times):
                canvas = Image.new("RGBA", (136, 68), "#30253a")
                ImageDraw.Draw(canvas).line((0, 60, 135, 60), fill="#6c546e")
                canvas.alpha_composite(a, (1, 2))
                canvas.alpha_composite(b, (70, 2))
                images.append(canvas.convert("RGB").resize((408, 204), Image.Resampling.NEAREST))
                durations.append(frame["ms"])
        if name == "death":
            durations[-1] += 500
        images[0].save(preview / f"{name}.gif", save_all=True, append_images=images[1:],
                       duration=durations, loop=0, disposal=2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--publish", action="store_true", help="copy the verified color sheets into Godot")
    args = parser.parse_args()
    if args.publish:
        sheets = VERSION / "sheets"
        clips = json.loads((sheets / "clips.json").read_text(encoding="utf-8"))["clips"]
        for clip in clips.values():
            color = clip["maps"]["color"]
            shutil.copyfile(sheets / color, RUNTIME / color)
        sprite_frames(clips)
    else:
        review(bake())


if __name__ == "__main__":
    main()

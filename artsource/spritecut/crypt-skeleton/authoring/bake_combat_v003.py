"""Bake a backward fall along each view's projected facing axis."""

import argparse
import json
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image, ImageDraw

from bake_combat_v002 import MATERIAL, VERSION as BASELINE, compiler_character, falling
from build_crypt_skeleton import CELL, DIRECTIONS, GROUND, PROJECT, ROOT, RUNTIME, spritecut, write


VERSION = ROOT / "motions/combat/v003"

# Screen-space poses. The rear view recedes on the opposite Y diagonal.
FALL = {
    "front_right": {
        "pelvis": [(-15, -0.5, 4), (-25, 0.5, 5.3), (-37, 1.6, 6.1),
                   (-48, 2.8, 7), (-52, 3.8, 7.5), (-51, 3.8, 7.8)],
        "right": [(27, 58, 4), (30, 57, 0), (34, 57, -5), (39, 58, -12),
                  (43, 59, -17), (43, 59, -13)],
        "left": [(38, 56, -3), (40, 56, -6), (43, 56, -8), (45, 55, -12),
                 (47, 55, -16), (47, 56, -11)],
    },
    "back_right": {
        "pelvis": [(-20, -0.5, 4.0), (-42, 0.5, 4.8), (-67, 1.8, 4.0),
                   (-106, 3.2, 2.0), (-124, 4, -2.3), (-126, 3.8, -2.4)],
        "right": [(36, 57, 5), (41, 55, -3), (44, 52, -8), (46, 45, -16),
                  (46, 36, -23), (46, 36, -19)],
        "left": [(25, 56, -3), (30, 55, 0), (36, 53, 4), (40, 47, 8),
                 (43, 38, 10), (43, 38, 6)],
    },
}

# Neck and arm motion still lag behind the hips during the fall.
UPPER_BODY = [
    (-19, -18, 31, 0, -24, 12),
    (-17, -14, 28, -15, -18, 18),
    (-14, -9, 26, -26, -12, 20),
    (-13, -3, 39, -35, -7, 14),
    (-10, 2, 44, -46, -9, 12),
    (-9, 1, 42, -49, -10, 10),
]


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def recipe_for(direction, baseline, joints):
    pelvis, right, left = (FALL[direction][key] for key in ("pelvis", "right", "left"))
    existing = baseline["poses"]
    frames = list(existing[:2])
    for previous, (tilt, x, y), lead, trail, upper in zip(existing[2:], pelvis, right, left, UPPER_BODY):
        chest, head, arm, elbow, far_arm, cloth = upper
        angles = {
            "pelvis": tilt, "chest": chest, "head": head, "right_upper_arm": arm,
            "right_forearm": elbow, "left_upper_arm": far_arm, "cloth": cloth,
        }
        frames.append(falling(previous["ms"], angles, [x, y], lead, trail, joints))
    return {**baseline, "poses": frames}


def cell_frames(directory, clip):
    with Image.open(directory / clip["maps"]["color"]) as atlas:
        return [
            atlas.crop((f["x"], f["y"], f["x"] + f["w"], f["y"] + f["h"])).convert("RGBA")
            for f in clip["frames"]
        ]


def frame_layout(frames):
    return [tuple(f[key] for key in ("x", "y", "w", "h", "ms")) for f in frames]


def verify(name, clip, previous, landmarks):
    if frame_layout(clip["frames"]) != frame_layout(previous["frames"]):
        raise ValueError(f"{name}: atlas frames or timing differ from the base animation")
    for index, sprite in enumerate(cell_frames(VERSION / "sheets", clip)):
        x0, y0, x1, y1 = sprite.getchannel("A").getbbox()
        if not (0 < x0 < x1 < CELL[0] and 0 < y0 < y1 < CELL[1]):
            raise ValueError(f"{name} frame {index + 1} reaches the cell edge: {(x0, y0, x1, y1)}")
    points = landmarks["frames"][-1]["points"]
    head_x, head_y = points["head"]
    foot_x = (points["right_foot"][0] + points["left_foot"][0]) / 2
    foot_y = (points["right_foot"][1] + points["left_foot"][1]) / 2
    dy = head_y - foot_y
    if foot_x - head_x < 13 or (dy < 9 if name.endswith("back_right") else dy > -9):
        raise ValueError(f"{name} does not fall back on its visible diagonal: {(head_x - foot_x, dy)}")
    print(f"{name}: head relative to heels ({head_x - foot_x:.1f}, {dy:.1f})")


def bake():
    baseline = read(BASELINE / "sheets/clips.json")
    clips = {}
    joints = read(MATERIAL / "joints.json")
    for folder in ("sheets", "tracks", "previews"):
        (VERSION / folder).mkdir(exist_ok=True)
    staging = PROJECT / ".local"
    staging.mkdir(exist_ok=True)
    with TemporaryDirectory(dir=staging, prefix="crypt-fall-") as directory:
        work = Path(directory)
        for direction in DIRECTIONS:
            name = "collapse_" + direction
            character = compiler_character(direction, work)
            recipe = VERSION / "recipes" / f"{name}.json"
            write(recipe, recipe_for(direction, read(BASELINE / "recipes" / recipe.name), joints[direction]))
            compiled = work / f"{name}_compiled"
            baked = work / name
            spritecut("animate", character, recipe, compiled)
            spritecut("bake", compiled / "recipe.json", baked)
            clip = read(baked / "clips.json")["clips"][name]
            for filename in clip["maps"].values():
                shutil.copyfile(baked / filename, VERSION / "sheets" / filename)
            landmarks = read(compiled / "tracks.json")
            landmarks["direction"] = direction
            write(VERSION / "tracks" / f"{name}.json", landmarks)
            verify(name, clip, baseline["clips"][name], landmarks)
            clips[name] = clip
    catalog = {}
    for name, previous in baseline["clips"].items():
        if name in clips:
            catalog[name] = clips[name]
        else:
            maps = {kind: f"../../{BASELINE.name}/sheets/{file}" for kind, file in previous["maps"].items()}
            catalog[name] = {**previous, "maps": maps}
    write(VERSION / "sheets/clips.json", {**baseline, "clips": catalog})
    return baseline, clips


def compare(baseline, clips):
    pairs = []
    for name, clip in clips.items():
        pairs.append((cell_frames(BASELINE / "sheets", baseline["clips"][name]),
                      cell_frames(VERSION / "sheets", clip)))
    images = []
    durations = [frame["ms"] for frame in next(iter(clips.values()))["frames"]]
    for frame in range(len(durations)):
        panel = Image.new("RGBA", (168, 166), "#30253a")
        draw = ImageDraw.Draw(panel)
        draw.text((30, 2), "Front", fill="#e8d2b5")
        draw.text((100, 2), "Rear", fill="#e8d2b5")
        for col, (before, after) in enumerate(pairs):
            x = 23 + 69 * col
            for y, label, cells in ((18, "Old", before), (96, "New", after)):
                draw.text((2, y + 28), label, fill="#e8d2b5")
                draw.line((x, y + 58, x + 63, y + 58), fill="#6c546e")
                panel.alpha_composite(cells[frame], (x, y))
        images.append(panel.convert("RGB").resize((504, 498), Image.Resampling.NEAREST))
    previews = VERSION / "previews"
    images[-1].save(previews / "death-end-poses.png")
    durations[-1] += 390
    images[0].save(previews / "death-comparison.gif", save_all=True, append_images=images[1:],
                   duration=durations, loop=0, disposal=2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--publish", action="store_true", help="apply the two collapse color atlases to Godot")
    args = parser.parse_args()
    if args.publish:
        catalog = read(VERSION / "sheets/clips.json")["clips"]
        for direction in DIRECTIONS:
            clip = catalog["collapse_" + direction]
            color = clip["maps"]["color"]
            shutil.copyfile(VERSION / "sheets" / color, RUNTIME / color)
    else:
        compare(*bake())


if __name__ == "__main__":
    main()

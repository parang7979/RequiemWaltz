"""Compose the Requiem chain motion study with the original in-game sprites."""

import argparse
import json
import math
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

from PIL import Image, ImageDraw, ImageOps


ROOT = Path(__file__).resolve().parents[2]
ACTORS = ROOT / "assets/actors"
STUDIES = ROOT / "artsource/spritecut/waltz/sources/form-studies"


def load_rgba(path):
    with Image.open(path) as image:
        return image.convert("RGBA")


def sprite_frame(path, rect):
    return load_rgba(path).crop(
        (rect["x"], rect["y"], rect["x"] + rect["w"], rect["y"] + rect["h"])
    )


def actor_frame(stage, sprite, feet, pivot):
    stage.alpha_composite(sprite, (round(feet[0] - pivot[0]), round(feet[1] - pivot[1])))


def rotated_sword(stage, sprite, pose, pommel):
    angle = math.radians(pose["angle"])
    cos, sin = math.cos(angle), math.sin(angle)
    x, y = pose["x"], pose["y"]
    return sprite.transform(
        stage.size,
        Image.Transform.AFFINE,
        (cos, sin, pommel[0] - cos * x - sin * y, -sin, cos, pommel[1] + sin * x - cos * y),
        Image.Resampling.NEAREST,
    )


def skeleton_frames(name):
    source = load_rgba(ACTORS / "crypt_skeleton" / f"{name}_front_right_color.png")
    return [
        ImageOps.mirror(source.crop((x, 0, x + 64, 64))) for x in range(0, source.width, 64)
    ]


def shadow(draw, x, y, width, height, alpha):
    draw.ellipse((round(x - width), round(y - height), round(x + width), round(y + height)),
                 fill=(19, 13, 27, alpha))


def compose(staging):
    preview = json.loads((staging / "preview.json").read_text(encoding="utf-8"))
    atlas = load_rgba(staging / "effects.png")
    frames = preview["atlas"]["frames"]
    size = (frames[0]["frame"]["w"], frames[0]["frame"]["h"])
    arena = load_rgba(ROOT / "assets/rooms/seal_chamber.png")
    floor = arena.crop((146, 146, 146 + size[0], 146 + size[1]))

    forms = ACTORS / "requiem_forms"
    clips = json.loads((forms / "clips.json").read_text(encoding="utf-8"))["clips"]
    waltz_clip = clips["waltz_front_right"]
    waltz = sprite_frame(forms / waltz_clip["maps"]["color"], waltz_clip["frames"][0])
    sword_clip = clips["sword"]
    sword = sprite_frame(forms / sword_clip["maps"]["color"], sword_clip["frames"][0])
    idle_skeleton = skeleton_frames("idle")[0]
    hit_skeleton = skeleton_frames("hit")
    for entry, pose in zip(frames, preview["frames"], strict=True):
        stage = floor.copy()
        waltz_x, waltz_y = preview["waltzFeet"]
        target_x, target_y = preview["targetFeet"]
        waltz_x += pose["lean"]
        duration = entry["duration"]
        hit = next((hit for hit in preview["hits"] if 0 <= pose["t"] - hit["time"] < .18), None)
        if hit:
            elapsed = pose["t"] - hit["time"]
            if elapsed == 0:
                duration += hit["holdMs"]
            skeleton = hit_skeleton[min(int(elapsed * 32), len(hit_skeleton) - 1)]
            target_x += hit["push"] * math.sin(math.pi * elapsed / .18)
            if elapsed < .041:
                tint = Image.new("RGBA", skeleton.size, (255, 223, 248))
                tint.putalpha(skeleton.getchannel("A"))
                skeleton = Image.blend(skeleton, tint, .54 * (1 - elapsed / .041))
        else:
            skeleton = idle_skeleton

        shadows = Image.new("RGBA", size)
        draw = ImageDraw.Draw(shadows)
        shadow(draw, waltz_x, waltz_y - 1, 13, 3, 108)
        shadow(draw, target_x, target_y - 1, 14, 4, 115)
        if pose["spirit"]:
            shadow(draw, pose["spirit"][0] - 11, waltz_y + 2, 12, 3, 58)
        shadow(draw, pose["x"] + 15, 111, 20, 2, 63)
        stage.alpha_composite(shadows)
        actor_frame(stage, waltz, (waltz_x, waltz_y), waltz_clip["pivot"])
        actor_frame(stage, skeleton, (target_x, target_y), (32, 56))
        rect = entry["frame"]
        effect = atlas.crop((rect["x"], rect["y"], rect["x"] + rect["w"], rect["y"] + rect["h"]))
        stage.alpha_composite(effect)
        stage.alpha_composite(rotated_sword(stage, sword, pose, preview["pommel"]))
        yield stage.convert("RGB"), duration


def save_gif(staging, destination):
    frames, durations = zip(*compose(staging))
    width, height = frames[0].size
    samples = frames[::4]
    swatches = Image.new("RGB", (width, height * len(samples)))
    for index, frame in enumerate(samples):
        swatches.paste(frame, (0, index * height))
    palette = swatches.quantize()
    scaled = [
        frame.quantize(palette=palette, dither=Image.Dither.NONE).resize(
            (width * 2, height * 2), Image.Resampling.NEAREST
        )
        for frame in frames
    ]
    scaled[0].save(
        destination, save_all=True, append_images=scaled[1:],
        duration=list(durations), loop=0,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", choices=("v002", "v003", "v004"), default="v004")
    version = parser.parse_args().version
    study = STUDIES / version
    study.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="requiem-chain-") as temporary:
        staging = Path(temporary)
        subprocess.run(
            ["node", ROOT / "artsource/pixelfx/requiem_chain.mjs", staging, version],
            check=True,
        )
        save_gif(staging, study / "chain-return.gif")

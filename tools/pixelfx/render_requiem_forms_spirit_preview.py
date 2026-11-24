"""Compare the original and spectral Requiem forms with the same SpriteCut posing."""

import base64
import json
import math
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

from PIL import Image, ImageDraw, ImageFont

from render_requiem_chain_preview import ACTORS, ROOT, STUDIES, actor_frame, load_rgba, rotated_sword


FORMS = ("hand", "bow", "cannon")
LABELS = ("장갑", "활", "대포")
FORM_DIR = ACTORS / "requiem_forms"
FX_DIR = ROOT / "assets/vfx/requiem_forms"
STUDY = STUDIES / "spectral-forms/v001"
PANEL = (224, 112)
RIG = (104, 53)
FEET = (30, 91)
ACTION = 440
PERIOD = 1440
STEP = 40


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def crop(sheet, rect):
    x, y = rect["x"], rect["y"]
    return sheet.crop((x, y, x + rect["w"], y + rect["h"]))


def frame_at(frames, time, duration_key):
    for index, entry in enumerate(frames):
        time -= entry[duration_key]
        if time < 0:
            return index
    return len(frames) - 1


def load_fx(name):
    manifest = read_json(FX_DIR / f"{name}.json")
    sheet = load_rgba(FX_DIR / f"{name}.png")
    images = [crop(sheet, entry["frame"]) for entry in manifest["frames"]]
    return manifest["frames"], images, manifest["meta"]["pixelfx"]["pivot"]


def draw_fx(stage, effect, age, anchor, loop_scale=None):
    durations, images, pivot = effect
    duration = sum(entry["duration"] for entry in durations)
    if loop_scale:
        age %= duration
    elif not 0 <= age < duration:
        return
    image = images[frame_at(durations, age, "duration")]
    if loop_scale:
        image = image.resize(tuple(round(length * loop_scale) for length in image.size), Image.Resampling.NEAREST)
        pivot = [part * loop_scale for part in pivot]
    actor_frame(stage, image, anchor, pivot)


def load_form(manifest, kind):
    name = f"{kind}_front_right"
    clips = [f"{name}_{state}" for state in ("idle", "action")]
    tracks = manifest["forms"][name]["tracks"]
    poses = {}
    for key in clips:
        clip = manifest["clips"][key]
        sheet = load_rgba(FORM_DIR / clip["maps"]["color"])
        images = [crop(sheet, entry) for entry in clip["frames"]]
        poses[key.rsplit("_", 1)[-1]] = (clip["frames"], images, tracks[key], clip["pivot"])
    release = 0
    for action in poses["action"][0]:
        if "release" in action.get("events", []):
            break
        release += action["ms"]
    return poses, release


def poses_for_time(time, form):
    poses, release = form
    action_duration = sum(frame["ms"] for frame in poses["action"][0])
    acting = ACTION <= time < ACTION + action_duration
    frames, images, tracks, pivot = poses["action" if acting else "idle"]
    elapsed = time - ACTION
    local_time = elapsed if acting else time % sum(frame["ms"] for frame in frames)
    index = frame_at(frames, local_time, "ms")
    if not acting:
        peak = 0
    elif elapsed < release:
        peak = math.sin(math.pi * .5 * elapsed / max(1, release))
    else:
        peak = max(0, 1 - (elapsed - release) / 110)
    return images[index], tracks[index], pivot, acting, elapsed - release, peak


def frame_job(kind, pose, time):
    image, points, pivot, _, _, peak = pose
    return {
        "kind": kind,
        "width": image.width,
        "height": image.height,
        "rgba": base64.b64encode(image.tobytes()).decode("ascii"),
        "points": {
            key: [point[0] + pivot[0], point[1] + pivot[1]]
            for key, point in points.items()
        } | {"pivot": pivot},
        "phase": math.tau * time / PERIOD,
        "load": peak,
    }


def scene(floor, waltz, blade, kind, pose, armor, fx, time):
    _, points, pivot, acting, fired, _ = pose
    stage = floor.copy()
    shadow = Image.new("RGBA", PANEL)
    draw = ImageDraw.Draw(shadow)
    x, y = FEET
    draw.ellipse((x - 13, y - 4, x + 13, y + 2), fill=(16, 10, 23, 112))
    draw.ellipse((RIG[0] - 22, y - 1, RIG[0] + 24, y + 7), fill=(16, 10, 23, 73))
    stage.alpha_composite(shadow)
    waltz_image, waltz_pivot = waltz
    actor_frame(stage, waltz_image, FEET, waltz_pivot)
    world = {key: (round(point[0] + RIG[0]), round(point[1] + RIG[1])) for key, point in points.items()}
    draw_fx(stage, fx["tail"], time, world["tail"], {"hand": .67, "bow": .52, "cannon": .63}[kind])
    socket = world["socket"]
    sword, sword_pivot = blade
    if kind == "bow":
        ImageDraw.Draw(stage).line((world["upper"], socket, world["lower"]), fill="#e9b5fa")
    if kind == "hand":
        actor_frame(stage, sword, socket, sword_pivot)
    actor_frame(stage, armor, RIG, pivot)

    if kind == "bow" and (not acting or fired < 0):
        actor_frame(stage, sword, socket, sword_pivot)
    if kind != "hand" and acting and fired >= 0:
        heading = 11 if kind == "cannon" else 0
        angle = math.radians(heading)
        distance = fired * (.76 if kind == "cannon" else .595)
        if kind == "cannon":
            distance -= 47.34
        x = socket[0] + math.cos(angle) * distance
        y = socket[1] + math.sin(angle) * distance
        projectile = rotated_sword(stage, sword, {"x": x, "y": y, "angle": heading}, sword_pivot)
        if kind == "cannon":
            stage.alpha_composite(projectile.crop((socket[0], 0, PANEL[0], PANEL[1])), (socket[0], 0))
        else:
            stage.alpha_composite(projectile)
        flash = (RIG[0] + 11, RIG[1]) if kind == "bow" else socket
        draw_fx(stage, fx[kind], fired, flash)
    return stage


def comparison(panels):
    margin, gutter, header, row_label = 6, 5, 18, 14
    width = 2 * margin + 2 * PANEL[0] + gutter
    height = header + len(FORMS) * (row_label + PANEL[1]) + margin
    board = Image.new("RGB", (width, height), "#1b1422")
    for index, panel in enumerate(panels):
        row, column = divmod(index, 2)
        x = margin + column * (PANEL[0] + gutter)
        y = header + row * (row_label + PANEL[1]) + row_label
        board.paste(panel, (x, y))
    board = board.resize((2 * width, 2 * height), Image.Resampling.NEAREST)
    draw = ImageDraw.Draw(board)
    font = ImageFont.truetype("malgun.ttf", 14)
    draw.text((2 * margin, 6), "기존", fill="#d4c4db", font=font)
    draw.text((2 * (margin + PANEL[0] + gutter), 6), "영체 시안", fill="#eecbff", font=font)
    for row, label in enumerate(LABELS):
        draw.text((2 * margin, 2 * (header + row * (row_label + PANEL[1])) + 3),
                  label, fill="#c7a9d0", font=font)
    return board


def build(staging):
    manifest = read_json(FORM_DIR / "clips.json")
    forms = {kind: load_form(manifest, kind) for kind in FORMS}
    fx = {"tail": load_fx("tail"), "bow": load_fx("bow_release"), "cannon": load_fx("cannon_release")}
    sprites = []
    for name in ("waltz_front_right", "sword"):
        clip = manifest["clips"][name]
        sprites.append((crop(load_rgba(FORM_DIR / clip["maps"]["color"]), clip["frames"][0]), clip["pivot"]))
    waltz, blade = sprites
    arena = load_rgba(ROOT / "assets/waltz_combat/chamber.png")
    floor = arena.crop((207, 152, 207 + PANEL[0], 152 + PANEL[1]))

    times = list(range(0, PERIOD, STEP))
    poses = [(time, kind, poses_for_time(time, forms[kind])) for time in times for kind in FORMS]
    jobs = [frame_job(kind, pose, time) for time, kind, pose in poses]
    request = staging / "frames.json"
    result = staging / "spectral.rgba"
    request.write_text(json.dumps(jobs), encoding="utf-8")
    subprocess.run(["node", ROOT / "artsource/pixelfx/requiem_forms_spirit.mjs", request, result], check=True)
    rgba = result.read_bytes()

    frames = []
    byte_offset = 0
    for frame_number in range(len(times)):
        panels = []
        for time, kind, pose in poses[frame_number * len(FORMS):(frame_number + 1) * len(FORMS)]:
            original = pose[0]
            end_offset = byte_offset + original.width * original.height * 4
            spectral = Image.frombytes("RGBA", original.size, rgba[byte_offset:end_offset])
            byte_offset = end_offset
            panels.extend(scene(floor, waltz, blade, kind, pose, armor, fx, time)
                          for armor in (original, spectral))
        frames.append(comparison(panels))
    return frames


def save_gif(frames, destination):
    width, height = frames[0].size
    samples = frames[::4]
    swatches = Image.new("RGB", (width, height * len(samples)))
    for index, image in enumerate(samples):
        swatches.paste(image, (0, index * height))
    palette = swatches.quantize()
    frames = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
    frames[0].save(destination, save_all=True, append_images=frames[1:], duration=STEP, loop=0)


if __name__ == "__main__":
    STUDY.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="requiem-forms-spirit-") as temporary:
        save_gif(build(Path(temporary)), STUDY / "comparison.gif")

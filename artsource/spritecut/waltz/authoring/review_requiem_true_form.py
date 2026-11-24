"""Review the baked front motions and their hand-offs with the existing gauntlet."""

import argparse
from bisect import bisect_right
from itertools import accumulate

from PIL import Image, ImageChops, ImageDraw, ImageFont

from build_requiem_true_form import CHARACTER, CLIPS, MATERIAL, read, write_json


PROJECT = CHARACTER.parents[2]
MOTIONS = CHARACTER / "motions"
BACKDROP = "#281e31"


def frames(sheet, entries, key):
    cells = []
    for entry in entries:
        rect = entry.get("frame", entry)
        x, y, w, h = (rect[field] for field in ("x", "y", "w", "h"))
        cells.append(sheet.crop((x, y, x + w, y + h)))
    return cells, list(accumulate(entry[key] for entry in entries))


def baked(kind):
    name = f"requiem_true_{kind}"
    folder = MOTIONS / name / "v001/sheets"
    clip = read(folder / "clips.json")["clips"][name]
    with Image.open(folder / clip["maps"]["color"]) as sheet:
        return frames(sheet.convert("RGBA"), clip["frames"], "ms")


def game_clip(path, name):
    clip = read(path / "clips.json")["clips"][name]
    with Image.open(path / clip["maps"]["color"]) as sheet:
        return (*frames(sheet.convert("RGBA"), clip["frames"], "ms"), clip["pivot"])


def cell_at(track, time):
    images, ends = track[:2]
    return images[min(len(images) - 1, bisect_right(ends, max(0, time)))]


def save_gif(images, ms, path):
    w, h = images[0].size
    samples = images[::max(1, len(images) // 12)]
    ribbon = Image.new("RGB", (w, h * len(samples)))
    for i, frame in enumerate(samples):
        ribbon.paste(frame, (0, i * h))
    palette = ribbon.quantize(colors=256)
    frames = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in images]
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=ms, loop=0)


def layout(panels):
    margin, gap, label_height, scale = 14, 9, 34, 3
    size = panels[0][1].size
    pw, ph = tuple(n * scale for n in size)
    canvas = Image.new("RGB", (2 * margin + len(panels) * pw + (len(panels) - 1) * gap,
                               2 * margin + label_height + ph), "#17111f")
    font = ImageFont.truetype("malgun.ttf", 17)
    labels = ImageDraw.Draw(canvas)
    for i, (name, sprite) in enumerate(panels):
        x = margin + (pw + gap) * i
        labels.text((x, margin - 1), name, font=font, fill="#e6c9f6")
        canvas.paste(sprite.convert("RGB").resize((pw, ph), Image.Resampling.NEAREST),
                     (x, margin + label_height))
    return canvas


def panel(image):
    art = Image.new("RGBA", image.size, BACKDROP)
    art.alpha_composite(image)
    return art


def overview(tracks):
    started = (0, 220, 220)
    # GIF uses centiseconds. Round boundaries rather than rounding each duration.
    times = sorted({round((offset + tick) / 10) * 10
                    for offset, track in zip(started, tracks, strict=True)
                    for tick in [0, *track[1]]})
    labels = ("대기 · 1.60초", "무기 전환 영체화 · 118ms", "소멸 · 0.64초")
    images, durations = [], []
    for a, b in zip(times, times[1:]):
        images.append(layout([
            (label, panel(cell_at(track, a - offset)))
            for label, track, offset in zip(labels, tracks, started, strict=True)
        ]))
        durations.append(b - a)
    save_gif(images, durations, MOTIONS / CLIPS[0] / "v001/previews/motion-overview.gif")


def switch_preview(exit_track, enter_track, idle_track, label, path):
    shader = PROJECT / "assets/vfx/requiem_forms"
    fx = read(shader / "shift.json")
    with Image.open(shader / "shift.png") as sheet:
        shift = frames(sheet.convert("RGBA"), fx["frames"], "duration")
    exit_ms = exit_track[1][-1]
    enter_ms = enter_track[1][-1]
    center = (78, 67)
    settle_at = max(exit_ms + enter_ms, shift[1][-1])
    points = sorted({0, *exit_track[1], *(exit_ms + t for t in enter_track[1]),
                     *shift[1], settle_at + 140})
    images, lengths = [], []
    for i, t in enumerate(points[:-1]):
        background = Image.new("RGBA", (156, 140), BACKDROP)
        if t < exit_ms:
            track, elapsed = exit_track, t
        elif t < exit_ms + enter_ms:
            track, elapsed = enter_track, t - exit_ms
        else:
            track, elapsed = idle_track, 0
        background.alpha_composite(cell_at(track, elapsed), tuple(a - b for a, b in zip(center, track[2])))
        if t < shift[1][-1]:
            layer = Image.new("RGBA", background.size)
            layer.alpha_composite(cell_at(shift, t), tuple(a - b for a, b in zip(center, fx["meta"]["pixelfx"]["pivot"])))
            black = Image.new("RGB", layer.size)
            black.paste(layer, (0, 0), layer.getchannel("A"))
            background = ImageChops.add(background.convert("RGB"), black, scale=1.0)
        images.append(layout([(label, background)]))
        lengths.append(max(10, round((points[i + 1] - t) * .4) * 10))
    lengths[0] += 200
    save_gif(images, lengths, path)


def enter_preview(enter_track, path):
    cells, ends = enter_track[:2]
    ticks = [0, *(round(ms / 10) * 10 for ms in ends)]
    exposures = [b - a for a, b in zip(ticks, ticks[1:])]
    exposures[-1] += 600
    images = [layout([("본모습 등장 · 실제 속도", panel(cell))]) for cell in cells]
    save_gif(images, exposures, path)
    index_path = path.with_name("index.json")
    index = read(index_path)
    # SpriteCut outputs a still for this short shot. Its first frame is transparent.
    path.with_name("full-speed.png").unlink(missing_ok=True)
    index["playback"] = path.name
    write_json(index_path, index)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--enter-only", action="store_true")
    args = parser.parse_args()
    forms = PROJECT / "assets/actors/requiem_forms"
    fluid = read(MATERIAL / "regions.json")["fluid_center"]
    idle_track = (*baked("idle"), fluid)
    if not args.enter_only:
        exit_track = (*baked("exit"), fluid)
        overview([idle_track, exit_track, baked("vanish")])
        switch_preview(exit_track, game_clip(forms, "hand_front_right_enter"),
                       game_clip(forms, "hand_front_right_idle"), "본모습 → 보랏빛 불꽃 → 장갑 · ¼배속",
                       MOTIONS / CLIPS[1] / "v001/previews/to-gauntlet-slow.gif")
    enter_track = (*baked("enter"), fluid)
    previews = MOTIONS / "requiem_true_enter/v001/previews"
    enter_preview(enter_track, previews / "enter-full-speed.gif")
    switch_preview(game_clip(forms, "hand_front_right_exit"), enter_track, idle_track,
                   "장갑 → 보랏빛 불꽃 → 본모습 · ¼배속", previews / "from-gauntlet-slow.gif")

"""Review the baked front motions and the hand-off into the existing gauntlet."""

from bisect import bisect_right
from itertools import accumulate

from PIL import Image, ImageChops, ImageDraw, ImageFont

from build_requiem_true_form import CHARACTER, CLIPS, MATERIAL, read


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


def to_gauntlet(exit_track):
    forms = PROJECT / "assets/actors/requiem_forms"
    hand_enter = game_clip(forms, "hand_front_right_enter")
    hand_idle = game_clip(forms, "hand_front_right_idle")
    shader = PROJECT / "assets/vfx/requiem_forms"
    fx = read(shader / "shift.json")
    with Image.open(shader / "shift.png") as sheet:
        shift = frames(sheet.convert("RGBA"), fx["frames"], "duration")
    fluid = read(MATERIAL / "regions.json")["fluid_center"]
    exit_ms = exit_track[1][-1]
    enter_ms = hand_enter[1][-1]
    center = (78, 67)
    points = sorted({0, *exit_track[1], *(exit_ms + t for t in hand_enter[1]),
                     *(t for t in shift[1] if t < exit_ms + enter_ms), exit_ms + enter_ms + 140})
    images, lengths = [], []
    for i, t in enumerate(points[:-1]):
        background = Image.new("RGBA", (156, 140), BACKDROP)
        if t < exit_ms:
            sprite = cell_at(exit_track, t)
            pivot = fluid
        else:
            track = hand_enter if t < exit_ms + enter_ms else hand_idle
            sprite = cell_at(track, t - exit_ms if track is hand_enter else 0)
            pivot = track[2]
        background.alpha_composite(sprite, tuple(a - b for a, b in zip(center, pivot)))
        if t < shift[1][-1]:
            layer = Image.new("RGBA", background.size)
            layer.alpha_composite(cell_at(shift, t), tuple(a - b for a, b in zip(center, fx["meta"]["pixelfx"]["pivot"])))
            black = Image.new("RGB", layer.size)
            black.paste(layer, (0, 0), layer.getchannel("A"))
            background = ImageChops.add(background.convert("RGB"), black, scale=1.0)
        images.append(layout([("본모습 → 공통 유체 → 장갑 · ¼배속", background)]))
        lengths.append(max(10, round((points[i + 1] - t) * .4) * 10))
    lengths[0] += 200
    save_gif(images, lengths, MOTIONS / CLIPS[1] / "v001/previews/to-gauntlet-slow.gif")


if __name__ == "__main__":
    tracks = [baked(kind) for kind in ("idle", "exit", "vanish")]
    overview(tracks)
    to_gauntlet(tracks[1])

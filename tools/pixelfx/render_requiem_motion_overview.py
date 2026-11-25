"""Assemble the Requiem motion boards from the atlases and Godot review captures."""

from bisect import bisect_right
import json

from PIL import Image, ImageDraw, ImageFont

from render_requiem_chain_preview import ROOT, STUDIES, load_rgba


CAPTURES = ROOT / ".local/requiem-motion-capture"
ATLASES = ROOT / "assets/vfx/requiem_forms"
TRUE_FORM = STUDIES / "true-form/v002"
FRAME_COUNT = 54
FONT = ImageFont.truetype("malgun.ttf", 16)


def atlas_frames(suffix):
    name = ATLASES / f"true_form_{suffix}"
    data = json.loads(name.with_suffix(".json").read_text(encoding="utf-8"))
    atlas = load_rgba(name.with_suffix(".png"))
    frames = []
    for entry in data["frames"]:
        f = entry["frame"]
        frames.append(atlas.crop((f["x"], f["y"], f["x"] + f["w"], f["y"] + f["h"])))
    return frames


def capture(label, index, bounds):
    return load_rgba(CAPTURES / f"{label}-{index:02d}.png").crop(bounds)


def board(panels, columns, size):
    width, height = size
    rows = (len(panels) + columns - 1) // columns
    margin, header, gap = 6, 17, 5
    canvas = Image.new("RGB", (
        2 * (margin * 2 + columns * width + (columns - 1) * gap),
        2 * (margin * 2 + rows * (header + height) + (rows - 1) * gap),
    ), "#191220")
    labels = ImageDraw.Draw(canvas)
    for index, (caption, panel) in enumerate(panels):
        row, column = divmod(index, columns)
        x = 2 * (margin + column * (width + gap))
        y = 2 * (margin + row * (header + height + gap))
        labels.text((x, y + 1), caption, font=FONT, fill="#e7c8f5")
        canvas.paste(panel.convert("RGB").resize((2 * width, 2 * height), Image.Resampling.NEAREST),
                     (x, y + 2 * header))
    return canvas


def save_gif(frames, path):
    width, height = frames[0].size
    samples = frames[::6]
    swatches = Image.new("RGB", (width, height * len(samples)))
    for i, frame in enumerate(samples):
        swatches.paste(frame, (0, i * height))
    palette = swatches.quantize()
    indexed = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
    durations = [40 if i % 3 == 2 else 30 for i in range(len(frames))]
    indexed[0].save(path, save_all=True, append_images=indexed[1:], duration=durations, loop=0)


def true_form_board():
    size = (155, 128)
    clips = [atlas_frames(suffix) for suffix in ("idle", "liquefy", "vanish")]
    labels = ("대기", "변신 직전 영체화", "소멸")
    background = capture("defeat", 53, (421, 143, 576, 271))
    frames = []
    for i in range(FRAME_COUNT):
        indices = (i % len(clips[0]), max(0, i - 9), max(0, i - 9))
        panels = []
        for label, clip, index in zip(labels, clips, indices, strict=True):
            panel = background.copy()
            panel.alpha_composite(clip[min(index, len(clip) - 1)], (13, 0))
            panels.append((label, panel))
        defeat = capture("defeat", i, (223, 134, 393, 274)).resize(size, Image.Resampling.NEAREST)
        panels.append(("사망 연출", defeat))
        frames.append(board(panels, 4, size))
    TRUE_FORM.mkdir(parents=True, exist_ok=True)
    save_gif(frames, TRUE_FORM / "motions.gif")


def chain_animation():
    frames, ends = [], []
    with Image.open(STUDIES / "v004/chain-return.gif") as gif:
        for i in range(gif.n_frames):
            gif.seek(i)
            frame = gif.convert("RGB").resize((350, 144), Image.Resampling.NEAREST)
            frames.append(frame.crop((37, 0, 330, 144)))
            ends.append(gif.info["duration"] + (ends[-1] if ends else 0))
    return frames, ends


def weapon_board():
    labels = [
        ("장갑 베기", "hand"), ("회피 후 되베기", "counter"), ("활 발사", "bow"),
        ("대포 발사", "cannon"), ("형태 교체", "switch"),
    ]
    size = (266, 207)
    bounds = (151, 52, 493, 318)
    chain, ends = chain_animation()
    frames = []
    for i in range(FRAME_COUNT):
        panels = [
            (caption, capture(label, i, bounds).resize(size, Image.Resampling.NEAREST))
            for caption, label in labels
        ]
        chain_frame = chain[bisect_right(ends, (i * 1000 / 30) % ends[-1])]
        height = round(size[0] * chain_frame.height / chain_frame.width)
        panel = Image.new("RGB", size, "#251b2c")
        panel.paste(chain_frame.resize((size[0], height), Image.Resampling.NEAREST),
                    (0, (size[1] - height) // 2))
        panels.append(("사슬 시안", panel))
        frames.append(board(panels, 3, size))
    save_gif(frames, STUDIES / "weapon-motions.gif")


if __name__ == "__main__":
    true_form_board()
    weapon_board()

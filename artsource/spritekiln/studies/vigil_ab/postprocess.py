"""Reduce a two-pose ImageGen study to matched 64 px profiles and draw its comparison."""

import argparse
import json
import math
from pathlib import Path

from PIL import Image, ImageColor, ImageDraw, ImageFont


STUDY = Path(__file__).resolve().parent
TILE = 64
DIRECTIONS = ("e", "w")


def pose_frame(cell, marks, crown_row, cutoff, blade_tones):
    """Place hand-measured crown and sole landmarks with one uniform scale."""
    sole_x, sole_y = marks["sole"]
    samples_per_pixel = (sole_y - marks["crown_y"]) / (57 - crown_row)
    left = sole_x - 32 * samples_per_pixel
    top = sole_y - 57 * samples_per_pixel
    extent = (left, top, left + TILE * samples_per_pixel, top + TILE * samples_per_pixel)
    sampled = cell.convert("RGBa").transform(
        (TILE * 8, TILE * 8), Image.Transform.EXTENT, extent, Image.Resampling.BILINEAR
    )
    frame = sampled.resize((TILE, TILE), Image.Resampling.BOX).convert("RGBA")
    coverage = frame.getchannel("A")
    mask = coverage.point(lambda value: 255 if value >= cutoff else 0)
    # The sword tapers below one output pixel. Keep the best-covered sample
    # in each column along the measured blade without dilating the body.
    blade = [((x - left) / samples_per_pixel, (y - top) / samples_per_pixel) for x, y in marks["blade"]]
    (x0, y0), (x1, y1) = sorted(blade)
    for x in range(max(0, math.floor(x0)), min(TILE, math.ceil(x1))):
        line_y = y0 + (x + 0.5 - x0) * (y1 - y0) / (x1 - x0)
        rows = range(max(0, math.floor(line_y) - 1), min(TILE, math.ceil(line_y) + 1))
        best = max(rows, key=lambda y: coverage.getpixel((x, y)))
        if coverage.getpixel((x, best)) >= 18:
            mask.putpixel((x, best), 255)
            # Keep the steel distinct from similarly coloured hair and velvet at game scale.
            source_red = frame.getpixel((x, best))[0]
            tone = blade_tones[1] if source_red >= 150 else blade_tones[0]
            frame.putpixel((x, best), (*ImageColor.getrgb(tone), 255))
    frame.putalpha(mask)
    return frame


def apply_shared_palette(frames, swatches):
    # Match the sampled painting colours, then assign a compact ramp for each material.
    samples, inks = zip(*swatches)
    palette = Image.new("P", (1, 1))
    palette.putpalette([c for color in samples for c in ImageColor.getrgb(color)])
    ink_palette = [c for color in inks for c in ImageColor.getrgb(color)]
    for frame in frames:
        indices = frame.convert("RGB").quantize(palette=palette, dither=Image.Dither.NONE)
        indices.putpalette(ink_palette)
        result = Image.new("RGBA", frame.size)
        result.paste(indices.convert("RGB"), mask=frame.getchannel("A"))
        yield result


def korean_font(size, font_path):
    for name in (font_path, "malgun.ttf", "NotoSansCJK-Regular.ttc", "AppleSDGothicNeo.ttc"):
        if name:
            try:
                return ImageFont.truetype(str(name), size)
            except OSError:
                continue
    raise ValueError("Pass --font with the path to a Korean TrueType or OpenType font")


def comparison(columns, font_path):
    margin, column_width, top = 76, 276, 62
    canvas = Image.new("RGB", (margin + len(columns) * column_width + 12, top + 620), "#666972")
    draw = ImageDraw.Draw(canvas)
    heading = korean_font(19, font_path)
    caption = korean_font(14, font_path)
    for row, label in enumerate(("오른쪽", "왼쪽", "실제 크기")):
        draw.text((16, top + row * 268 + 13), label, font=caption, fill="#e3dfe3")
    for col, (name, profiles) in enumerate(columns):
        left = margin + col * column_width
        center = left + column_width // 2
        draw.text((center, 30), name, font=heading, anchor="mm", fill="#f0eced")
        for row, frame in enumerate(profiles):
            y = top + row * 268
            x = center - TILE * 2
            large = frame.resize((TILE * 4, TILE * 4), Image.Resampling.NEAREST)
            draw.line((x + 8, y + 57 * 4, x + large.width - 8, y + 57 * 4), fill="#82858d")
            canvas.paste(large, (x, y), large)
            canvas.paste(frame, (center - TILE - 8 + row * (TILE + 16), top + 540), frame)
        if col:
            draw.line((left, 18, left, canvas.height - 16), fill="#757781")
    draw.line((16, top - 5, canvas.width - 16, top - 5), fill="#858790")
    draw.line((16, top + 533, canvas.width - 16, top + 533), fill="#757781")
    return canvas


def read_profiles(folder):
    result = []
    for direction in DIRECTIONS:
        with Image.open(folder / f"idle_{direction}.png") as frame:
            if frame.size != (TILE, TILE):
                raise ValueError(f"Expected a 64 px frame in {folder}")
            result.append(frame.convert("RGBA"))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=STUDY / "imagegen.png")
    parser.add_argument("--calibration", type=Path, default=STUDY / "calibration.json")
    parser.add_argument("--font", type=Path)
    args = parser.parse_args()
    settings = json.loads(args.calibration.read_text(encoding="utf-8"))
    with Image.open(args.source) as original:
        source = original.convert("RGBA")
    if source.getchannel("A").getextrema() == (255, 255):
        raise ValueError("The reference sheet needs a transparent background")
    direct = read_profiles(STUDY / "direct")
    frames = []
    split = source.width // 2
    for index, direction in enumerate(DIRECTIONS):
        cell = source.crop((split if index else 0, 0, source.width if index else split, source.height))
        frames.append(pose_frame(
            cell, settings[direction], settings["crown_row"], settings["alpha_cutoff"], settings["blade_tones"]
        ))
    frames = list(apply_shared_palette(frames, settings["palette"]))
    output = STUDY / "imagegen_pixel"
    output.mkdir(exist_ok=True)
    for direction, frame in zip(DIRECTIONS, frames):
        frame.save(output / f"idle_{direction}.png")
    columns = [
        ("직전 시안", read_profiles(STUDY / "baseline")),
        ("A   SpriteKiln", direct),
        ("B   ImageGen 도트 후처리", frames),
    ]
    comparison(columns, args.font).save(STUDY / "comparison.png")


if __name__ == "__main__":
    main()

"""Build the two in-game Seal Chamber layers from the painted room."""

import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image, ImageDraw, ImageFilter


HERE = Path(__file__).resolve().parent
OUTPUT = HERE.parents[1] / "assets" / "rooms"
WIDTH = 640
WALL_HEIGHT = 68
FLOOR_HEIGHT = 211
SOURCE_WALL_EDGE = 310


def fit_source(image):
    # Register the wall foot at room y=112, just behind the actors' movement area.
    scale = 3
    width = WIDTH * scale
    wall_height = WALL_HEIGHT * scale
    floor_height = FLOOR_HEIGHT * scale
    artwork = Image.new("RGBA", (width, wall_height + floor_height))
    wall = image.crop((0, 0, image.width, SOURCE_WALL_EDGE))
    floor = image.crop((0, SOURCE_WALL_EDGE, image.width, image.height))
    artwork.paste(wall.resize((width, wall_height), Image.Resampling.LANCZOS))
    artwork.paste(floor.resize((width, floor_height), Image.Resampling.LANCZOS), (0, wall_height))
    # A transparent rim makes SpriteCut retain the complete illustration as its subject.
    padded = Image.new("RGBA", (artwork.width + 2, artwork.height + 2))
    padded.paste(artwork, (1, 1))
    return padded


def pixelate(source):
    height = WALL_HEIGHT + FLOOR_HEIGHT
    with TemporaryDirectory() as directory:
        incoming = Path(directory) / "paint.png"
        outgoing = Path(directory) / "pixel.png"
        source.save(incoming)
        subprocess.run(
            [sys.executable, "-m", "spritecut", "pixelate", str(incoming), str(outgoing),
             "--size", str(WIDTH), "--height", str(height)],
            check=True,
        )
        top = (WIDTH - height) // 2
        with Image.open(outgoing) as cell:
            return cell.crop((0, top, WIDTH, top + height)).convert("RGB")


def frame_floor(artwork):
    overlay = ImageDraw.Draw(artwork, "RGBA")
    bottom = 199
    shadow = (17, 14, 26, 45)
    overlay.rectangle((0, 0, 59, artwork.height - 1), fill=shadow)
    overlay.rectangle((580, 0, WIDTH - 1, artwork.height - 1), fill=shadow)
    overlay.rectangle((60, bottom, 579, artwork.height - 1), fill=shadow)
    overlay.line([(60, 0), (60, bottom), (579, bottom), (579, 0)], fill=(17, 14, 26, 85))
    overlay.line([(61, 0), (61, bottom - 1), (578, bottom - 1), (578, 0)], fill=(139, 109, 128, 38))


def build():
    with Image.open(HERE / "seal_chamber_source.png") as source:
        artwork = pixelate(fit_source(source))
    artwork = artwork.filter(ImageFilter.UnsharpMask(radius=0.7, percent=85, threshold=3))
    wall = artwork.crop((0, 0, WIDTH, WALL_HEIGHT))
    floor = artwork.crop((0, WALL_HEIGHT, WIDTH, artwork.height))
    frame_floor(floor)
    # Preserve small amber highlights on the wall and smooth palette steps under the actors.
    wall.quantize(colors=64, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE).save(
        OUTPUT / "seal_chamber_wall.png"
    )
    floor.quantize(colors=64, dither=Image.Dither.NONE).save(OUTPUT / "seal_chamber_floor.png")


if __name__ == "__main__":
    build()

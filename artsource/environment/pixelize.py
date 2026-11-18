"""Build the abbey and bridge textures from their archived paintings (Pillow 9.4)."""

from math import sqrt
from pathlib import Path

from PIL import Image, ImageFilter

SOURCE = Path(__file__).resolve().parent
DEST = SOURCE.parents[1] / "assets" / "environment"


def reduce_palette(image, colors):
    return image.convert("RGB").quantize(
        colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE
    ).convert("RGB")


def shallow_stone_normal(image):
    """Approximate fine relief on opaque masonry, keeping cutout edges neutral."""
    height = image.convert("L").filter(ImageFilter.GaussianBlur(1)).load()
    alpha = image.getchannel("A").load()
    normal = Image.new("RGB", image.size, (128, 128, 255))
    pixels = normal.load()
    for y in range(1, image.height - 1):
        for x in range(1, image.width - 1):
            if min(alpha[x - 1, y], alpha[x + 1, y], alpha[x, y - 1], alpha[x, y + 1], alpha[x, y]) < 250:
                continue
            nx = (height[x - 1, y] - height[x + 1, y]) / 96
            ny = (height[x, y + 1] - height[x, y - 1]) / 96
            length = sqrt(nx * nx + ny * ny + 1)
            pixels[x, y] = tuple(round(127.5 * (1 + v / length)) for v in (nx, ny, 1))
    return normal


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    with Image.open(SOURCE / "abbey_source.png") as source:
        sky = source.resize((704, 396), Image.Resampling.BOX)
        reduce_palette(sky, 56).save(DEST / "abbey.png")
    with Image.open(SOURCE / "causeway_source.png") as source:
        bridge = source.convert("RGBA").resize((960, 320), Image.Resampling.BOX)
        color = reduce_palette(bridge, 48)
        color.putalpha(bridge.getchannel("A").point(lambda a: 255 if a >= 128 else 0))
        color.save(DEST / "causeway.png")
        shallow_stone_normal(bridge).save(DEST / "causeway_normal.png")


if __name__ == "__main__":
    main()

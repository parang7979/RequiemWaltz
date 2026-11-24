"""Register the two generated monster views on the skeleton's pixel grid."""

from pathlib import Path
import json

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance
from scipy.ndimage import label


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "sources/v001"
MATERIAL = ROOT / "materials/v001"
CELL = (64, 64)
PIVOT = (32, 58)
DIRECTIONS = ("front_right", "back_right")
MONSTERS = {
    "crypt_warden": (47, 1.12, 100),
    "spore_lurker": (43, 1.09, 100),
    "ossuary_hexer": (45, 1.05, 100),
    "quartz_sentinel": (46, 1.02, 216),
}


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def source_view(art, index, key):
    height, brightness, cutoff = MONSTERS[key]
    x0, x1 = (0, art.width // 2) if index == 0 else (art.width // 2, art.width)
    view = art.crop((x0, 0, x1, art.height)).convert("RGBA")
    alpha = view.getchannel("A").point(lambda value: value if value >= cutoff else 0)
    view.putalpha(alpha)
    # The rear of the quartz helmet was drawn with its crystal ridge pointing left.
    mirrored = key == "quartz_sentinel" and index == 1
    if mirrored:
        view = view.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    x, y, right, bottom = view.getbbox()
    view = view.crop((x, y, right, bottom))
    scaled = view.resize((round(view.width * height / view.height), height), Image.Resampling.LANCZOS)
    pixels = np.asarray(ImageEnhance.Brightness(scaled).enhance(brightness)).copy()
    connected, _ = label(pixels[:, :, 3] >= 85, structure=np.ones((3, 3)))
    regions = np.bincount(connected.ravel())
    regions[0] = 0
    pixels[connected != regions.argmax()] = 0
    pixels[pixels[:, :, 3] > 0, 3] = 255
    foot_columns = np.nonzero(pixels[-4:, :, 3])[1]
    foot_center = (foot_columns.min() + foot_columns.max() + 1) / 2
    origin = (round(PIVOT[0] - foot_center), PIVOT[1] - height)
    cell = Image.new("RGBA", CELL)
    cell.paste(Image.fromarray(pixels), origin)
    return cell, {"source_half": index, "bounds_in_half": [x, y, right, bottom], "mirrored": mirrored,
                  "height": height, "alpha_cutoff": cutoff, "origin": origin}


def prepare():
    for key in MONSTERS:
        output = MATERIAL / key / "prepared"
        output.mkdir(parents=True, exist_ok=True)
        views = []
        with Image.open(SOURCE / "originals" / f"{key}.png") as art:
            for index, direction in enumerate(DIRECTIONS):
                cell, placement = source_view(art, index, key)
                name = f"{direction}.png"
                cell.save(output / name)
                views.append({"direction": direction, "file": name, "placement": placement})
        write(output / "views.json", {"version": 1, "cell": CELL, "pivot": PIVOT, "views": views})


def registered_preview(path, grid=False):
    scale = 5 if grid else 3
    width, height = CELL[0] * scale, CELL[1] * scale + 22
    preview = Image.new("RGBA", (len(MONSTERS) * width, 2 * height), "#302638")
    draw = ImageDraw.Draw(preview)
    for col, key in enumerate(MONSTERS):
        for row, direction in enumerate(DIRECTIONS):
            x, y = col * width, row * height
            draw.text((x + 8, y + 3), f"{key} / {direction}", fill="#dfc6b3")
            with Image.open(MATERIAL / key / "prepared" / f"{direction}.png") as cell:
                preview.alpha_composite(cell.resize((width, height - 22), Image.Resampling.NEAREST), (x, y + 22))
            draw.line((x + 8, y + 22 + PIVOT[1] * scale, x + width - 8, y + 22 + PIVOT[1] * scale), fill="#916d87")
            if grid:
                for pos in range(8, 64, 8):
                    mark = pos * scale
                    draw.line((x + mark, y + 22, x + mark, y + height - 1), fill="#786075")
                    draw.line((x + 4, y + 22 + mark, x + width - 4, y + 22 + mark), fill="#786075")
                    draw.text((x + mark, y + 22), str(pos), fill="#dfc6b3")
                    draw.text((x + 4, y + 22 + mark), str(pos), fill="#dfc6b3")
    preview.convert("RGB").save(path)


if __name__ == "__main__":
    prepare()

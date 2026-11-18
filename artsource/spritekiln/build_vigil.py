"""Build the two idle profiles with the Python interpreter of the pinned SpriteKiln checkout."""

import json
from pathlib import Path
import subprocess
import sys

from PIL import Image


SOURCE = Path(__file__).resolve().parent
SPEC = "specs/characters/vigil/vigil.yaml"
RENDER = SOURCE / "out" / "vigil"
RUNTIME = SOURCE.parents[1] / "assets" / "actors" / "vigil"


def kiln(*args):
    subprocess.run([sys.executable, "-m", "spritekiln", *args], cwd=SOURCE, check=True)


def main():
    kiln("validate", SPEC)
    kiln("render", SPEC, "-o", str(RENDER), "--jobs", "1")
    qa = json.loads((RENDER / "qa.json").read_text(encoding="utf-8"))
    if qa["errors"] or qa["warnings"]:
        raise ValueError(f"SpriteKiln QA needs review: {qa}")

    atlas = json.loads((RENDER / "vigil.json").read_text(encoding="utf-8"))
    RUNTIME.mkdir(parents=True, exist_ok=True)
    for suffix in ("", "_normal", "_emissive"):
        with Image.open(RENDER / f"vigil{suffix}.png") as sheet:
            for direction in atlas["spritekiln"]["directions"]:
                tag = f"idle_{direction}"
                rect = atlas["frames"][f"{tag}_0"]["frame"]
                x, y = rect["x"], rect["y"]
                bounds = (x, y, x + rect["w"], y + rect["h"])
                sheet.crop(bounds).save(RUNTIME / f"{tag}{suffix}.png")


if __name__ == "__main__":
    main()

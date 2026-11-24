"""Bake the v004 chain spirit and publish the fourth Requiem weapon."""

from itertools import accumulate
from pathlib import Path
import json
import math
from shutil import copyfile
import subprocess
import sys
from tempfile import TemporaryDirectory

from PIL import Image

from build_requiem_forms import CHARACTER, RUNTIME, mesh, publish_chain, write_json


MATERIAL = CHARACTER / "materials/v009/prepared"
VERSION = CHARACTER / "motions/requiem_chain/v001"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def deform(point, pivot, phase, extent, pull):
    x, y = (coordinate - anchor for coordinate, anchor in zip(point, pivot, strict=True))
    tail = max(0.0, min(1.0, (22 - x) / 47))
    fold = phase - x * .12
    crest = math.sin(fold) - math.sin(-x * .12)
    x += 1.0 * crest * tail + pull * (1 - tail)
    y += (1.75 * crest + pull * .35) * tail
    width = extent + .23 * math.sin(extent * math.pi)
    return [round(pivot[0] + x * width, 4), round(pivot[1] + y * extent ** 1.35, 4)]


def samples(motion):
    idle = motion["idle_ms"]
    action = motion["action_keys_ms"]
    cast = motion["cast"]
    result = {
        "idle": [(ms, elapsed / sum(idle) * math.tau, 1.0, 0.0)
                 for ms, elapsed in zip(idle, accumulate([0, *idle[:-1]]), strict=True)],
        "action": [(end - start, start / action[-1] * math.tau, 1.0,
                    3.2 * math.sin(math.pi * (start - cast["release"]) / (cast["catch"] - cast["release"]))
                    if cast["release"] <= start <= cast["catch"] else 0.0)
                   for start, end in zip(action, action[1:])],
    }
    for name in ("enter", "exit"):
        result[name] = [(ms, 0.0, extent, 0.0) for ms, extent in motion[name]]
    return result


def bake():
    motion = read(VERSION / "motion.json")
    views = read(MATERIAL / "views.json")
    cell, pivot = views["cell"], views["pivot"]
    view = views["views"][0]
    color = MATERIAL / view["file"]
    with Image.open(color) as sprite:
        vertices, triangles = mesh(sprite, 5)

    clips, tracks = {}, {}
    with TemporaryDirectory(prefix="spritecut-chain-") as directory:
        stage = Path(directory)
        Image.new("RGBA", tuple(cell)).save(stage / "empty.png")
        for name, keys in samples(motion).items():
            elapsed = 0
            frames, sockets = [], []
            for duration, phase, extent, pull in keys:
                coords = [deform(point, pivot, phase, extent, pull) for point in vertices]
                frame = {"ms": duration, "vertices": coords if extent else vertices}
                if not extent:
                    frame["materials"] = {"color": "empty.png"}
                if name == "action" and elapsed == motion["cast"]["release"]:
                    frame["events"] = ["release"]
                landmarks = {}
                for key, point in view["landmarks"].items():
                    posed = deform(point, pivot, phase, extent, pull)
                    landmarks[key] = [round(value - origin, 4)
                                      for value, origin in zip(posed, pivot, strict=True)]
                sockets.append({**landmarks, "presence": extent})
                frames.append(frame)
                elapsed += duration
            clip_name = f"chain_{name}"
            clips[clip_name] = {"loop": name == "idle", "frames": frames}
            tracks[clip_name] = sockets
        recipe = {
            "version": 1, "cell": cell, "pivot": pivot,
            "uv": vertices, "triangles": triangles, "materials": {"color": color.as_posix()},
            "clips": clips,
        }
        recipe_path = stage / "bake.json"
        write_json(recipe_path, recipe, None)
        output = stage / "sheets"
        subprocess.run([sys.executable, "-m", "spritecut", "bake", recipe_path, output], check=True)
        sheets = VERSION / "sheets"
        sheets.mkdir(exist_ok=True)
        for file in output.iterdir():
            copyfile(file, sheets / file.name)
    write_json(VERSION / "tracks.json", tracks)


if __name__ == "__main__":
    bake()
    manifest = RUNTIME / "clips.json"
    bundle = read(manifest)
    publish_chain(bundle)
    write_json(manifest, bundle)

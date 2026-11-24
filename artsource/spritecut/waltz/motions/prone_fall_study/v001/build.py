"""Register original cels and bake the standalone Waltz prone-fall study."""

import argparse
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

import numpy as np
from PIL import Image
from spritecut.review.playback import read_clip


ROOT = Path(__file__).resolve().parent
CLIP = "prone_fall_study"
SAMPLES_PER_PIXEL = 2


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")


def read_cel(path, box):
    with Image.open(path) as source:
        cel = source.convert("RGBA").crop(box)
    if path.name == "prone.png":
        cel.putalpha(cel.getchannel("A").point(lambda alpha: alpha if alpha >= 24 else 0))
        return cel

    # The entry boards were painted over a green matte. Keep antialiased
    # coverage and remove reflected green from the edge pixels.
    rgba = np.asarray(cel).astype(np.int16)
    neutral_green = np.maximum(rgba[:, :, 0], rgba[:, :, 2])
    green_excess = rgba[:, :, 1] - neutral_green
    coverage = np.clip((100 - green_excess) / 75, 0, 1)
    rgba[:, :, 1] = np.minimum(rgba[:, :, 1], neutral_green)
    rgba[:, :, 3] = np.rint(rgba[:, :, 3] * coverage)
    return Image.fromarray(rgba.astype(np.uint8))


def register_pose(pose, cell):
    scale = pose["scale"]
    anchor_x, anchor_y = pose["points"][pose["anchor"]]
    target_x, target_y = pose["at"]
    points = {
        name: [
            round(target_x + (x - anchor_x) * scale, 2),
            round(target_y + (y - anchor_y) * scale, 2),
        ]
        for name, (x, y) in pose["points"].items()
    }

    source_box = pose["rect"]
    cel = read_cel(ROOT / "source" / pose["image"], source_box)
    alpha = np.asarray(cel.getchannel("A"))
    if any(np.any(edge >= 96) for edge in (alpha[0], alpha[-1], alpha[:, 0], alpha[:, -1])):
        raise ValueError(f"{pose['id']}: source crop intersects the silhouette")
    art_box = cel.getbbox()
    if art_box is None:
        raise ValueError(f"{pose['id']}: source cel is empty")

    samples = SAMPLES_PER_PIXEL
    art = cel.crop(art_box)
    x = round(samples * (target_x + (source_box[0] + art_box[0] - anchor_x) * scale))
    y = round(samples * (target_y + (source_box[1] + art_box[1] - anchor_y) * scale))
    art = art.resize(
        (round(samples * scale * art.width), round(samples * scale * art.height)),
        Image.Resampling.LANCZOS,
    )
    tile = Image.new("RGBA", (samples * cell[0], samples * cell[1]))
    if x < 0 or y < 0 or x + art.width > tile.width or y + art.height > tile.height:
        raise ValueError(f"{pose['id']}: registered cel exceeds the sheet cell")
    tile.paste(art, (x, y))
    return tile, points


def quad(left, top, width, height):
    return [
        [left, top],
        [left + width, top],
        [left + width, top + height],
        [left, top + height],
    ]


def compile_atlas(spec, working):
    cell = spec["cell"]
    poses = spec["poses"]
    oversampled_width, oversampled_height = [size * SAMPLES_PER_PIXEL for size in cell]
    source = Image.new("RGBA", (oversampled_width * len(poses), oversampled_height))
    uv, triangles, frames, tracks = [], [], [], []
    for index, pose in enumerate(poses):
        tile, points = register_pose(pose, cell)
        source_x = index * oversampled_width
        source.paste(tile, (source_x, 0))
        uv.extend(quad(source_x, 0, oversampled_width, oversampled_height))
        vertex = index * 4
        triangles.extend([[vertex, vertex + 1, vertex + 2], [vertex, vertex + 2, vertex + 3]])

        # Each exposure enables only its own painted cel in the source atlas.
        vertices = [[0, 0]] * (4 * len(poses))
        vertices[vertex : vertex + 4] = quad(0, 0, *cell)
        frames.append({"vertices": vertices, "ms": pose["ms"], "contacts": pose["contacts"]})
        tracks.append({"id": pose["id"], "points": points})

    source.save(working / "registered.png")
    recipe = {
        "version": 1,
        "cell": cell,
        "pivot": spec["pivot"],
        "materials": {"color": "registered.png"},
        "uv": uv,
        "triangles": triangles,
        "clips": {CLIP: {"columns": 3, "loop": False, "frames": frames}},
    }
    write_json(working / "recipe.json", recipe)
    return {
        "version": 1,
        "cell": cell,
        "pivot": spec["pivot"],
        "landmarks": list(tracks[0]["points"]),
        "frames": tracks,
    }


def run_spritecut(*arguments):
    subprocess.run([sys.executable, "-m", "spritecut", *map(str, arguments)], check=True)


def save_looping_preview(manifest, output):
    _, _, frames, durations = read_clip(manifest, CLIP)
    zoom = 3
    size = (frames[0].width * zoom, frames[0].height * zoom)
    playback = []
    for frame in frames:
        enlarged = frame.resize(size, Image.Resampling.NEAREST)
        panel = Image.new("RGB", size, "#302e39")
        panel.paste(enlarged, (0, 0), enlarged)
        playback.append(panel)
    playback[0].save(
        output, save_all=True, append_images=playback[1:], duration=durations, loop=0,
    )


def build(output):
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    spec = json.loads((ROOT / "poses.json").read_text(encoding="utf-8"))
    with TemporaryDirectory(dir=output) as temporary:
        working = Path(temporary)
        tracks = compile_atlas(spec, working)
        run_spritecut("bake", working / "recipe.json", output / "sheets")
        write_json(output / "tracks.json", tracks)
        manifest = output / "sheets" / "clips.json"
        previews = output / "previews"
        run_spritecut(
            "preview",
            manifest,
            previews,
            "--clip", CLIP,
            "--label", "Waltz: Prone fall",
            "--tracks", output / "tracks.json",
            "--axis", "torso:pelvis:neck",
            "--axis", "head:neck:crown",
            "--axis", "fall:boot:crown",
            "--check-gaps",
        )
        save_looping_preview(manifest, previews / "looping.gif")
        # Match the repository's LF convention on Windows as well.
        for path in (manifest, previews / "index.json"):
            path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="new output directory")
    build(parser.parse_args().output)

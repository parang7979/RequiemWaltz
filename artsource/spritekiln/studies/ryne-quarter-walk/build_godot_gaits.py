"""Build rest-part textures and the baked walk/run recipe using SpriteKiln."""
import json
import os
import subprocess

import numpy as np
from PIL import Image

import render_walk as walk
import render_run as run
from build import ORIGIN
from render_pixelated import GRIDS, register_pose
from spritekiln import spec
from spritekiln.anim import frames_of
from spritekiln.rig import Ctx

HERE = walk.HERE
GRID = GRIDS[56]
ROOT = HERE.parents[3]
OUTPUT = ROOT / "artsource/spritecut/ryne/gait-materials"
PIXEL = GRID.scale / walk.SCALE
ORIGIN_PX = ORIGIN + walk.SCALE * (np.array([16, 11]) - np.array([19, 4]) / GRID.scale)
TILE = 128


def cell(points):
    return (points - ORIGIN_PX) * PIXEL


def sparse_mesh(art):
    mesh = walk.SkinMesh(art, spacing=(28, 25))
    coverage = art.getchannel("A")
    kept = []
    for triangle in mesh.triangles:
        pts = mesh.vertices[list(triangle)]
        lo = np.floor(pts.min(axis=0) - 4).astype(int)
        hi = np.ceil(pts.max(axis=0) + 4).astype(int)
        if coverage.crop((*lo, *hi)).getbbox():
            kept.append(triangle)
    indices, compact = np.unique(kept, return_inverse=True)
    return mesh.vertices[indices], compact.ravel()


def samples(name, art):
    rig = spec.load(str(HERE / f"{name}.yaml"))
    cycle = frames_of(rig, "walk", 0)
    outlines = {s: walk.sole(art[s+"_leg"], joints[-1]) for s, joints in walk.LEGS.items()}
    for i in range(walk.FRAMES):
        # The archived run loop starts half a stride into the steady-speed section.
        s = (36 + i) / walk.FRAMES
        is_run = name == "run"
        sample = cycle[(36+i if is_run else i) % walk.FRAMES][0]
        env = run.gait_env(sample, s) if is_run else dict(sample)
        feet = {}
        contact = 0
        for side, offset, bit in [("near", 0, 1), ("far", 12, 2)]:
            if is_run:
                feet[side], planted = run.leg(s, side, outlines[side])
            else:
                feet[side] = walk.foot(i+offset, side, outlines[side])
                planted = (i+offset) % walk.FRAMES <= walk.CONTACT
            point = feet[side][0]
            env[side+"_target"] = [point[0], -point[1], 0]
            if planted:
                contact |= bit
        ctx = run.leg_context(rig, env, feet) if is_run else Ctx(rig, env)
        yield ctx, feet, contact


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    art = walk.pieces(source=register_pose(GRID, GRID.out/"quarter-pose.png"))
    atlas = Image.new("RGBA", (TILE * len(art), TILE))
    glow = Image.new("RGBA", atlas.size)
    meshes, uvs, tris = {}, [], []
    offset = 0
    extent = (*ORIGIN_PX, *(ORIGIN_PX+64/PIXEL))
    for col, (name, image) in enumerate(art.items()):
        vertices, indices = sparse_mesh(image)
        meshes[name] = vertices
        uvs.append(cell(vertices)*2 + [TILE*col, 0])
        tris.extend(indices + offset)
        offset += len(vertices)
        part = image.transform((TILE*2, TILE*2), Image.Transform.EXTENT, extent,
                               Image.Resampling.BILINEAR).resize((TILE,TILE), Image.Resampling.BOX)
        atlas.paste(part, (TILE*col, 0))
        if name == "body":
            with Image.open(OUTPUT/"color_emissive.png") as ribbon:
                emit = ribbon.resize((TILE,TILE), Image.Resampling.NEAREST)
            alpha = np.minimum(np.asarray(part.getchannel("A")), np.asarray(emit.getchannel("A")))
            emit.putalpha(Image.fromarray(alpha))
            glow.paste(emit, (TILE*col, 0))
    atlas.save(OUTPUT/"parts.png")
    glow.save(OUTPUT/"parts_emissive.png")
    subprocess.run(["python", str(ROOT/"tools/sprite_maps.py"), str(OUTPUT/"parts.png"),
                    "--frame-size", str(TILE), str(TILE)], check=True)

    recipes = ROOT / "artsource/spritecut/ryne"
    recipes.mkdir(parents=True, exist_ok=True)
    recipe = {"version": 1, "cell": [64,64], "materials": {},
              "uv": np.vstack(uvs).round(4).tolist(), "triangles": np.reshape(tris,(-1,3)).tolist(), "clips": {}}
    for channel, suffix in [("color",""),("normal","_normal"),("emissive","_emissive")]:
        recipe["materials"][channel] = os.path.relpath(OUTPUT/f"parts{suffix}.png", recipes).replace(os.sep,"/")
    for name in ("walk", "run"):
        meta = json.loads((GRID.out/f"{name}.json").read_text())
        keys, contacts = [], []
        for ctx, feet, contact in samples(name, art):
            shape = np.vstack([cell(walk.pose(verts, part, ctx, feet)) for part, verts in meshes.items()])
            keys.append(np.rint(shape*128).astype("<i2"))
            contacts.append(contact)
        recipe["pivot"] = meta["pivot"]
        recipe["clips"][name] = {"columns": 6, "cycle_advance_px": meta["cycle_advance_px"],
            "frames": [{"vertices": (points.astype(float)/128).tolist(), "ms": frame["ms"],
                        "contacts": [side for bit, side in [(1,"near"),(2,"far")] if contact & bit]}
                       for points,frame,contact in zip(keys,meta["frames"],contacts,strict=True)]}
    (recipes/"recipe.json").write_text(json.dumps(recipe,separators=(",",":"))+"\n", encoding="utf-8")
    print(f"{len(art)} parts, {offset} vertices, {len(tris)//3} triangles")


if __name__ == "__main__":
    main()

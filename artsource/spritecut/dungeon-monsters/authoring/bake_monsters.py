"""Rig four registered monster views and retarget the chamber skeleton's combat clips."""

import argparse
import sys
from pathlib import Path
from shutil import copyfile
from tempfile import TemporaryDirectory

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import binary_dilation, distance_transform_edt
from spritecut.animation.character import rest_geometry

from prepare_views import CELL, DIRECTIONS, MATERIAL, MONSTERS, PIVOT, ROOT, prepare, registered_preview, write

sys.path.insert(0, str(ROOT.parent / "crypt-skeleton/authoring"))
from bake_combat_v002 import MATERIAL as SKELETON_MATERIAL, compiler_character, spritecut
from bake_combat_v006 import REFERENCE, VERSION as SKELETON_MOTIONS, entry, project_floor, registered_pose, segment
from bake_combat_v004 import read, unit
from prepare_combat_v002 import PARENTS, DRAW_ORDER


PROJECT = ROOT.parents[2]
VERSION = ROOT / "motions/combat/v001"
SHEETS = VERSION / "sheets"
RUNTIME = PROJECT / "assets/actors/dungeon_monsters"
CLIPS = ("idle", "walk", "windup", "recover", "hit", "collapse")
SIDES = ("right", "left")
BAKE_CELL = (96, 96)
BAKE_PIVOT = (48, 58)
COLUMNS = 8
PADDING = np.asarray(BAKE_PIVOT) - PIVOT


def point_on_chain(grid, start, end):
    edge = end - start
    axis = (grid - start) @ edge / (edge @ edge)
    return np.linalg.norm(grid - start - np.clip(axis, 0, 1)[..., None] * edge, axis=-1)


def separate_parts(source, spec, rear):
    """Partition visible pixels by the authored joints and the approved head outline."""
    rows, cols = np.indices(CELL)
    grid = np.stack((cols + 0.5, rows + 0.5), axis=-1)
    pivots = {name: np.asarray(spec[name]) for name in ("pelvis", "chest", "head")}
    pivots["cloth"] = pivots["pelvis"]
    spine = point_on_chain(grid, pivots["head"], pivots["pelvis"] + [0, 2])
    low = rows >= pivots["pelvis"][1] - 3
    scores = {"chest": np.where(low, np.inf, spine * 0.70),
              "pelvis": np.where(low, spine * 0.76, np.inf),
              "cloth": np.full(CELL, np.inf), "head": np.full(CELL, np.inf)}
    for side, direction in zip(SIDES, ("right", "left") if rear else ("left", "right")):
        for chain, parts in (("arm", ("upper_arm", "forearm", "hand")),
                             ("leg", ("thigh", "shin", "boot"))):
            marks = [np.asarray(point) for point in spec[f"screen_{direction}_{chain}"]]
            for part, start, end in zip(parts, marks, marks[1:]):
                name = f"{side}_{part}"
                pivots[name] = start
                cost = point_on_chain(grid, start, end)
                early = rows + (5 if chain == "arm" else 2) < marks[0][1]
                late = rows > marks[-1][1] + 2 if chain == "arm" else False
                scores[name] = np.where(early | late, np.inf, cost)
    head = Image.new("L", CELL)
    ImageDraw.Draw(head).polygon([tuple(point) for point in spec["head_mask"]], fill=255)
    scores["head"] = np.where(np.asarray(head) > 0, -1, np.inf)
    names = tuple(scores)
    ownership = np.argmin(np.stack(tuple(scores.values())), axis=0)
    opaque = np.asarray(source)[..., 3] > 0
    masks = {name: (ownership == index) & opaque for index, name in enumerate(names)}
    return masks, pivots


def prepare_rig(key, specs, work):
    views = {}
    repairs = {}
    pivots = {}
    for direction in DIRECTIONS:
        source = Image.open(MATERIAL / key / "prepared" / f"{direction}.png").convert("RGBA")
        masks, pivots[direction] = separate_parts(source, specs[direction], direction == "back_right")
        parts = {}
        backing = {}
        for order, name in enumerate(DRAW_ORDER):
            mask = masks[name]
            if not mask.any():
                parts[name] = {"visibility": "hidden", "order": order, "pivot": pivots[direction][name].tolist()}
                continue
            path = f"{direction}_{name}.png"
            Image.fromarray(np.uint8(mask) * 255).save(work / path)
            parts[name] = {"mask": path, "order": order, "pivot": pivots[direction][name].tolist()}
            higher = np.any([np.zeros(CELL, dtype=bool), *(masks[other] for other in DRAW_ORDER[order + 1:])], axis=0)
            overlap = binary_dilation(mask, iterations=2) & ~mask & higher
            if overlap.any():
                _, near = distance_transform_edt(~mask, return_indices=True)
                colors = np.asarray(source)[tuple(near)]
                paint = np.where(overlap[..., None], colors, 0)
                backing_path = f"{direction}_{name}_backing.png"
                Image.fromarray(paint.astype(np.uint8)).save(work / backing_path)
                backing[name] = backing_path
        views[direction] = {"parts": parts}
        repairs[direction] = backing
    structure = [{"id": name, **({"parent": parent} if parent else {})} for name, parent in PARENTS.items()]
    write(work / "parts.json", {"version": 1, "parts": structure, "views": views})
    write(work / "repairs.json", {"version": 1, "views": repairs})
    spritecut("parts", work / "parts.json", work / "observed", "--views", MATERIAL / key / "prepared/views.json")
    spritecut("parts-repair", work / "observed/index.json", work / "repairs.json", work / "rig")
    return pivots, read(work / "rig/index.json")["views"]


def reference_motion(work):
    joints = read(SKELETON_MATERIAL / "joints.json")
    views = read(SKELETON_MATERIAL / "parts/index.json")["views"]
    guide = read(REFERENCE / "contact-poses.json")
    source_clips = read(SKELETON_MOTIONS / "sheets/clips.json")["clips"]
    rigs = {direction: entry(direction, work, views[direction]) for direction in DIRECTIONS}
    front_pieces = rigs["front_right"][2]
    face = next(vertices for name, vertices in front_pieces if name == "head")
    reference_face = {"vertices": face[:, :2], "pivot": joints["front_right"]["head"]["pivot"]}
    motions = {}
    for direction, (_, geometry, pieces) in rigs.items():
        rear = direction == "back_right"
        character = work / "rear_material/character.json" if rear else SKELETON_MATERIAL / "front_right_character.json"
        fall = f"collapse_{direction}"
        early = [np.asarray(frame["vertices"]) + PADDING for frame in geometry["clips"][fall]["frames"]]
        early_transforms = [registered_pose(pieces, vertices) for vertices in early]
        reference = read(REFERENCE / "tracks" / f"{fall}.json")["frames"][len(early):]
        late = []
        for index, (pose, _) in enumerate(project_floor(direction, guide, reference, joints[direction],
                                                      early_transforms[-1], pieces, reference_face)):
            vertices = np.asarray(pose["vertices"])
            show_face = rear and index >= 3
            matrices = registered_pose(pieces, vertices[:-len(face)] if rear else vertices)
            if show_face:
                matrices["head"] = np.linalg.lstsq(face, vertices[-len(face):], rcond=None)[0]
            late.append((matrices, show_face))
        motions[fall] = [(matrix, False) for matrix in early_transforms] + late
        for action in CLIPS[:-1]:
            name = f"{action}_{direction}"
            output = work / name
            recipe = SKELETON_MOTIONS.parents[0] / "v002/recipes" / f"{name}.json"
            spritecut("animate", character, recipe, output)
            clip = read(output / "recipe.json")["clips"][name]
            motions[name] = [(registered_pose(pieces, np.asarray(f["vertices"]) + PADDING), False)
                             for f in clip["frames"]]
    return motions, joints, source_clips


def transfer_pose(matrices, reference, rest, head_reference):
    """Keep the reference timing and transforms while registering each actor's own joints."""
    positions = {}
    rig = {part: np.asarray(joint["pivot"]) for part, joint in reference.items() if "pivot" in joint}
    rig["head"] = np.asarray(head_reference)

    def ref(part):
        return np.array([*rig[part], 1]) @ matrices[part]

    for part, parent in PARENTS.items():
        if parent is None:
            positions[part] = rest[part] + ref(part) - rig[part]
        else:
            # Preserve independent offsets such as neck settle before adding character proportions.
            relative = (rest[part] - rest[parent]) - (rig[part] - rig[parent])
            positions[part] = positions[parent] + ref(part) - ref(parent) + relative @ matrices[parent][:2]
    geometry = {}
    for side in SIDES:
        thigh, shin, boot = (f"{side}_{part}" for part in ("thigh", "shin", "boot"))
        ankle = rest[boot] + ref(boot) - rig[boot]
        knee = ref(shin) + 0.5 * ((positions[thigh] - ref(thigh)) + (ankle - ref(boot)))
        geometry[thigh] = segment(rest[thigh], rest[shin], positions[thigh], knee)
        seam = ankle + 0.85 * unit(ankle - knee)
        geometry[shin] = segment(rest[shin], rest[boot], knee, seam)
        positions[shin], positions[boot] = knee, ankle
    return positions, geometry


def reuse_head(geometry, pieces, output, front):
    front_path, front_geometry, front_pieces = front
    backing = set(front_geometry["underpaint_triangles"])
    tile, head = next((tile, vertices) for tile, (part, vertices) in enumerate(front_pieces)
                      if part == "head" and 2 * tile not in backing)
    for channel, filename in geometry["materials"].items():
        with Image.open(output / filename) as own, Image.open(front_path / front_geometry["materials"][channel]) as source:
            result = Image.new("RGBA", (own.width + CELL[0], own.height))
            result.paste(own)
            result.paste(source.crop((tile * CELL[0], 0, (tile + 1) * CELL[0], CELL[1])), (own.width, 0))
        result.save(output / filename)
    start = len(geometry["uv"])
    geometry["uv"].extend((head[:, :2] + [len(pieces) * CELL[0], 0]).tolist())
    geometry["triangles"].extend([[start, start + 1, start + 2], [start, start + 2, start + 3]])
    return head[:, :2]


def bake_direction(key, direction, work, motion, reference_joints, source_clips, rest_joints, rig, front):
    output, geometry, pieces = rig
    rear = direction == "back_right"
    alternate = reuse_head(geometry, pieces, output, front) if rear else None
    rest = rest_joints[direction]
    clips = {}
    all_frames = []
    for action in CLIPS:
        name = f"{action}_{direction}"
        source = source_clips[name]
        start = len(all_frames)
        for (matrices, show_face), reference in zip(motion[name], source["frames"], strict=True):
            face_direction = "front_right" if show_face else direction
            head_ref = reference_joints[face_direction]["head"]["pivot"]
            positions, segments = transfer_pose(matrices, reference_joints[direction], rest, head_ref)
            vertices = []
            for part, points in pieces:
                xy = points[:, :2]
                if part == "head" and show_face:
                    result = xy - 160
                elif part in segments:
                    result = segments[part](xy)
                else:
                    result = positions[part] + (xy - rest[part]) @ matrices[part][:2]
                vertices.extend(result.tolist())
            if rear:
                face = positions["head"] + (alternate - rest_joints["front_right"]["head"]) @ matrices["head"][:2]
                vertices.extend((face if show_face else alternate - 160).tolist())
            all_frames.append({"ms": reference["ms"], "contacts": reference["contacts"], "vertices": vertices})
        clips[name] = {"loop": source["loop"], "first": start}
    atlas = f"{key}_{direction}"
    recipe = {**geometry, "version": 1, "cell": BAKE_CELL, "pivot": BAKE_PIVOT,
              "clips": {atlas: {"columns": COLUMNS, "loop": False, "frames": all_frames}}}
    write(output / "recipe.json", recipe)
    baked = work / f"baked_{direction}"
    spritecut("bake", output / "recipe.json", baked)
    result = read(baked / "clips.json")["clips"][atlas]
    maps = result["maps"]
    for filename in maps.values():
        copyfile(baked / filename, SHEETS / filename)
    for action in CLIPS:
        name = f"{action}_{direction}"
        start = clips[name].pop("first")
        size = len(source_clips[name]["frames"])
        clips[name].update(maps=maps, frames=result["frames"][start:start + size])
    return clips


def bake():
    prepare()
    SHEETS.mkdir(parents=True, exist_ok=True)
    previews = VERSION / "previews"
    previews.mkdir(exist_ok=True)
    specs = read(MATERIAL / "landmarks.json")
    staging = PROJECT / ".local"
    staging.mkdir(exist_ok=True)
    manifest = {}
    with TemporaryDirectory(dir=staging, prefix="dungeon_monster_bake_") as scratch:
        work = Path(scratch)
        template = work / "reference"
        template.mkdir()
        motion, reference_joints, source_clips = reference_motion(template)
        for key in MONSTERS:
            production = work / key
            production.mkdir()
            rest_joints, views = prepare_rig(key, specs[key], production)
            rigs = {}
            for direction, view in views.items():
                target = production / direction
                target.mkdir()
                geometry, pieces = rest_geometry(production / "rig", view, CELL, production, {}, target)
                rigs[direction] = (target, geometry, pieces)
            clips = {}
            for direction, rig in rigs.items():
                clips.update(bake_direction(key, direction, production, motion, reference_joints, source_clips,
                                            rest_joints, rig, rigs["front_right"]))
            manifest.update({f"{key}_{name}": clip for name, clip in clips.items()})
    write(SHEETS / "clips.json", {"version": 1, "cell": BAKE_CELL, "pivot": BAKE_PIVOT, "clips": manifest})
    registered_preview(previews / "roster.png")
    review_motion(manifest, previews / "combat.gif")


def review_motion(clips, path):
    titles = ("Crypt Warden", "Spore Lurker", "Ossuary Hexer", "Quartz Sentinel")
    sources = {(key, view): Image.open(SHEETS / f"{key}_{view}_color.png").convert("RGBA")
               for key in MONSTERS for view in DIRECTIONS}
    panels = []
    durations = []
    for action in CLIPS:
        lead = clips[f"crypt_warden_{action}_front_right"]
        for index, lead_frame in enumerate(lead["frames"]):
            panel = Image.new("RGBA", (364, 205), "#302638")
            draw = ImageDraw.Draw(panel)
            draw.text((9, 4), "attack" if action == "recover" else action, fill="#eed6c4")
            for column, (key, title) in enumerate(zip(MONSTERS, titles)):
                x = column * 91
                draw.text((x + 7, 18), title, fill="#eed6c4")
                for row, view in enumerate(DIRECTIONS):
                    y = 21 + row * 82
                    frame = clips[f"{key}_{action}_{view}"]["frames"][index]
                    left, top = frame["x"], frame["y"]
                    cel = sources[key, view].crop((left, top, left + BAKE_CELL[0], top + BAKE_CELL[1]))
                    draw.line((x + 7, y + BAKE_PIVOT[1], x + 86, y + BAKE_PIVOT[1]), fill="#765976")
                    panel.alpha_composite(cel, (x - 2, y))
            panels.append(panel.convert("RGB").resize((728, 410), Image.Resampling.NEAREST))
            durations.append(lead_frame["ms"])
    panels[0].save(path, save_all=True, append_images=panels[1:], duration=durations, loop=0, disposal=2)


def publish():
    RUNTIME.mkdir(parents=True, exist_ok=True)
    for key in MONSTERS:
        for direction in DIRECTIONS:
            name = f"{key}_{direction}"
            copyfile(SHEETS / f"{name}_color.png", RUNTIME / f"{name}.png")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--publish", action="store_true", help="copy the approved color atlases to Godot")
    if parser.parse_args().publish:
        publish()
    else:
        bake()

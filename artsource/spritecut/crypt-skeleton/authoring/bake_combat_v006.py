"""Transfer the v004 backward fall to the original v002 skeleton cutouts."""

from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
from PIL import Image, ImageDraw
from spritecut.animation.character import rest_geometry

from bake_combat_v002 import MATERIAL, compiler_character
from bake_combat_v004 import VERSION as REFERENCE, cells, read, registered_landmarks, screen_turn, unit
from build_crypt_skeleton import CELL, DIRECTIONS, GROUND, PROJECT, spritecut, write


VERSION = REFERENCE.with_name("v006")
ENTRY_FRAMES = 4
SIDES = ("right", "left")


def segment(start, end, at, to, width=1.0):
    """Map a cutout's two joint points while preserving its transverse width."""
    source = end - start
    axis = unit(source)
    perpendicular = np.array([-axis[1], axis[0]])
    target = to - at
    perpendicular_target = unit(np.array([-target[1], target[0]]))
    linear = np.outer(target / np.linalg.norm(source), axis) + width * np.outer(perpendicular_target, perpendicular)
    return lambda xy: at + (xy - start) @ linear.T


def entry(direction, work, view):
    character = compiler_character(direction, work)
    output = work / direction
    spritecut("animate", character, REFERENCE / "recipes" / f"entry_{direction}.json", output)
    compiled = read(output / "recipe.json")
    geometry, pieces = rest_geometry(MATERIAL / "parts", view, CELL, MATERIAL, {}, output)
    if compiled["uv"] != geometry["uv"] or compiled["triangles"] != geometry["triangles"]:
        raise ValueError("The source part channels differ from the compiled entry rig")
    return output, compiled, pieces


def add_face(geometry, pieces, output, front):
    """Append the existing front head surface for the rear roll's face-up frames."""
    front_dir, front_recipe, front_pieces = front
    head_tile, original = next((tile, vertex) for tile, (name, vertex) in enumerate(front_pieces) if name == "head")
    vertices = original[:, :2]
    tile_x = head_tile * CELL[0]
    face_uv = (tile_x, 0, tile_x + CELL[0], CELL[1])
    for name, filename in geometry["materials"].items():
        with Image.open(output / filename) as own, Image.open(front_dir / front_recipe["materials"][name]) as other:
            canvas = Image.new("RGBA", (own.width + CELL[0], own.height))
            canvas.paste(own)
            canvas.paste(other.crop(face_uv), (own.width, 0))
        canvas.save(output / filename)
    start = len(geometry["uv"])
    geometry["uv"].extend((vertices + [len(pieces) * CELL[0], 0]).tolist())
    geometry["triangles"].extend([[start, start + 1, start + 2], [start, start + 2, start + 3]])
    return vertices


def registered_pose(pieces, landed):
    """Recover the final standing articulation from the same mesh the baker used."""
    split = np.cumsum([len(vertices) for _, vertices in pieces])[:-1]
    transforms = {}
    for (name, rest), posed in zip(pieces, np.split(landed, split)):
        transforms[name] = np.linalg.lstsq(rest, posed, rcond=None)[0]
    return transforms


def turn_about(points, center, angle):
    return center + (points - center) @ screen_turn(angle).T


def bent_knee(hip, knee, ankle, posed_hip, progress):
    """Solve the knee from the two original bone lengths and a fixed ankle."""
    before = unit(ankle - hip)
    side = np.sign(np.dot(knee - hip, [-before[1], before[0]]))
    after = unit(ankle - posed_hip)
    gap = np.linalg.norm(ankle - posed_hip)
    lengths = np.array([np.linalg.norm(knee - hip), np.linalg.norm(ankle - knee)])
    first, second = lengths * max(0.86, gap / sum(lengths))
    distance = max(gap, abs(first - second) + 0.01)
    forward = (first**2 - second**2 + distance**2) / (2 * distance)
    bend = np.sqrt(max(0, first**2 - forward**2))
    solved = posed_hip + forward * after + side * bend * np.array([-after[1], after[0]])
    carry = knee + (posed_hip - hip) * 0.45
    return carry + (solved - carry) * progress


def project_floor(direction, guide, reference, joints, transforms, pieces, front_face):
    spec = guide["views"][direction]
    support = np.asarray(guide["support"])
    rest_frame = registered_landmarks(spec, support)
    reference_axis = unit(rest_frame["crown"] - support)
    reference_hip = np.mean(rest_frame["hips"], axis=0)
    rear = direction == "back_right"

    def mark(owner, field="pivot"):
        return np.array([*joints[owner][field], 1.0]) @ transforms[owner]

    hip_at_entry, neck_at_entry = mark("pelvis"), mark("head")
    head_up = np.array([0.0, -1.0]) @ transforms["head"][:2]
    for index, frame in enumerate(reference):
        points = frame["points"]
        stretch = np.eye(2) + (frame["upper_scale"] - 1) * np.outer(reference_axis, reference_axis)
        hip = support + screen_turn(frame["roll_deg"]) @ stretch @ (reference_hip - support)
        hip += spec["body_offsets"][index]
        neck = np.asarray(points["neck"])
        head = np.asarray(points["head"])
        torso = segment(hip_at_entry, neck_at_entry, hip, neck, width=0.95)

        limbs = {}
        tracked_limbs = {}
        for side in SIDES:
            thigh, shin, boot = (f"{side}_{name}" for name in ("thigh", "shin", "boot"))
            upper, middle, ankle = mark(thigh), mark(shin), mark(boot)
            new_upper = torso(upper)
            knee = bent_knee(upper, middle, ankle, new_upper, progress=min(1, (index + 1) / 3))
            seam = ankle + 0.85 * unit(mark(boot, "toe") - ankle)
            limbs[thigh] = segment(upper, middle, new_upper, knee)
            limbs[shin] = segment(middle, ankle, knee, seam)
            tracked_limbs[f"{side}_knee"] = knee.tolist()

        # Both meshes use existing skull colors. Narrow the turn before the rear surface rolls out of view.
        use_face = rear and index >= 3
        head_width = (0.96, 0.88, 0.76, 0.78, 0.87, 0.94, 0.94, 0.94)[index] if rear else 0.96
        head_axis = unit(np.asarray(points["crown"]) - head)
        crown = head + head_axis * 0.91
        head_pose = segment(neck_at_entry, neck_at_entry + head_up, head, crown, width=head_width)

        vertices = []
        for part, rest in pieces:
            placed = rest @ transforms[part]
            if part.endswith("_boot"):
                result = placed
            elif part in limbs:
                result = limbs[part](placed)
            elif part == "head":
                result = placed - 192 if use_face else head_pose(placed)
            else:
                side = part.split("_", 1)[0]
                if "arm" in part or part.endswith("_hand"):
                    shoulder = torso(mark(f"{side}_upper_arm"))
                    swing = (-1 if side == "right" else 1) * (5 + index * 1.6)
                    result = turn_about(torso(placed), shoulder, swing)
                else:
                    result = torso(placed)
            vertices.extend(result.tolist())
        if rear:
            face_pivot = np.asarray(front_face["pivot"])
            face = segment(face_pivot, face_pivot + [0, -1], head, crown, width=head_width)
            vertices.extend((face(front_face["vertices"]) if use_face else front_face["vertices"] - 192).tolist())

        tracks = {**points, **tracked_limbs, "pelvis": hip.tolist(), "head": head.tolist(),
                  "crown": (head + head_axis * 14.0).tolist()}
        for side in SIDES:
            tracks[f"{side}_foot"] = mark(f"{side}_boot", "heel").tolist()
        yield ({"ms": frame["ms"], "contacts": frame["contacts"], "vertices": vertices},
               {"ms": frame["ms"], "contacts": frame["contacts"], "points": tracks})


def pack_like_game(source, clip, destination, layout):
    """Keep Godot atlas rectangles and timing identical to the active collapse clip."""
    frames = clip["frames"]
    size = (max(f["x"] + f["w"] for f in layout), max(f["y"] + f["h"] for f in layout))
    for name in clip["maps"].values():
        with Image.open(source / name) as atlas:
            output = Image.new("RGBA", size)
            for frame, target in zip(frames, layout, strict=True):
                x, y, width, height = (frame[key] for key in ("x", "y", "w", "h"))
                if (width, height, frame["ms"]) != (target["w"], target["h"], target["ms"]):
                    raise ValueError("The candidate clip differs from the game cell size or timing")
                output.paste(atlas.crop((x, y, x + width, y + height)), (target["x"], target["y"]))
        output.save(destination / name)
    return [dict(frame, x=target["x"], y=target["y"]) for frame, target in zip(frames, layout, strict=True)]


def bake():
    guide = read(REFERENCE / "contact-poses.json")
    baseline = read(REFERENCE / "sheets/clips.json")
    joints = read(MATERIAL / "joints.json")
    views = read(MATERIAL / "parts/index.json")["views"]
    sheets = VERSION / "sheets"
    sheets.mkdir(exist_ok=True)
    clips = {}
    padding = np.asarray(guide["pivot"]) - GROUND
    staging = PROJECT / ".local"
    staging.mkdir(exist_ok=True)
    with TemporaryDirectory(dir=staging, prefix="crypt-original-fall-") as directory:
        work = Path(directory)
        rigs = {direction: entry(direction, work, views[direction]) for direction in DIRECTIONS}
        for direction, (output, geometry, pieces) in rigs.items():
            name = f"collapse_{direction}"
            reference = read(REFERENCE / "tracks" / f"{name}.json")
            early = geometry["clips"][name]["frames"]
            for frame in early:
                frame["vertices"] = (np.asarray(frame["vertices"]) + padding).tolist()
            transforms = registered_pose(pieces, np.asarray(early[-1]["vertices"]))
            face = None
            if direction == "back_right":
                vertices = add_face(geometry, pieces, output, rigs["front_right"])
                face = {"vertices": vertices, "pivot": joints["front_right"]["head"]["pivot"]}
                for frame in early:
                    frame["vertices"].extend((vertices - 192).tolist())
            late, tracks = zip(*project_floor(direction, guide, reference["frames"][ENTRY_FRAMES:],
                                             joints[direction], transforms, pieces, face))
            geometry["clips"][name]["frames"] = early + list(late)
            geometry.update(cell=guide["cell"], pivot=guide["pivot"])
            mesh = output / "transferred.json"
            write(mesh, geometry)
            baked = work / f"baked_{direction}"
            spritecut("bake", mesh, baked)
            clip = read(baked / "clips.json")["clips"][name]
            clip["frames"] = pack_like_game(baked, clip, sheets, baseline["clips"][name]["frames"])
            clips[name] = {**clip, "cell": guide["cell"], "pivot": guide["pivot"]}
            write(VERSION / "tracks" / f"{name}.json", {**reference, "frames": reference["frames"][:ENTRY_FRAMES] + list(tracks)})
    write(sheets / "clips.json", {**baseline, "clips": {**baseline["clips"], **clips}})
    compare(baseline["clips"], clips)


def compare(before, after):
    output = VERSION / "previews"
    output.mkdir(exist_ok=True)
    pairs = [(cells(REFERENCE / "sheets", before[name]), cells(VERSION / "sheets", clip))
             for name, clip in after.items()]
    frames = []
    durations = [frame["ms"] for frame in next(iter(after.values()))["frames"]]
    for index in range(len(durations)):
        panel = Image.new("RGBA", (200, 216), "#292334")
        pen = ImageDraw.Draw(panel)
        for y, label in ((0, "v004 reference"), (106, "v006 original parts")):
            pen.text((5, y + 1), label, fill="#eacdb7")
            for column, title in enumerate(("front", "rear")):
                x = column * 100
                pen.text((x + 62, y + 10), title, fill="#d1a6bd")
                pen.line((x + 4, y + 75, x + 96, y + 75), fill="#6c546e")
                panel.alpha_composite(pairs[column][int(y > 0)][index], (x, y + 17))
        frames.append(panel.convert("RGB").resize((600, 648), Image.Resampling.NEAREST))
    frames[-1].save(output / "original-parts-end.png")
    durations[-1] += 380
    frames[0].save(output / "original-parts-comparison.gif", save_all=True, append_images=frames[1:],
                   duration=durations, disposal=2, loop=0)


if __name__ == "__main__":
    bake()

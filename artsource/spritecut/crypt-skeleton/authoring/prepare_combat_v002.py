"""Separate the two combat views of the authored v002 skeleton."""

from pathlib import Path
import json
import shutil
from tempfile import TemporaryDirectory

from PIL import Image, ImageChops, ImageDraw

from build_crypt_skeleton import CELL, DIRECTIONS, ROOT, spritecut, write


MATERIAL = ROOT / "materials/v002"
PREPARED = MATERIAL / "prepared"
MASKS = MATERIAL / "masks"
REPAIRS = MATERIAL / "underpaint"

PARENTS = {
    "pelvis": None, "chest": "pelvis", "head": "chest", "cloth": "pelvis",
    "right_thigh": "pelvis", "right_shin": "right_thigh", "right_boot": "right_shin",
    "left_thigh": "pelvis", "left_shin": "left_thigh", "left_boot": "left_shin",
    "right_upper_arm": "chest", "right_forearm": "right_upper_arm", "right_hand": "right_forearm",
    "left_upper_arm": "chest", "left_forearm": "left_upper_arm", "left_hand": "left_forearm",
}

DRAW_ORDER = (
    "left_thigh", "left_shin", "left_boot", "right_thigh", "right_shin", "right_boot",
    "left_upper_arm", "left_forearm", "left_hand", "pelvis", "cloth", "chest",
    "head", "right_upper_arm", "right_forearm", "right_hand",
)

MASK_PRIORITY = (
    "head", "right_hand", "left_hand", "right_boot", "left_boot",
    "right_forearm", "left_forearm", "right_upper_arm", "left_upper_arm",
    "right_shin", "left_shin", "right_thigh", "left_thigh", "cloth",
)

REPAIR_COLORS = {
    "left_upper_arm": "#806177",
    "right_thigh": "#8e6e75",
    "left_thigh": "#795d70",
    "chest": "#614758",
}


def polygon(points):
    mask = Image.new("L", CELL)
    ImageDraw.Draw(mask).polygon([tuple(point) for point in points], fill=255)
    return mask


def split_masks(source, joints):
    solid = source.getchannel("A").point(lambda alpha: 255 if alpha else 0)
    remaining = solid.copy()
    masks = {}
    for name in MASK_PRIORITY:
        masks[name] = ImageChops.darker(remaining, polygon(joints[name]["polygon"]))
        remaining = ImageChops.subtract(remaining, masks[name])
    waist = Image.new("L", CELL)
    ImageDraw.Draw(waist).rectangle((0, 41, 63, 63), fill=255)
    masks["pelvis"] = ImageChops.darker(remaining, waist)
    masks["chest"] = ImageChops.subtract(remaining, masks["pelvis"])
    return masks


def repairs_for(direction, source, joints, masks):
    result = {}
    for name, points in joints["repairs"].items():
        later = DRAW_ORDER[DRAW_ORDER.index(name) + 1:]
        occluded = Image.new("L", CELL)
        for other in later:
            occluded = ImageChops.lighter(occluded, masks[other])
        exposed = ImageChops.darker(polygon(points), occluded)
        color = Image.new("RGBA", CELL, REPAIR_COLORS[name])
        color.putalpha(ImageChops.multiply(exposed, source.getchannel("A")))
        if not color.getbbox():
            continue
        filename = REPAIRS / f"{direction}_{name}.png"
        color.save(filename)
        result[name] = filename.relative_to(MATERIAL).as_posix()
    return result


def main():
    MASKS.mkdir(exist_ok=True)
    REPAIRS.mkdir(exist_ok=True)
    joints = json.loads((MATERIAL / "joints.json").read_text(encoding="utf-8"))
    parts = [{"id": name, **({"parent": parent} if parent else {})}
             for name, parent in PARENTS.items()]
    views, repairs = {}, {}
    for direction in DIRECTIONS:
        with Image.open(PREPARED / f"{direction}.png") as original:
            source = original.convert("RGBA")
        matched = split_masks(source, joints[direction])
        frame = {}
        for order, name in enumerate(DRAW_ORDER):
            filename = MASKS / f"{direction}_{name}.png"
            assert matched[name].getbbox(), (direction, name)
            matched[name].save(filename)
            info = joints[direction][name]
            frame[name] = {"mask": filename.relative_to(MATERIAL).as_posix(), "order": order,
                           "pivot": info["pivot"], "landmarks": {
                               key: info[key] for key in ("heel", "toe", "tip") if key in info
                           }}
        views[direction] = {"parts": frame}
        repairs[direction] = repairs_for(direction, source, joints[direction], matched)
    write(MATERIAL / "parts.json", {"version": 1, "parts": parts, "views": views})
    write(MATERIAL / "repairs.json", {"version": 1, "views": repairs})
    with TemporaryDirectory(dir=MATERIAL, prefix=".parts-") as directory:
        work = Path(directory)
        spritecut("parts", MATERIAL / "parts.json", work / "observed", "--views", PREPARED / "views.json")
        spritecut("parts-repair", work / "observed/index.json", MATERIAL / "repairs.json", work / "repaired")
        shutil.copytree(work / "repaired", MATERIAL / "parts", dirs_exist_ok=True)
    for direction in DIRECTIONS:
        write(MATERIAL / f"{direction}_character.json", {
            "version": 1, "direction": direction, "views": "prepared/views.json",
            "parts": "parts/index.json",
        })
    shutil.copyfile(MATERIAL / "front_right_character.json", MATERIAL / "character.json")


if __name__ == "__main__":
    main()

"""Render the reference-painted skin on SpriteKiln's orthographic idle rig."""

import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from spritekiln import spec
from spritekiln.anim import frames_of
from spritekiln.render import Camera
from spritekiln.rig import Ctx, rest_env


HERE = Path(__file__).resolve().parent
CELL = (128, 192)
SAMPLE = 4
PIVOT = (67, 183)
# pose-source.png is the first figure of the sheet, starting at sheet x=30.
SOURCE_LEFT = 30
SHEET_TOP = -22
SHEET_LEFT = -4


def smooth(lo, hi, field):
    t = np.clip((field - lo) / (hi - lo), 0, 1)
    return t*t*(3 - 2*t)


def eye_paint(neutral, amount):
    if amount == 0:
        return neutral
    closed = Image.open(HERE / "eyelids-source.png").convert("RGB")
    face = neutral.copy()
    # Maps from the expression panel into the two independently foreshortened eyes.
    for ref, target, outline in [
        ((6, 0, 39, 29), (248, 141, 285, 172),
         [(248, 148), (255, 143), (267, 141), (279, 144), (284, 152),
          (283, 163), (276, 170), (258, 171), (252, 165)]),
        ((57, 0, 81, 29), (304, 141, 332, 171),
         [(304, 152), (311, 146), (321, 142), (330, 144), (331, 150),
          (327, 163), (324, 169), (309, 170), (304, 165)])]:
        x, y, right, bottom = target
        patch = closed.crop(ref).resize((right-x, bottom-y), Image.Resampling.BICUBIC)
        gate = Image.new("L", patch.size)
        ImageDraw.Draw(gate).polygon([(u-x, v-y) for u,v in outline], fill=255)
        if amount < 0.95:
            # Lower the open upper lid and compress the iris. No transparency crossfade.
            opened = neutral.crop((x-SOURCE_LEFT, y, right-SOURCE_LEFT, bottom)).convert("RGB")
            h = max(1, round(opened.height*(1-amount)))
            lowered = opened.resize((opened.width, h), Image.Resampling.BOX)
            patch.paste(lowered, (0, round((opened.height-h)*0.72)))
        face.paste(patch, (x-SOURCE_LEFT, y), gate)
    return face


def weights(x, y):
    # These fields are continuous through the neck, waist and wrists. The
    # root takes the remaining weight and thus fixes both soles to the ground.
    upper = 1-smooth(271, 378, y)
    head = 1-smooth(184, 213, y)
    pony_edge = np.interp(y, [0,65,108,153,190,225,265,313],
                          [232,223,199,201,195,180,166,153])
    tail = (1-smooth(pony_edge-6, pony_edge+5, x))*(1-smooth(304, 319, y))
    near = (1-smooth(220, 252, x))*smooth(203, 233, y)*(1-smooth(420, 431, y))
    far = smooth(327, 350, x)*smooth(201, 237, y)*(1-smooth(420, 431, y))
    rest = 1-tail
    face = rest*head
    rest = rest*(1-head)
    sleeve_near, sleeve_far = rest*near, rest*far
    rest = rest*(1-near-far)
    return dict(pony=tail, face=face, sleeve_near=sleeve_near, sleeve_far=sleeve_far,
                chest=rest*upper, hips=rest*(1-upper)*(1-smooth(383, 528, y)))


def plane(ctx, camera, name):
    bone = ctx.frame(name, name)
    points = [camera.project(bone.apply(np.array(p))) for p in [(0,0,0),(1,0,0),(0,1,0)]]
    origin, horizontal, vertical = np.asarray(points)
    return np.array([[horizontal[0]-origin[0], vertical[0]-origin[0], origin[0]],
                     [horizontal[1]-origin[1], vertical[1]-origin[1], origin[1]],
                     [0, 0, 1]])


def render():
    rig = spec.load(str(HERE / "idle.yaml"))
    camera = Camera.from_spec(rig)
    neutral = Image.open(HERE / "pose-source.png").convert("RGBA")
    rest = Ctx(rig, rest_env(rig, 0))
    # Source sheet pixels -> camera pixels, with the sheet's Y axis pointing down.
    cx, cy = camera.project(np.zeros(3))
    registration = np.array([[1/camera.scale,0,cx],[0,1/camera.scale,cy],[0,0,1]])
    y, x = np.indices((CELL[1]*SAMPLE, CELL[0]*SAMPLE), dtype=np.float32)
    x += SHEET_LEFT
    y += SHEET_TOP
    influence = weights(x,y)
    ribcage = np.exp(-((x-298)/39)**4)*smooth(214,236,y)*(1-smooth(259,290,y))
    reference = {name: plane(rest, camera, name) for name in influence}
    frames, durations = [], []
    eyes = {}
    for env, duration, _ in frames_of(rig, "idle", 0):
        state = Ctx(rig, env)
        sx, sy = x.copy(), y.copy()
        for name, weight in influence.items():
            matrix = (np.linalg.inv(registration) @ reference[name] @
                      np.linalg.inv(plane(state, camera, name)) @ registration)
            sx += weight*((matrix[0,0]-1)*x + matrix[0,1]*y + matrix[0,2])
            sy += weight*(matrix[1,0]*x + (matrix[1,1]-1)*y + matrix[1,2])
        # Inverse displacement of the fitted panel. Collar and waist stay pinned.
        breath = env["breath"]
        sx -= ribcage*((x-295)*.041 + .7)*breath
        sy += ribcage*3.6*breath
        blink = round(float(env["blink"]), 3)
        if blink not in eyes:
            eyes[blink] = np.asarray(eye_paint(neutral, blink))
        src = eyes[blink]
        ix, iy = np.rint(sx-SOURCE_LEFT).astype(int), np.rint(sy).astype(int)
        valid = (ix>=0)&(ix<src.shape[1])&(iy>=0)&(iy<src.shape[0])
        pixels = np.zeros((*valid.shape,4),dtype=np.uint8)
        pixels[valid] = src[iy[valid],ix[valid]]
        frame = Image.fromarray(pixels).resize(CELL, Image.Resampling.BOX)
        frame.putalpha(frame.getchannel("A").point(lambda a: 255 if a>=128 else 0))
        frames.append(frame)
        durations.append(duration)
    return frames, durations


def write_clip(frames, durations, destination):
    strip = Image.new("RGBA", (CELL[0]*8, CELL[1]*5))
    stops = []
    for i, frame in enumerate(frames):
        x,y = i%8*CELL[0], i//8*CELL[1]
        strip.paste(frame,(x,y))
        stops.append({"x":x,"y":y,"w":CELL[0],"h":CELL[1],"ms":durations[i]})
    strip.save(destination / "idle-sheet.png")
    data = {"animation":"idle","view":"front three-quarter","image":"idle-sheet.png",
            "loop": True, "cell":CELL, "pivot":PIVOT,"frames":stops}
    (destination / "idle.json").write_text(json.dumps(data, indent=2)+"\n",encoding="utf-8")
    bg = (39,32,45)
    previews = []
    for frame in frames:
        stage = Image.new("RGB", (344,404), bg)
        ground_y = 17 + PIVOT[1]*2
        ImageDraw.Draw(stage).line((27,ground_y,317,ground_y),fill=(72,59,78))
        stage.paste(frame.resize((256,384),Image.Resampling.NEAREST),(44,17),
                    frame.getchannel("A").resize((256,384),Image.Resampling.NEAREST))
        previews.append(stage)
    # One shared display palette keeps neighboring frames from changing hue.
    palette = Image.fromarray(np.concatenate([np.asarray(im) for im in previews[::5]],axis=1))
    palette = palette.quantize(256, dither=Image.Dither.NONE)
    indexed = [im.quantize(palette=palette,dither=Image.Dither.NONE) for im in previews]
    indexed[0].save(destination / "idle.gif",save_all=True,append_images=indexed[1:],
                    duration=durations,loop=0,optimize=False,disposal=1)


def export():
    write_clip(*render(), HERE)


if __name__ == "__main__":
    export()

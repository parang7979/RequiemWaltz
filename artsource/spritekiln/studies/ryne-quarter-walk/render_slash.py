"""Render a single planted, right-facing slash with the turnaround cutouts."""
import json
from math import cos, radians, sin

import numpy as np
from PIL import Image, ImageDraw
from spritekiln import spec
from spritekiln.rig import Ctx, rest_env

from render_walk import GROUND, HERE, LEGS, SCALE, SkinMesh, pieces, pose, rocker, smooth, sole
from build import ORIGIN

CELL = (240, 192)
OFFSET = np.array([190., 0.])
FRAME_MS = 30
END = 34

# Frame numbers include a brief loaded pose, a rapid release and a longer settle.
KEYS = np.array([0, 4, 8, 11, 13, 15, 17, 20, 25, 30, END])
TRACKS = {
    "shift":       [0, -15, -36, -39, -6, 48, 75, 75, 51, 12, 0],
    "lift":        [14, 27, 54, 59, 57, 50, 52, 53, 42, 23, 14],
    "pelvic_turn": [0, -5, -13, -13, 1, 15, 18, 16, 8, 1, 0],
    "lean":        [-.05, .04, .16, .17, .09, -.16, -.32, -.29, -.18, -.09, -.05],
    "twist":       [0, -.20, -.59, -.64, -.48, .26, .68, .93, .72, .13, 0],
    "upper":       [.17, -.38, -1.14, -1.38, -1.34, .19, 1.04, .94, .88, .50, .17],
    "elbow":       [.67, .87, .99, 1.03, 1.11, 1.84, 1.18, 1.34, 1.27, .93, .67],
    "arm_depth":   [0, 0, 0, 0, 0, .58, .06, .86, .93, .23, 0],
    "guard":       [.13, .38, .55, .59, .64, .12, -.77, -.91, -.34, .06, .13],
    "guard_elbow": [.63, .86, 1.18, 1.21, 1.19, 1.12, .91, .86, .86, .71, .63],
    "head":        [.035, -.02, -.09, -.105, -.10, .07, .18, .20, .13, .06, .035],
    "hair":        [0, .04, .11, .06, .02, -.16, -.34, -.38, .07, .045, 0],
    "tip_lag":     [0, .02, .09, .12, .075, -.02, -.15, -.28, -.12, .08, 0],
    "step":        [0, 7, 60, 105, 115, 115, 115, 115, 105, 38, 0],
    "foot_lift":   [0, 12, 32, 10, 0, 0, 0, 0, 14, 25, 0],
    "heel":        [0, 0, 0, 0, 5, 18, 30, 30, 18, 3, 0],
    "sweep":       [33, 70, 155, 177, 180, 112, 12, -76, -112, -21, 33],
    "pitch":       [.64, .25, -.12, -.10, -.055, -.025, .01, .035, .06, .48, .64],
}


def interpolate(values, t):
    # Monotone Hermite tangents preserve a planted foot and avoid snapping at keys.
    slopes = np.diff(values) / np.diff(KEYS)
    tangent = np.zeros(len(KEYS))
    for i, (a, b) in enumerate(zip(slopes, slopes[1:]), 1):
        if a*b > 0:
            tangent[i] = 2*a*b/(a+b)
    k = min(np.searchsorted(KEYS, t, side="right")-1, len(KEYS)-2)
    width = KEYS[k+1]-KEYS[k]
    u = (t-KEYS[k])/width
    return ((1+2*u)*(1-u)**2*values[k] + u*(1-u)**2*width*tangent[k]
            + u*u*(3-2*u)*values[k+1] + u*u*(u-1)*width*tangent[k+1])


def state(rig, soles, t, *, idle_right_foot=False):
    env = rest_env(rig)
    env.update({k: interpolate(v, t) for k,v in TRACKS.items()})
    # The elbow comes toward the viewer as the hand passes the front hip.
    env["forearm_pitch"] = -1.1*smooth((t-12.8)/1.2)*(1-smooth((t-14)/1.6))
    feet = {}
    for side, outline in soles.items():
        angle = radians(env["heel"]) if side == "near" and not idle_right_foot else 0.
        x = 157 if side == "near" else 251+env["step"]
        lift = 0 if side == "near" else env["foot_lift"]
        ankle = np.array([x, GROUND[side]-outline[:,1].max()-lift])+rocker(angle,side,outline)
        feet[side] = ankle, angle
        env[side+"_target"] = [ankle[0], -ankle[1], 0]
        hip_x = 254+env["shift"]+(-28+env["pelvic_turn"] if side=="near" else 26-env["pelvic_turn"])
        reach = sum(rig["ik"][side+"_leg"]["lengths"])*.997
        max_height = np.sqrt(max(0., reach**2-(ankle[0]-hip_x)**2))
        env["lift"] = max(env["lift"], ankle[1]-350-max_height)
    return env, Ctx(rig, env), feet


def blade_axis(env, ctx, feet, t):
    yaw = radians(env["sweep"])
    pitch = env["pitch"]
    depth = .32-.21*smooth((t-11)/3)*(1-smooth((t-26)/5))
    sweep = np.array([cos(yaw)*cos(pitch), sin(pitch)+depth*sin(yaw)*cos(pitch)])
    # Catch the blade with the arm at extension. Maintain that alignment until
    # recovery is almost over, then ease back to the original resting grip.
    catch = smooth((t-16)/3) * (1-smooth((t-29)/(END-29)))
    if catch == 0:
        return sweep
    anchors = np.array([[173.,305.], GRIP[0]])
    elbow, hand = pose(anchors, "near_arm", ctx, feet)
    forearm = (hand-elbow)/np.linalg.norm(anchors[1]-anchors[0])
    return sweep*(1-catch)+forearm*catch


WRIST = np.array([[139., 367.]])
GRIP = np.array([[134., 384.]])
BLADE_LENGTH = 212
HANDLE_FRACTION = .132


def grip(ctx, feet):
    return pose(GRIP, "near_arm", ctx, feet)[0] - ORIGIN + OFFSET


def draw_grasp(canvas, blade, ctx, feet, axis):
    hand = grip(ctx, feet)
    wrist = pose(WRIST, "near_arm", ctx, feet)[0] - ORIGIN + OFFSET
    fore = (hand-wrist)/np.linalg.norm(hand-wrist)
    across = np.array([fore[1], -fore[0]])
    pen = ImageDraw.Draw(canvas)
    def palm(poly, color):
        pen.polygon([tuple(wrist+x*across+y*fore) for x,y in poly], fill=color)

    # The palm overlaps the painted cuff. The handle sits in the palm, beneath
    # the folded fingers. It stays at the same socket even when viewed end-on.
    palm([(-13,-6),(12,-6),(15,8),(12,22),(4,28),(-8,27),(-16,15)], "#251a25")
    palm([(-10,-5),(10,-5),(12,8),(8,22),(-6,23),(-13,13)], "#49343f")
    palm([(-9,-4),(5,-4),(3,1),(-9,5)], "#765764")
    draw_blade(canvas,blade,hand,axis)
    normal = np.array([-axis[1],axis[0]])/np.linalg.norm(axis)
    for along, size in [(-10, .76),(-4, .89),(2, .99),(8, 1.)]:
        center = hand+along*axis
        def finger(poly,color):
            pen.polygon([tuple(center+x*axis+y*normal*size) for x,y in poly], fill=color)
        finger([(-4,-8),(0,-11),(4,-9),(5,2),(3,7),(-3,7),(-5,3)],"#271c26")
        finger([(-3,-7),(0,-9),(3,-7),(3,0),(-3,2)],"#58424c")
        finger([(-2,2),(3,0),(3,4),(0,6),(-2,5)],"#cb8e80")
    # A crossing thumb closes the grip on the emitter side.
    thumb = hand+7*axis
    outline = [(-5,-8),(0,-12),(8,-9),(10,-1),(6,3),(1,-3)]
    pen.polygon([tuple(thumb+x*axis+y*normal) for x,y in outline], fill="#30202a")
    pen.line([tuple(thumb+x*axis+y*normal) for x,y in [(0,-8),(4,-7),(7,-2)]],
             fill="#dca795",width=3)


def draw_blade(canvas, blade, hand, axis):
    # Project the long axis into depth, keeping the emitter's thickness legible.
    normal = np.array([-axis[1], axis[0]]) / np.linalg.norm(axis)
    scale = BLADE_LENGTH/blade.width
    linear = np.column_stack((axis, normal))*scale
    pivot = np.array([blade.width*HANDLE_FRACTION, blade.height*.53])
    inverse = np.linalg.inv(linear)
    offset = pivot-inverse@hand
    matrix = tuple(np.column_stack((inverse, offset)).flatten())
    canvas.alpha_composite(blade.transform(canvas.size, Image.Transform.AFFINE, matrix,
                                          Image.Resampling.BICUBIC))


def trail(canvas, rig, soles, t, *, idle_right_foot=False):
    # A narrow ribbon records the tip's actual swept path during the fastest frames.
    if not 14 <= t <= 19:
        return
    layer = Image.new("RGBA", canvas.size)
    pen = ImageDraw.Draw(layer)
    inner, outer = [], []
    times = np.linspace(max(12, t-3.0), t, 16)
    strength = min(1., (20-t)/3)
    for i, time in enumerate(times):
        env, ctx, feet = state(rig, soles, time,idle_right_foot=idle_right_foot)
        hand, axis = grip(ctx, feet), blade_axis(env, ctx, feet, time)
        tip = BLADE_LENGTH*(1-HANDLE_FRACTION)
        outer.append(tuple(hand+tip*axis))
        inner.append(tuple(hand+(tip-55*(i/(len(times)-1))**.7*strength)*axis))
    pen.polygon(outer+inner[::-1], fill=(27,205,132,round(130*strength)))
    pen.line(outer, fill=(147,255,206,round(235*strength)), width=5)
    canvas.alpha_composite(layer)


def render_frames(source=None, *, idle_right_foot=False):
    rig = spec.load(str(HERE/"slash.yaml"))
    art = pieces(turn=0.0 if idle_right_foot else 1.0,source=source)
    # Replace the open fingers only for this attack. Keep the painted wristband.
    arm = art["near_arm"]
    arm.paste((0,0,0,0),(0,369,arm.width,arm.height))
    meshes = {name:SkinMesh(im, spacing=(14,11)) for name,im in art.items()}
    soles = {s:sole(art[s+"_leg"], LEGS[s][-1]) for s in LEGS}
    blade = Image.open(HERE/"energy-blade.png").convert("RGBA")
    blade = blade.crop(blade.getchannel("A").point(lambda a: 255 if a>96 else 0).getbbox())
    frames, records = [], []
    for t in range(END+1):
        env,ctx,feet = state(rig,soles,t,idle_right_foot=idle_right_foot)
        canvas = Image.new("RGBA", tuple(n*SCALE for n in CELL))
        for name,mesh in meshes.items():
            points = pose(mesh.vertices,name,ctx,feet)
            if name == "near_arm":
                trail(canvas,rig,soles,t,idle_right_foot=idle_right_foot)
            # Position each painted layer in its own raster window on the wide attack cell.
            shift = round((points[:,0].min()+points[:,0].max())/2-235)
            local = mesh.draw(points-np.array([shift,0]))
            canvas.alpha_composite(local,(int(OFFSET[0])+shift,0))
            if name == "near_arm":
                draw_grasp(canvas,blade,ctx,feet,blade_axis(env,ctx,feet,t))
        frame = canvas.resize(CELL,Image.Resampling.BOX)
        left,top,right,bottom = frame.getchannel("A").getbbox()
        assert left>=2 and top>=2 and right<=CELL[0]-2 and bottom<=CELL[1]-2,(t,(left,top,right,bottom))
        frames.append(frame)
        records.append(dict(x=t%7*CELL[0],y=t//7*CELL[1],ms=FRAME_MS))
    assert np.array_equal(frames[0],frames[-1])
    return frames,records


def main():
    frames,records = render_frames()
    atlas = Image.new("RGBA",(CELL[0]*7,CELL[1]*5))
    pages = []
    for frame,record in zip(frames,records):
        atlas.paste(frame,(record["x"],record["y"]))
        page = Image.new("RGB", CELL, "#27202d")
        pen = ImageDraw.Draw(page)
        pen.line((10,184,230,184),fill="#514352")
        page.paste(frame,mask=frame.getchannel("A"))
        pages.append(page.resize((480,384),Image.Resampling.NEAREST))
    atlas.save(HERE/"horizontal-slash-sheet.png")
    meta = dict(image="horizontal-slash-sheet.png", cell=CELL, pivot=[115,183],
                loop=False, frames=records)
    (HERE/"horizontal-slash.json").write_text(json.dumps(meta,indent=2)+"\n")
    palette = Image.fromarray(np.concatenate([np.asarray(im) for im in pages[::3]], axis=1)).quantize(256)
    pages = [page.quantize(palette=palette,dither=Image.Dither.NONE) for page in pages]
    pages[0].save(HERE/"horizontal-slash.gif",save_all=True,append_images=pages[1:],
                  duration=[FRAME_MS]*(len(pages)-1)+[450],loop=0,optimize=False,disposal=1)


if __name__ == "__main__":
    main()

"""Author a phase-continuous acceleration, running stride and return to the walk."""
import json
from math import floor, pi, sin, cos

import numpy as np
from PIL import Image, ImageDraw
from spritekiln import spec
from spritekiln.anim import frames_of
from spritekiln.rig import Ctx

from render_sequence import read_clip
from render_walk import (CELL, FRAMES, GROUND, HERE, LEGS, PIVOT, SCALE, SkinMesh,
                         flex, native, pieces, pose, rocker, rotation, screen, smooth, sole)

RUN_STRIDE = 168
RUN_PERIOD_MS = 640


def easing_area(x):
    """Integral of a smooth step, including the constant continuation."""
    if x <= 0:
        return 0
    if x >= 1:
        return x-.5
    return x**3-.5*x**4


def pace(s):
    return smooth(s)-smooth(s-3)


def root(s):
    return 72*s+(RUN_STRIDE-72)*(easing_area(s)-easing_area(s-3))


def clock_ms(s):
    return 960*s+(RUN_PERIOD_MS-960)*(easing_area(s)-easing_area(s-3))


def plant(s,side):
    # Land under the runner. The fixed plant then travels behind the hip
    # relative to the moving torso before the heel folds in recovery.
    front = 290-36*pace(s) if side=="near" else 331-42*pace(s)
    return root(s)*SCALE+front


def leg(s,side,outline):
    offset = 0 if side=="near" else .5
    landing = floor(s+offset+1e-10)-offset
    phase = s-landing
    effort = pace(landing)
    if 0<=landing<1:
        # Anticipate the acceleration during this stance rather than leaving
        # the trailing leg planted until the timing of the preceding walk.
        effort = pace(landing+.45)
    support = (14/24)*(1-effort)+.265*effort
    airborne = max(0,(phase-support)/(1-support))
    u = phase/support*14
    heel,toe = (12,22) if side=="near" else (10,19)
    heel -= 10*pace(landing)
    toe += 27*effort
    if phase<=support:
        degrees = -heel*(1-smooth(u/3))+toe*smooth((u-9)/5)
    else:
        degrees = toe+(4+17*effort)*sin(pi*min(1,airborne/.4))-(toe+heel)*smooth((airborne-.12)/.75)
    angle = np.radians(degrees)
    anchor = plant(landing,side)
    anchor += (plant(landing+1,side)-anchor)*smooth(airborne)
    # Fold the heel behind the hip on recovery, then drive the knee forward
    # before opening the shin for touchdown. Keep the landing anchor fixed.
    backswing = max(0.,sin(2*pi*airborne))
    anchor -= 48*effort*backswing*sin(pi*airborne)
    # The advancing shin opens in flight, then retracts towards the contact.
    anchor += 32*effort*smooth((airborne-.42)/.28)*(1-smooth((airborne-.70)/.30))
    arc = sin(pi*airborne)
    walk_height = (42 if side=="near" else 36)*arc**1.7
    run_height = (172 if side=="near" else 164)*arc**1.08
    clearance = (1-effort)*walk_height+effort*run_height
    ankle = np.array([anchor-root(s)*SCALE,GROUND[side]-outline[:,1].max()-clearance])
    return (ankle+rocker(angle,side,outline),angle),phase<=support


def gait_env(sample, s):
    env = dict(sample)
    env["pace"] = w = pace(s)
    p = env["p"]
    env["lift"] = (1-w)*env["lift"]+w*(5+35*cos(2*p-1.19))
    env["swing"] = (1-w)*env["swing"]+w*cos(p+1.19)
    return env


def leg_context(rig, env, feet):
    ctx = Ctx(rig,env)
    # Limit the rise of the pelvis to the reach of the trailing ankle.
    lower = 0.
    for side,(ankle,_) in feet.items():
        hip = screen(ctx,side+"_hip")
        reach = sum(rig["ik"][side+"_leg"]["lengths"])*.999-0.05
        span = np.sqrt(max(0.,reach**2-(ankle[0]-hip[0])**2))
        lower = max(lower,ankle[1]-span-hip[1])
    if lower>0:
        env["lift"] += lower
        ctx = Ctx(rig,env)
    return ctx


def render_gait(walk,source=None):
    rig = spec.load(str(HERE/"run.yaml"))
    samples = frames_of(rig,"walk",0)
    art = pieces(source=source)
    meshes = {n:SkinMesh(im,spacing=(12,10) if n.endswith("leg") or n=="body" else (31,14))
              for n,im in art.items()}
    soles = {s:sole(art[s+"_leg"],LEGS[s][-1]) for s in LEGS}
    frames,records,previous = [],[],{}
    # A final half walking stride lets both feet acquire ordinary walk anchors.
    for i in range(109):
        s = i/FRAMES
        env = gait_env(samples[i%FRAMES][0], s)
        grounded,feet = [],{}
        for side,outline in soles.items():
            (target,angle),contact = leg(s,side,outline)
            feet[side] = target,angle
            env[side+"_target"] = [target[0],-target[1],0]
            if contact:
                grounded.append(side)
                if side in previous:
                    old_pos,old_a,old_x = previous[side]
                    mid = (old_a+angle)/2
                    j = (flex(outline,mid,side) @ rotation(mid)[1]).argmax()
                    point = outline[j:j+1]
                    px = (flex(point,angle,side) @ rotation(angle).T-
                          flex(point,old_a,side) @ rotation(old_a).T)[0,0]
                    slip = (target[0]-old_pos[0]+px)/SCALE+root(s)-old_x
                    if abs(slip)>.09:
                        raise ValueError(f"{side} boot lost its plant at frame {i}: {slip}")
                previous[side] = target,angle,root(s)
            else:
                previous.pop(side,None)
        ctx = leg_context(rig, env, feet)
        surface = Image.new("RGBA",(CELL[0]*SCALE,CELL[1]*SCALE))
        sole_gaps = {}
        for name,mesh in meshes.items():
            layer = mesh.draw(pose(mesh.vertices,name,ctx,feet))
            surface.alpha_composite(layer)
            if name.endswith("_leg"):
                side = name.split("_")[0]
                bottom = native(layer).getchannel("A").getbbox()[3]
                sole_gaps[side] = (183 if side=="near" else 181)-bottom
        frame = native(surface)
        box = frame.getchannel("A").getbbox()
        assert box and min(box[:2])>0 and box[2]<CELL[0] and box[3]<CELL[1], (i,box)
        if i in (0,108):
            assert np.array_equal(frame,walk[i%FRAMES]), f"Walk seam at {i}"
        if i==108:
            break
        frames.append(frame)
        ms = round(clock_ms((i+1)/FRAMES))-round(clock_ms(s))
        records.append(dict(x=i%12*CELL[0],y=i//12*CELL[1],w=CELL[0],h=CELL[1],
                            ms=ms,root_px=round(root(s),5),grounded=grounded,sole_gap_px=sole_gaps))
    assert np.array_equal(frames[36],frames[60])
    suspension = [min(r["sole_gap_px"].values()) for r in records[36:60] if not r["grounded"]]
    assert len(suspension)>=8 and min(suspension)>=2 and max(suspension)>=12, suspension
    return frames,records


def film(timeline,run_only=False):
    size = (360 if run_only else 804,400)
    bg = (39,32,45)
    swatches = Image.new("RGB",(8*CELL[0],5*CELL[1]),bg)
    for n,(im,_,_) in enumerate(timeline[::7]):
        swatches.paste(im,(n%8*CELL[0],n//8*CELL[1]),im)
    for i,color in enumerate(((69,57,71),(108,89,106))):
        ImageDraw.Draw(swatches).rectangle((i*16,0,i*16+15,15),fill=color)
    palette = swatches.quantize(256,dither=Image.Dither.NONE)
    film_frames,times = [],[]
    elapsed = written = 0
    for im,ms,world in timeline:
        page = Image.new("RGB",size,bg)
        draw = ImageDraw.Draw(page)
        camera = round(world*2*(1 if run_only else .69))
        for y,color in ((372,(69,57,71)),(376,(108,89,106))):
            draw.line((10,y,size[0]-10,y),fill=color)
            for x in range(22-camera%48,size[0]-10,48):
                if x>13:
                    draw.line((x,y+1,x-3,y+3),fill=color)
        art = im.resize((2*CELL[0],2*CELL[1]),Image.Resampling.NEAREST)
        origin = 46 if run_only else 8
        page.paste(art,(origin+round(world*2)-camera,10),art)
        film_frames.append(page.quantize(palette=palette,dither=Image.Dither.NONE))
        elapsed += ms
        tick = round(elapsed/10)*10
        times.append(tick-written)
        written = tick
    name = "run-right.gif" if run_only else "walk-run-walk-idle.gif"
    film_frames[0].save(HERE/name,save_all=True,append_images=film_frames[1:],
                        duration=times,disposal=1,optimize=False,**({"loop":0} if run_only else {}))


def main():
    idle,imeta = read_clip("idle")
    walk,wmeta = read_clip("walk-right")
    entry,emeta = read_clip("walk-start")
    stop,smeta = read_clip("walk-stop")
    gait,records = render_gait(walk)
    atlas = Image.new("RGBA",(12*CELL[0],9*CELL[1]))
    for im,r in zip(gait,records):
        atlas.paste(im,(r["x"],r["y"]))
    atlas.save(HERE/"walk-run-walk-sheet.png")
    meta = dict(image="walk-run-walk-sheet.png",cell=CELL,pivot=PIVOT,loop=False,
                advance_px=root(4.5),run_loop=dict(first=36,count=24,advance_px=RUN_STRIDE),
                next_walk_frame=12,frames=records)
    (HERE/"walk-run-walk.json").write_text(json.dumps(meta,indent=2)+"\n",encoding="utf-8")
    timeline = [(idle[i],r["ms"],0) for i,r in enumerate(imeta["frames"]) if i>=23]
    timeline.extend((im,r["ms"],r["root_px"]) for im,r in zip(entry,emeta["frames"]))
    world = emeta["advance_px"]
    timeline.extend((im,r["ms"],world+i*3) for i,(im,r) in enumerate(zip(walk,wmeta["frames"])))
    world += wmeta["cycle_advance_px"]
    timeline.extend((im,r["ms"],world+r["root_px"]) for im,r in zip(gait,records))
    world += root(4.5)
    for i in range(24):
        f = (i+12)%24
        timeline.append((walk[f],wmeta["frames"][f]["ms"],world+3*i))
    world += wmeta["cycle_advance_px"]
    timeline.extend((im,r["ms"],world+r["root_px"]) for im,r in zip(stop,smeta["frames"]))
    world += smeta["advance_px"]
    timeline.extend((im,r["ms"],world) for im,r in zip(idle,imeta["frames"]))
    film(timeline)
    film([(gait[i],records[i]["ms"],root(i/FRAMES)-root(1.5)) for i in range(36,60)],run_only=True)


if __name__=="__main__":
    main()

"""Build the second turnaround view on the same SpriteKiln/cutout pipeline as the profile."""
import json
import sys
from math import pi, sin
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from spritekiln import spec
from spritekiln.anim import frames_of
from spritekiln.rig import Ctx

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3]/"tools"))
from cutout.contact import contact_offset, sole_outline

sys.path.insert(0, str(HERE.parent / "ryne-turnaround-walk"))
from build import (ADVANCE, CELL, CONTACT, FRAMES, PIVOT, SCALE, SkinMesh, blend,
                   native, rigid, rotation, screen, segment, smooth)
from paint import pieces

LEGS = {
    "near": np.array([[226.,358.],[201.,494.],[157.,649.]]),
    "far": np.array([[280.,358.],[272.,497.],[251.,647.]])
}
ARMS = {"near": ([196,228],[173,305]), "far": ([289,231],[305,304])}
GROUND = {"near":705., "far":697.}


def sole(layer,ankle):
    return sole_outline(layer,ankle,first_row=635)


def flex(points,angle,side):
    # Coordinates relative to the ankle. Bend the toe box at the ball while
    # the heel and shaft retain the orientation of the rear of the shoe.
    ball = np.array([40.,48.]) if side=="near" else np.array([48.,46.])
    toe_angle = -max(0,angle)*.90*smooth((points[:,0]-ball[0]+8)/17)
    q = points-ball
    c,s = np.cos(toe_angle),np.sin(toe_angle)
    return np.column_stack((c*q[:,0]-s*q[:,1],s*q[:,0]+c*q[:,1]))+ball


def rocker(angle,side,outline):
    return contact_offset(outline,angle,lambda a: flex(outline,a,side) @ rotation(a).T)


def foot(f,side,outline):
    f = f % FRAMES
    t = max(0,(f-CONTACT)/(FRAMES-CONTACT))
    heel,toe = (12,22) if side=="near" else (10,19)
    if f<=CONTACT:
        angle = -heel*(1-smooth(f/3)) + toe*smooth((f-9)/5)
    else:
        angle = toe + 4*sin(pi*min(1,t/.4)) - (toe+heel)*smooth((t-.12)/.75)
    angle = np.radians(angle)
    stride = t*t*(3-2*t)
    front = 290 if side=="near" else 331
    lift = 42 if side=="near" else 36
    target = np.array([front-ADVANCE*f+ADVANCE*FRAMES*stride,
                       GROUND[side]-outline[:,1].max()-lift*sin(pi*t)**1.7])
    return target+rocker(angle,side,outline),angle


def pose(vertices,name,ctx,feet,settled=1.0):
    x,y = vertices.T
    def thigh(side):
        hip,knee,_ = LEGS[side]
        return segment(vertices,hip,knee,screen(ctx,side+"_hip"),screen(ctx,side+"_knee"))

    def shorts(trunk):
        across = smooth((x-239)/43)
        attached = blend(thigh("near"),thigh("far"),across)
        hem = smooth((y-331)/47)*(.52+.48*smooth(abs(x-259)/29))
        return blend(trunk,attached,hem)

    if name.endswith("leg"):
        side = name.split("_")[0]
        hip,knee,ankle = LEGS[side]
        target,angle = feet[side]
        h,k,a = [screen(ctx,side+"_"+j) for j in ("hip","knee","ankle")]
        k = knee*(1-settled)+k*settled
        if np.linalg.norm(a-target)>.01:
            raise ValueError(f"{side} ankle cannot reach {target}")
        upper = segment(vertices,hip,knee,h,k)
        shin = segment(vertices,knee,ankle,k,a)
        garment = blend(vertices,shorts(rigid(ctx,"chest",[254,358],vertices)),settled)
        upper = blend(garment,upper,smooth((y-363)/39))
        boot = flex(vertices-ankle,angle,side) @ rotation(angle).T + a
        return blend(blend(upper,shin,smooth((y-knee[1]+25)/50)),
                     boot,smooth((y-608)/40))
    if name.endswith("arm"):
        side = name.split("_")[0]
        shoulder,elbow = ARMS[side]
        upper = rigid(ctx,side+"_arm",shoulder,vertices)
        fore = rigid(ctx,side+"_forearm",elbow,vertices)
        return blend(upper,fore,smooth((y-elbow[1]+13)/27))
    if name=="pouch":
        return rigid(ctx,"pouch",[227,327],vertices)
    trunk = shorts(rigid(ctx,"chest",[254,358],vertices))
    # Local fabric response falls to zero at the collar, side seams and belt.
    p = ctx.env["p"]
    volume = np.exp(-((x-267)/38)**4)*smooth((y-220)/22)*(1-smooth((y-264)/31))
    recovery = np.sin(2*p-1.12)
    trunk[:,0] += volume*(x-265)*.024*recovery
    trunk[:,1] += volume*(2.3*recovery+.40*np.sin(4*p-.7))
    face = rigid(ctx,"face",[254,197],vertices)
    tail = rigid(ctx,"tail",[185,73],vertices)
    mid = rigid(ctx,"hair_mid",[129,143],vertices)
    tip = rigid(ctx,"hair_tip",[110,211],vertices)
    tail = blend(blend(tail,mid,smooth((y-100)/90)),tip,smooth((y-175)/105))
    edge = np.interp(y,[20,65,110,154,196,246,305],[210,190,167,175,164,149,146])
    return blend(blend(trunk,face,1-smooth((y-188)/37)),tail,
                 (1-smooth((x-edge+6)/12))*(1-smooth((y-293)/20)))


def check_contacts(outlines,boot_rows):
    for side,offset in (("near",0),("far",12)):
        for j in range(3,9):
            left,right = [boot_rows[side][(i+offset)%FRAMES] for i in (j,j+1)]
            if not np.array_equal(left[:,3:],right[:,:-3]):
                raise ValueError(f"{side} sole pixels slid at {j}")
        for j in range(CONTACT):
            a,ra = foot(j,side,outlines[side])
            b,rb = foot(j+1,side,outlines[side])
            pts = outlines[side]
            angle = (ra+rb)/2
            idx = (flex(pts,angle,side) @ rotation(angle)[1]).argmax()
            pt = pts[idx:idx+1]
            dx = (b-a)[0]+(flex(pt,rb,side) @ rotation(rb).T-flex(pt,ra,side) @ rotation(ra).T)[0,0]
            if abs(dx+ADVANCE)/SCALE > .05:
                raise ValueError(f"{side} contact rolled with slip at {j}")


def preview(frames,records,filename="walk-right.gif"):
    images = []
    for i,frame in enumerate(frames):
        stage = Image.new("RGB",(388,405),(39,32,45))
        d = ImageDraw.Draw(stage)
        # Two depths with a common horizontal world speed. Close and far soles
        # meet their respective ground rows even when one passes the other.
        for y,color in [(374,(69,57,71)),(378,(108,89,106))]:
            d.line((14,y,374,y),fill=color)
            distance = round(records[i].get("root_px",i*ADVANCE/SCALE)*2)
            for x in range(17-distance%48,373,48):
                if x>=14:
                    d.line((x,y+1,x-3,y+3),fill=color)
        large = frame.resize((256,384),Image.Resampling.NEAREST)
        stage.paste(large,(58,12),large)
        images.append(stage)
    palette = Image.fromarray(np.concatenate([np.asarray(im) for im in images[::3]],axis=1)).quantize(256)
    frames_p = [im.quantize(palette=palette,dither=Image.Dither.NONE) for im in images]
    frames_p[0].save(HERE/filename,save_all=True,append_images=frames_p[1:],loop=0,
                     duration=[r["ms"] for r in records],optimize=False,disposal=1)


def entry_pose(i,count,rig,env0,source=None):
    t = i/count
    ready = smooth(t/.82)
    swing = np.clip((t-.27)/.73,0,1)
    turn = smooth((swing-.05)/.74)
    art = pieces(turn,source)
    outlines = {s:sole(art[s+"_leg"],LEGS[s][-1]) for s in LEGS}
    travel = 24*t*t+40*t**3
    far_angle = foot(12+i-count,"far",outlines["far"])[1] if i>=count-3 else 0.
    near_angle = np.radians(17*smooth(t/.27)*(1-smooth((swing-.08)/.65))-12*smooth((swing-.55)/.45))
    feet = {}
    for side,angle,flat_x,lift in [
        ("near",near_angle,157+197*smooth(swing)-travel,38*sin(pi*swing)**1.6),
        ("far",far_angle,251-travel,0)]:
        contour = outlines[side]
        point = np.array([flat_x,GROUND[side]-contour[:,1].max()-lift])
        feet[side] = (point+rocker(angle,side,contour),angle)
    env = dict(env0)
    env["p"] = -.8*(1-t)
    env["lift"] = (8+4*sin(pi*t))*(1-ready)+env0["lift"]*ready
    return transition_canvas(rig,env,art,feet,ready),travel,swing


def transition_canvas(rig,env,art,feet,ready):
    for side,(pt,_) in feet.items():
        env[side+"_target"] = [pt[0],-pt[1],0]
    ctx = Ctx(rig,env)
    canvas = Image.new("RGBA",(CELL[0]*SCALE,CELL[1]*SCALE))
    for name,layer in art.items():
        mesh = SkinMesh(layer,spacing=(12,10) if name.endswith("leg") or name=="body" else (31,14))
        posed = pose(mesh.vertices,name,ctx,feet,ready)
        if not name.endswith("leg"):
            posed = blend(mesh.vertices,posed,ready)
        canvas.alpha_composite(mesh.draw(posed))
    return canvas


def entry(rig,walk_frames,walk_records):
    # Start on both feet. Hold the far shoe in world space and turn the right
    # shoe only in flight. At the next heel strike the regular loop takes over.
    count = 14
    env0,ms,_ = frames_of(rig,"walk",0)[0]
    frames,records = [],[]
    for i in range(count+1):
        canvas,travel,swing = entry_pose(i,count,rig,env0)
        image = native(canvas)
        if i==count:
            # This endpoint is consumed by frame zero of walk; omit the duplicate.
            if not np.array_equal(np.asarray(image),np.asarray(walk_frames[0])):
                raise ValueError("First step does not join the walk loop")
            break
        frames.append(image)
        records.append(dict(x=i%7*CELL[0],y=i//7*CELL[1],w=CELL[0],h=CELL[1],ms=ms,
                            root_px=round(travel/SCALE,4),grounded=["far","near"] if swing==0 else ["far"]))
    atlas = Image.new("RGBA",(7*CELL[0],2*CELL[1]))
    for frame,rec in zip(frames,records):
        atlas.paste(frame,(rec["x"],rec["y"]))
    atlas.save(HERE/"walk-start-sheet.png")
    data = dict(animation="walk_start",image="walk-start-sheet.png",loop=False,pivot=PIVOT,cell=CELL,
                next_animation="walk_right",advance_px=16,frames=records)
    (HERE/"walk-start.json").write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")
    follow = [dict(r,root_px=16+i*ADVANCE/SCALE) for i,r in enumerate(walk_records*2)]
    preview(frames+walk_frames*2,records+follow,"walk-start.gif")


def render_cycle(source=None):
    rig = spec.load(str(HERE/"walk.yaml"))
    art = pieces(source=source)
    outlines = {s:sole(art[s+"_leg"],LEGS[s][-1]) for s in LEGS}
    meshes = {n:SkinMesh(image,spacing=(12,10) if n.endswith("leg") or n=="body" else (31,14))
              for n,image in art.items()}
    frames,records = [],[]
    boot_rows = {"near":[],"far":[]}
    for i,(env,ms,_) in enumerate(frames_of(rig,"walk",0)):
        feet = {s:foot(i+offset,s,outlines[s]) for s,offset in [("near",0),("far",12)]}
        for s,(point,_) in feet.items():
            env[s+"_target"] = [point[0],-point[1],0]
        ctx = Ctx(rig,env)
        canvas = Image.new("RGBA",(CELL[0]*SCALE,CELL[1]*SCALE))
        for name,mesh in meshes.items():
            layer = mesh.draw(pose(mesh.vertices,name,ctx,feet))
            canvas.alpha_composite(layer)
            if name.endswith("leg"):
                boot_rows[name.split("_")[0]].append(np.asarray(native(layer))[173:].copy())
        frame = native(canvas)
        box = frame.getchannel("A").getbbox()
        if not box or box[0]<1 or box[1]<1 or box[2]>=CELL[0] or box[3]>=CELL[1]:
            raise ValueError(f"Frame {i} is empty or clipped")
        frames.append(frame)
        records.append(dict(x=i%6*CELL[0],y=i//6*CELL[1],w=CELL[0],h=CELL[1],ms=ms,
                            grounded=[s for s,off in (("near",0),("far",12)) if (i+off)%FRAMES<=CONTACT]))
    check_contacts(outlines,boot_rows)
    return rig,frames,records


def main():
    rig,frames,records = render_cycle()
    atlas = Image.new("RGBA",(CELL[0]*6,CELL[1]*4))
    for frame,record in zip(frames,records):
        atlas.paste(frame,(record["x"],record["y"]))
    atlas.save(HERE/"walk-right-sheet.png")
    delta = ADVANCE*FRAMES/SCALE
    data = dict(animation="walk_right",view="three-quarter",image="walk-right-sheet.png",
                cell=CELL,pivot=PIVOT,loop=True,cycle_advance_px=delta,
                ground_speed_px_per_second=delta*1000/sum(r["ms"] for r in records),frames=records)
    (HERE/"walk-right.json").write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")
    preview(frames,records)
    entry(rig,frames,records)


if __name__ == "__main__":
    main()

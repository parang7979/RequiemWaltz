"""Texture the SpriteKiln walk rig with the supplied profile, then export one cycle."""
import json
import sys
from math import ceil, cos, pi, sin
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from spritekiln import spec
from spritekiln.anim import frames_of
from spritekiln.rig import Ctx

from skin import pieces

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3]/"tools"))
from cutout.mesh import SkinMesh as PaintedMesh, blend, rigid, screen, segment

CELL, SCALE = (128,192), 4
ORIGIN = np.array([-21.,-27.])
PIVOT = (67,183)
ANKLE = np.array([200.,648.])
HIP = np.array([249.,368.])
KNEE = np.array([226.,492.])
FRAMES, CONTACT, ADVANCE = 24, 14, 12


def smooth(t):
    t = np.clip(t,0,1)
    return t*t*(3-2*t)


def rotation(a):
    return np.array([[cos(a),-sin(a)],[sin(a),cos(a)]])


def bottom_contour(image):
    alpha = np.asarray(image)[:,:,3]
    xs = np.flatnonzero(alpha[636:].any(axis=0))
    ys = [len(alpha)-1-np.argmax(alpha[::-1,x]>0) for x in xs]
    return np.column_stack((xs+.5,np.array(ys)+1.0))-ANKLE


def roll(angle, sole):
    # Roll a rigid boot over its actual heel and toe outline without tangential slip.
    translation = np.zeros(2)
    steps = max(1,ceil(abs(angle)/0.003))
    previous = np.eye(2)
    for j in range(1,steps+1):
        mid = rotation(angle*(j-.5)/steps)
        current = rotation(angle*j/steps)
        contact = sole[np.argmax(sole @ mid[1])]
        translation += (previous-current) @ contact
        previous = current
    translation[1] = sole[:,1].max() - (sole @ previous[1]).max()
    return translation


def shoe(frame,sole):
    f = frame % FRAMES
    t = max(0,(f-CONTACT)/(FRAMES-CONTACT))
    if f <= CONTACT:
        degrees = -14*(1-smooth(f/3)) + 25*smooth((f-9)/5)
    else:
        degrees = 25 + 5*sin(pi*min(1,t/.4)) - 39*smooth((t-.12)/.75)
    angle = np.radians(degrees)
    travel = t**3*(10-15*t+6*t*t)
    pos = np.array([311-ADVANCE*f+ADVANCE*FRAMES*travel,
                    ANKLE[1]-50*sin(pi*t)**1.7])+roll(angle,sole)
    return pos,angle


def move(points,part,ctx,feet):
    x,y = points.T
    if part.endswith("leg"):
        side = part.split("_")[0]
        hip,knee,ankle = [screen(ctx,side+"_"+joint) for joint in ("hip","knee","ankle")]
        position,angle = feet[side]
        if np.linalg.norm(ankle-position) > .01:
            raise ValueError(f"Unreachable {side} contact target")
        upper = segment(points,HIP,KNEE,hip,knee)
        lower = segment(points,KNEE,ANKLE,knee,ankle)
        boot = (points-ANKLE) @ rotation(angle).T + position
        return blend(blend(upper,lower,smooth((y-465)/52)),
                     boot,smooth((y-608)/40))
    if part.endswith("arm"):
        side = part.split("_")[0]
        upper = rigid(ctx,side+"_arm",[235,226],points)
        lower = rigid(ctx,side+"_forearm",[228,304],points)
        return blend(upper,lower,smooth((y-289)/29))
    if part=="hem":
        return rigid(ctx,"hem",[222,328],points)
    if part=="pouch":
        return rigid(ctx,"hips",[247,368],points)
    chest = rigid(ctx,"chest",[247,368],points)
    face = rigid(ctx,"face",[247,197],points)
    tail = rigid(ctx,"tail",[182,82],points)
    tail_edge = np.interp(y,[20,60,100,145,195,250,303],[193,184,169,172,166,169,166])
    return blend(blend(chest,face,1-smooth((y-189)/30)),
                 tail, (1-smooth((x-tail_edge+6)/12))*(1-smooth((y-291)/20)))


class SkinMesh(PaintedMesh):
    """Use the original walk study's camera and grid for its existing callers."""
    def __init__(self, art, spacing=(31,14)):
        super().__init__(art, canvas_size=(CELL[0]*SCALE,CELL[1]*SCALE),
                         origin=ORIGIN, spacing=spacing)


def native(image):
    im = image.resize(CELL,Image.Resampling.BOX)
    im.putalpha(im.getchannel("A").point(lambda a: 255 if a>=128 else 0))
    return im


def main():
    rig = spec.load(str(HERE/"walk.yaml"))
    art = pieces()
    sole = bottom_contour(art["near_leg"])
    meshes = {name:SkinMesh(layer) for name,layer in art.items()}
    frames,records,footprints = [],[],{"near":[], "far":[]}
    for i,(env,ms,_) in enumerate(frames_of(rig,"walk",0)):
        feet = {"near":shoe(i,sole),"far":shoe(i+FRAMES//2,sole)}
        for side,(point,_) in feet.items():
            env[side+"_target"] = [point[0],-point[1],0]
        state = Ctx(rig,env)
        result = Image.new("RGBA",(CELL[0]*SCALE,CELL[1]*SCALE))
        for name,mesh in meshes.items():
            layer = mesh.draw(move(mesh.vertices,name,state,feet))
            result.alpha_composite(layer)
            if name.endswith("leg"):
                footprints[name.split("_")[0]].append(np.asarray(native(layer))[174:,:,:].copy())
        frames.append(native(result))
        records.append({"x":i%6*CELL[0],"y":i//6*CELL[1],"w":CELL[0],"h":CELL[1],
                        "ms":ms,"grounded":[side for side,f in (("near",i),("far",(i+12)%24)) if f<=CONTACT]})
    # Compare the rendered sole pixels after forward world motion during flat support.
    for side,offset in [("near",0),("far",12)]:
        for i in range(3,9):
            a,b = [footprints[side][(j+offset)%FRAMES] for j in (i,i+1)]
            assert np.array_equal(a[:,3:],b[:,:-3]), f"{side} boot slid at frame {i}"
    speed = ADVANCE/SCALE/(records[0]["ms"]/1000)
    atlas = Image.new("RGBA",(6*CELL[0],4*CELL[1]))
    for im,rec in zip(frames,records):
        atlas.paste(im,(rec["x"],rec["y"]))
        box = im.getchannel("A").getbbox()
        assert box and box[0]>0 and box[1]>0 and box[2]<CELL[0] and box[3]<CELL[1]
    atlas.save(HERE/"walk-right-sheet.png")
    data = dict(animation="walk_right",image="walk-right-sheet.png",loop=True,cell=CELL,pivot=PIVOT,
                ground_speed_px_per_second=speed,cycle_advance_px=ADVANCE*FRAMES/SCALE,frames=records)
    (HERE/"walk-right.json").write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")
    preview(frames,records)


def preview(frames,records):
    # Tracking-camera view. The 24 px cadence of the floor repeats after a 72 px stride.
    film = []
    for i,frame in enumerate(frames):
        bg = Image.new("RGB",(384,408),(39,32,45))
        pen = ImageDraw.Draw(bg)
        ground = 16+PIVOT[1]*2
        pen.line((12,ground,372,ground),fill=(108,90,108))
        for x in range(12-(i*6)%48,373,48):
            if x>=12:
                pen.line((x,ground+1,x-4,ground+5),fill=(133,111,125),width=2)
        actor = frame.resize((256,384),Image.Resampling.NEAREST)
        bg.paste(actor,(58,16),actor)
        film.append(bg)
    palette = Image.fromarray(np.concatenate([np.asarray(im) for im in film[::3]],axis=1)).quantize(256)
    indexed = [im.quantize(palette=palette,dither=Image.Dither.NONE) for im in film]
    indexed[0].save(HERE/"walk-right.gif",save_all=True,append_images=indexed[1:],
                    duration=[r["ms"] for r in records],loop=0,disposal=1,optimize=False)


if __name__=="__main__":
    main()

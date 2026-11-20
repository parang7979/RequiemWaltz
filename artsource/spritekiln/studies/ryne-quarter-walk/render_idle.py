"""Idle painted on the same three-quarter rest pose used to begin walking."""
import sys
from importlib import import_module

import numpy as np
from PIL import Image, ImageDraw
from spritekiln import spec
from spritekiln.anim import frames_of
from spritekiln.render import Camera
from spritekiln.rig import Ctx, rest_env

from render_walk import HERE, entry_pose, native
from build import ORIGIN

sys.path.insert(0,str(HERE.parent))
idle = import_module("ryne-turnaround-idle.build")


def paint_eyes(base,amount,closed):
    if not amount:
        return base
    result = base.copy()
    for src,poly in [
        ((5,0,39,29),[(214,149),(219,144),(230,140),(239,141),(246,145),
                       (249,151),(245,163),(241,169),(226,171),(219,166)]),
        ((56,0,80,29),[(269,151),(273,146),(282,142),(288,142),(290,146),
                        (289,154),(284,167),(280,170),(271,169)])]:
        points = np.array(poly)-ORIGIN.astype(int)
        left,top = points.min(axis=0)
        right,bottom = points.max(axis=0)+1
        box = (left,top,right,bottom)
        size = (right-left,bottom-top)
        patch = closed.crop(src).resize(size,Image.Resampling.BICUBIC)
        if amount<.95:
            eye = base.crop(box).convert("RGB")
            reduced = max(1,round(eye.height*(1-amount)))
            patch.paste(eye.resize((eye.width,reduced),Image.Resampling.BOX),
                        (0,round((eye.height-reduced)*.72)))
        gate = Image.new("L",size)
        ImageDraw.Draw(gate).polygon([tuple(v) for v in points-[left,top]],fill=255)
        result.paste(patch,(left,top),gate)
    return result


def fields(x,y):
    smooth = idle.smooth
    edge = np.interp(y,[20,65,110,154,196,246,305],[210,190,167,175,164,149,146])
    hair = (1-smooth(edge-6,edge+6,x))*(1-smooth(293,313,y))
    mid,tip = smooth(100,190,y),smooth(175,280,y)
    head = 1-smooth(187,217,y)
    neck_down = (1-hair)*(1-head)
    near = (1-smooth(202,230,x))*smooth(205,234,y)*(1-smooth(416,435,y))
    far = smooth(289,316,x)*smooth(205,237,y)*(1-smooth(416,435,y))
    trunk = neck_down*(1-near-far)
    chest = 1-smooth(270,377,y)
    return dict(pony=hair*(1-mid)*(1-tip),mid=hair*mid*(1-tip),tip=hair*tip,
                face=(1-hair)*head,sleeve_near=neck_down*near,sleeve_far=neck_down*far,
                chest=trunk*chest,hips=trunk*(1-chest)*(1-smooth(380,525,y)))


def render(source=None):
    walk = spec.load(str(HERE/"walk.yaml"))
    start_env,_,_ = frames_of(walk,"walk",0)[0]
    base,_,_ = entry_pose(0,14,walk,start_env,source)
    rig = spec.load(str(HERE/"idle.yaml"))
    cam = Camera.from_spec(rig)
    rest = Ctx(rig,rest_env(rig,0))
    cx,cy = cam.project(np.zeros(3))
    registration = np.array([[1/cam.scale,0,cx],[0,1/cam.scale,cy],[0,0,1]])
    inv_registration = np.linalg.inv(registration)
    yy,xx = np.indices((base.height,base.width),dtype=np.float32)
    x,y = xx+ORIGIN[0], yy+ORIGIN[1]
    weights = fields(x,y)
    planes = {name:idle.plane(rest,cam,name) for name in weights}
    chest = np.exp(-((x-267)/38)**4)*idle.smooth(220,242,y)*(1-idle.smooth(264,295,y))
    closed = Image.open(HERE.parent/"ryne-turnaround-idle"/"eyelids-source.png").convert("RGB")
    expressions = {}
    frames,durations = [],[]
    for env,ms,_ in frames_of(rig,"idle",0):
        ctx = Ctx(rig,env)
        u,v = xx.copy(),yy.copy()
        for bone,weight in weights.items():
            m = inv_registration @ planes[bone] @ np.linalg.inv(idle.plane(ctx,cam,bone)) @ registration
            u += weight*((m[0,0]-1)*x+m[0,1]*y+m[0,2])
            v += weight*(m[1,0]*x+(m[1,1]-1)*y+m[1,2])
        u -= chest*(.039*(x-265)+.75)*env["breath"]
        v += chest*3.6*env["breath"]
        blink = round(float(env["blink"]),3)
        if blink not in expressions:
            expressions[blink] = np.asarray(paint_eyes(base,blink,closed))
        ix = np.clip(np.rint(u).astype(int),0,base.width-1)
        iy = np.clip(np.rint(v).astype(int),0,base.height-1)
        frames.append(native(Image.fromarray(expressions[blink][iy,ix])))
        durations.append(ms)
    neutral = np.asarray(native(base))
    assert np.array_equal(np.asarray(frames[0]),neutral)
    assert all(np.array_equal(np.asarray(f)[146:],neutral[146:]) for f in frames)
    return frames,durations


if __name__=="__main__":
    idle.write_clip(*render(),HERE)

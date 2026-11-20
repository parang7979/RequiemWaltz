"""Bake the skeleton Idle from one piece of art and the shared cutout tools."""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from spritekiln import spec
from spritekiln.anim import frames_of
from spritekiln.rig import Ctx, rest_env

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parents[3]/"tools"
sys.path.insert(0, str(TOOLS))
from cutout.mesh import SkinMesh, blend, rigid, screen
from cutout.texture import register_texture


def ramp(a, b, x):
    t = np.clip((x-a)/(b-a), 0, 1)
    return t*t*(3-2*t)


def texture():
    source = HERE/"source.png"
    cell = HERE/"pose-56.png"
    subprocess.run(["python", str(TOOLS/"pixelate_pose.py"), str(source), str(cell),
                    "--size", "64", "--height", "56"], check=True)
    with Image.open(source) as art, Image.open(cell) as sprite:
        registered = register_texture(art, sprite, 56)
    box = registered.getchannel("A").getbbox()
    patch = registered.crop(box)
    width = round(56*patch.width/patch.height)
    patch = patch.resize((width*4,224), Image.Resampling.BOX)
    canvas = Image.new("RGBA",(256,256))
    canvas.paste(patch,(((64-width)//2)*4,16))
    canvas.putalpha(canvas.getchannel("A").point(lambda a: a if a>=8 else 0))
    return canvas


def bind(vertices, ctx, origins):
    x,y = vertices.T
    def bone(name):
        return rigid(ctx,name,origins[name],vertices)

    # Let the pelvis and planted legs support the spine. The pockets of
    # transparent space either side of the ribs separate the hanging arms.
    trunk = blend(vertices,bone("ribs"),1-ramp(109,132,y))
    near_edge = np.interp(y,[75,91,108,116,135,158],[105,111,104,100,98,100])
    far_edge = np.interp(y,[75,90,107,118,138,162],[143,143,143,145,153,157])
    near = (1-ramp(near_edge-2,near_edge+2,x))*ramp(66,82,y)*(1-ramp(158,169,y))
    far = ramp(far_edge-2,far_edge+2,x)*ramp(78,91,y)*(1-ramp(161,170,y))
    trunk = blend(blend(trunk,bone("near_arm"),near),bone("far_arm"),far)

    # A lower mandible can part slightly without flexing the tooth row above it.
    jawline = np.interp(x,[117,124,131,143],[60,62,65,65])
    head = blend(bone("skull"),bone("jaw"),ramp(jawline-1,jawline+2,y)*ramp(116,122,x))
    head_mask = (1-ramp(68,76,y))*ramp(106,117,x)+(1-ramp(61,69,y))*(1-ramp(106,117,x))
    trunk = blend(trunk,head,head_mask)
    sash_edge = np.interp(y,[132,147,167,189],[145,142,143,152])
    sash = ramp(133,147,y)*ramp(sash_edge-2,sash_edge+2,x)*(1-far)*(1-ramp(188,192,y))
    return blend(trunk,bone("sash"),sash)


def render():
    rig = spec.load(str(HERE/"idle.yaml"))
    rest = Ctx(rig,rest_env(rig))
    origins = {name:screen(rest,name) for name in rig["bones"]}
    mesh = SkinMesh(texture(),canvas_size=(256,256),spacing=(4,4))
    frames, times = [], []
    for env,ms,_ in frames_of(rig,"idle",0):
        posed = bind(mesh.vertices,Ctx(rig,env),origins)
        frame = mesh.draw(posed).resize((64,64),Image.Resampling.BOX)
        alpha = frame.getchannel("A")
        ink = frame.convert("RGB").filter(ImageFilter.UnsharpMask(.8,110,2))
        frame.paste(ink,mask=alpha.point(lambda a: 255 if a>225 else 0))
        frame.putalpha(alpha.point(lambda a: a if a>=16 else 0))
        frames.append(frame)
        times.append(ms)
    return frames,times


def main():
    frames,times = render()
    sheet = Image.new("RGBA",(384,384))
    pages,records = [],[]
    for i,(f,ms) in enumerate(zip(frames,times,strict=True)):
        x,y = (i%6)*64,(i//6)*64
        sheet.paste(f,(x,y))
        records.append(dict(x=x,y=y,w=64,h=64,ms=ms))
        assert f.crop((0,51,64,64)).tobytes()==frames[0].crop((0,51,64,64)).tobytes()
        l,t,r,b = f.getchannel("A").getbbox()
        assert min(l,t,64-r,64-b)>0
        stage = Image.new("RGB",(74,70),"#27202d")
        ImageDraw.Draw(stage).line((4,63,69,63),fill="#50434e")
        stage.paste(f,(5,3),f)
        pages.append(stage.resize((222,210),Image.Resampling.NEAREST))
    sheet.save(HERE/"idle-sheet.png")
    (HERE/"idle.json").write_text(json.dumps(dict(animation="idle",image="idle-sheet.png",
        cell=[64,64],pivot=[32,60],loop=True,frames=records),indent=2)+"\n",encoding="utf-8")
    palette = Image.fromarray(np.concatenate([np.asarray(p) for p in pages],axis=1)).quantize(256)
    indexed = [p.quantize(palette=palette,dither=Image.Dither.NONE) for p in pages]
    indexed[0].save(HERE/"idle.gif",save_all=True,append_images=indexed[1:],duration=times,
                    loop=0,optimize=False,disposal=1)


if __name__=="__main__":
    main()

"""Build the four quarter-view clips. Use --height 56 for the 64px reference grid."""
import argparse
from dataclasses import dataclass
import json
import subprocess
import sys
from math import ceil

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import render_idle
import render_run
import render_slash
import render_walk
from render_walk import HERE

sys.path.insert(0, str(HERE.parents[3]/"tools"))
from cutout.texture import register_texture

@dataclass(frozen=True)
class PixelGrid:
    height: int
    cell: int
    scale: float
    directory: str
    zoom: int

    @property
    def out(self):
        return HERE/self.directory


GRIDS = {128: PixelGrid(128,144,.75,"pixelated",2),
         56: PixelGrid(56,64,56/172,"pixelated-56",3)}


def pixel_source(grid):
    original = HERE/"quarter.png"
    tool = HERE.parents[3]/"tools"/"pixelate_pose.py"
    # The project's Python has SciPy for pixelate_pose. This renderer runs
    # in the shared SpriteKiln environment.
    output = grid.out/"quarter-pose.png"
    subprocess.run(["python", str(tool), str(original), str(output), "--size",
                    str(grid.cell), "--height", str(grid.height)], check=True)
    return register_pose(grid, output)


def register_pose(grid, output):
    with Image.open(HERE/"quarter.png") as reference, Image.open(output) as cell:
        return register_texture(reference, cell, grid.height)


def export(grid, name, frames, durations, pivot, columns, advance=0):
    scale = grid.scale
    w,h = (round(v*scale) for v in frames[0].size)
    extent = None
    if grid.height==56:
        # Register the 172px standing body to the reference's (19,4)-(45,60)
        # silhouette. Keep the camera fixed as the character moves, with more
        # horizontal room in the slash cell for its full sweep.
        w,h = (96 if name=="slash" else 64),64
        center_shift = (w-64)/2
        left = 16+pivot[0]-render_walk.PIVOT[0]-(19+center_shift)/scale
        top = 11-4/scale
        extent = (left,top,left+w/scale,top+h/scale)
        pivot = [(pivot[0]-left)*scale,(pivot[1]-top)*scale]
    else:
        pivot = [v*scale for v in pivot]
    sheet = Image.new("RGBA",(columns*w,ceil(len(frames)/columns)*h))
    pages, records = [], []
    for i,(frame,ms) in enumerate(zip(frames,durations,strict=True)):
        if extent:
            samples = frame.transform((2*w,2*h),Image.Transform.EXTENT,extent,
                                      Image.Resampling.BILINEAR)
            tile = samples.resize((w,h),Image.Resampling.BOX)
        else:
            tile = frame.resize((w,h),Image.Resampling.LANCZOS)
        # Restore local contrast after rig sampling and the final grid resize.
        # Only sharpen solid paint so the hair edges and blade trail stay clean.
        alpha = tile.getchannel("A")
        solid = alpha.point(lambda a: 255 if a>235 else 0)
        ink = tile.convert("RGB").filter(ImageFilter.UnsharpMask(.85,115,2))
        tile.paste(ink,mask=solid)
        tile.putalpha(alpha.point(lambda a: 0 if a<24 else a))
        x,y = i%columns*w,i//columns*h
        sheet.paste(tile,(x,y))
        records.append(dict(x=x,y=y,w=w,h=h,ms=ms))
        page = Image.new("RGB",(w+16,h+6),"#27202d")
        ground = round(pivot[1])+3
        pen = ImageDraw.Draw(page)
        pen.line((5,ground,page.width-5,ground),fill="#493d4b")
        if advance:
            # Choose a repeat distance that divides the full stride so the
            # ground scrolls seamlessly when the preview loops.
            repeat = advance/(3 if name=="walk" else 6)
            offset = i*advance/len(frames)
            for mark in np.rint(np.arange(8-offset%repeat,page.width-6,repeat)).astype(int):
                if mark>=6:
                    pen.line((mark,ground+1,mark-1,ground+2),fill="#695c69")
        page.paste(tile,(8,3),tile)
        pages.append(page.resize((page.width*grid.zoom,page.height*grid.zoom),Image.Resampling.NEAREST))
    sheet.save(grid.out/f"{name}-sheet.png")
    meta = dict(animation=name,image=f"{name}-sheet.png",cell=[w,h],pivot=pivot,
                loop=name!="slash",frames=records)
    if advance:
        meta["cycle_advance_px"] = advance
    (grid.out/f"{name}.json").write_text(json.dumps(meta,indent=2)+"\n",encoding="utf-8")
    palette = Image.fromarray(np.concatenate([np.asarray(p) for p in pages],axis=1)).quantize(256)
    indexed = [p.quantize(palette=palette,dither=Image.Dither.NONE) for p in pages]
    ticks = np.rint(np.cumsum([0]+durations)/10).astype(int)*10
    preview_ms = np.diff(ticks).tolist()
    if name=="slash":
        preview_ms[-1] += 420
    indexed[0].save(grid.out/f"{name}.gif",save_all=True,append_images=indexed[1:],
                    duration=preview_ms,loop=0,optimize=False,disposal=1)
    print(f"{name}: {len(frames)} frames, {w} x {h}",flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--height",type=int,choices=GRIDS,default=128)
    grid = GRIDS[parser.parse_args().height]
    grid.out.mkdir(exist_ok=True)
    source = pixel_source(grid)
    idle,times = render_idle.render(source)
    export(grid,"idle",idle,times,render_walk.PIVOT,8)
    _,walk,records = render_walk.render_cycle(source)
    export(grid,"walk",walk,[r["ms"] for r in records],render_walk.PIVOT,6,72*grid.scale)
    gait,records = render_run.render_gait(walk,source)
    export(grid,"run",gait[36:60],[r["ms"] for r in records[36:60]],render_walk.PIVOT,
           6,render_run.RUN_STRIDE*grid.scale)
    slash,records = render_slash.render_frames(source)
    export(grid,"slash",slash,[r["ms"] for r in records],[115,183],7)


if __name__=="__main__":
    main()

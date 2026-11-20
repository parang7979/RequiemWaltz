"""Render the 56px slash with the character's right boot planted as in Idle."""
from dataclasses import replace
import json

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from render_pixelated import GRIDS, export, register_pose
from render_slash import render_frames


def compare(original, variant):
    palettes = []
    pages = []
    font = ImageFont.truetype("malgun.ttf",16)
    with Image.open(original/"slash.gif") as before, Image.open(variant/"slash.gif") as after:
        assert before.n_frames == after.n_frames and before.size == after.size
        width,height = before.size
        durations = []
        for i in range(before.n_frames):
            before.seek(i)
            after.seek(i)
            assert before.info["duration"] == after.info["duration"]
            durations.append(after.info["duration"])
            page = Image.new("RGB",(2*width,height+32),"#27202d")
            page.paste(before.convert("RGB"),(0,32))
            page.paste(after.convert("RGB"),(width,32))
            pen = ImageDraw.Draw(page)
            for j,title in enumerate(("기존 횡베기","오른발 Idle 고정")):
                pen.text(((j+.5)*width,18),title,fill="#eee6ed",font=font,anchor="mm")
            pen.line((width,8,width,height+24),fill="#514352")
            pages.append(page)
            if i%4==0:
                palettes.append(np.asarray(page))
    palette = Image.fromarray(np.concatenate(palettes,axis=0)).quantize(256)
    indexed = [p.quantize(palette=palette,dither=Image.Dither.NONE) for p in pages]
    indexed[0].save(variant/"comparison.gif",save_all=True,append_images=indexed[1:],
                    duration=durations,loop=0,optimize=False,disposal=1)


def main():
    grid = GRIDS[56]
    variant = replace(grid,directory=grid.directory+"/slash-idle-right-foot")
    variant.out.mkdir(exist_ok=True)
    source = register_pose(grid,grid.out/"quarter-pose.png")
    frames,records = render_frames(source,idle_right_foot=True)
    original = json.loads((grid.out/"slash.json").read_text())
    times = [r["ms"] for r in records]
    assert times == [r["ms"] for r in original["frames"]]
    export(variant,"slash",frames,times,[115,183],7)
    compare(grid.out,variant.out)


if __name__=="__main__":
    main()

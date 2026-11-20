"""Draw the weight transfer into idle and show the whole motion on a fixed floor."""
import json
from math import pi, sin

import numpy as np
from PIL import Image, ImageDraw
from spritekiln import spec
from spritekiln.anim import frames_of

from render_walk import (ADVANCE,CELL,FRAMES,GROUND,HERE,LEGS,PIVOT,SCALE,flex,foot,
                         native,pieces,rocker,rotation,smooth,sole,transition_canvas)


def read_clip(name):
    info = json.loads((HERE/(name+".json")).read_text("utf-8"))
    with Image.open(HERE/info["image"]) as sheet:
        frames = [sheet.crop((f["x"],f["y"],f["x"]+f["w"],f["y"]+f["h"]))
                  for f in info["frames"]]
    return frames,info


def stop_clip(walk,idle):
    rig = spec.load(str(HERE/"walk.yaml"))
    cycle = frames_of(rig,"walk",0)
    start,ms,_ = cycle[12]  # The far heel arrives and takes the final load.
    end = dict(cycle[0][0],p=-.8,lift=8)
    length = 18
    frames,records = [],[]
    previous = {}
    for i in range(length+1):
        t = i/length
        settle = smooth(t)
        ready = 1-settle
        swing = np.clip((i-2)/10,0,1)
        art = pieces(1-smooth((swing-.06)/.82))
        # Integrate the deceleration; the first derivative at entry equals
        # the 12 artwork pixels per frame of the steady walk.
        travel = 80*(1-(1-min(i/14,1))**2.1)
        feet = {}
        for side in LEGS:
            contour = sole(art[side+"_leg"],LEGS[side][-1])
            if side=="far":
                angle = foot(min(i,3),side,contour)[1]
                world_x,lift = 331,0
            else:
                toe = foot(12+min(i,2),side,contour)[1]
                heel = -5*smooth((swing-.44)/.44)*(1-smooth((i-12)/3))
                angle = toe*(1-smooth((swing-.06)/.74))+np.radians(heel)
                world_x,lift = 146+91*smooth(swing), 27*sin(pi*swing)**1.65
            base = np.array([world_x-travel,GROUND[side]-contour[:,1].max()-lift])
            pt = base+rocker(angle,side,contour)
            feet[side] = pt,angle
            grounded = side=="far" or i<=2 or i>=12
            if grounded and side in previous:
                old_pt,old_angle,old_travel = previous[side]
                mid = (angle+old_angle)/2
                k = np.argmax((flex(contour,mid,side) @ rotation(mid).T)[:,1])
                material = contour[k:k+1]
                before = flex(material,old_angle,side) @ rotation(old_angle).T
                after = flex(material,angle,side) @ rotation(angle).T
                slip = (pt-old_pt)[0]+travel-old_travel+(after-before)[0,0]
                assert abs(slip)/SCALE<.05, (side,i,slip/SCALE)
            if grounded:
                previous[side] = (pt,angle,travel)
            else:
                previous.pop(side,None)

        env = dict(start)
        phase = pi+2.35*(1-(1-t)**2)
        for channel,value in (("swing",np.cos(phase-.14)),("counter",np.cos(phase-.23)),
                              ("lift",3.5*sin(2*phase-.8)+2.1*(1-np.cos(2*phase)))):
            env[channel] = ready*value+settle*end[channel]
        env["p"] = phase*ready+(2*pi+end["p"])*settle
        if i==length:
            env.update(end)
        frame = native(transition_canvas(rig,env,art,feet,ready))
        if i==0:
            assert np.array_equal(frame,walk[12]), "Stop entry differs from walk contact"
        if i==length:
            assert np.array_equal(frame,idle[0]), "Stop exit differs from idle"
            break
        frames.append(frame)
        records.append(dict(x=i%6*CELL[0],y=i//6*CELL[1],w=CELL[0],h=CELL[1],ms=ms,
                            root_px=round(travel/SCALE,5),
                            grounded=["far","near"] if i<=2 or i>=12 else ["far"]))
    atlas = Image.new("RGBA",(6*CELL[0],3*CELL[1]))
    for frame,rec in zip(frames,records):
        atlas.paste(frame,(rec["x"],rec["y"]))
    atlas.save(HERE/"walk-stop-sheet.png")
    info = dict(animation="walk_stop",image="walk-stop-sheet.png",loop=False,pivot=PIVOT,
                cell=CELL,from_walk_frame=12,next_animation="idle",advance_px=20,frames=records)
    (HERE/"walk-stop.json").write_text(json.dumps(info,indent=2)+"\n",encoding="utf-8")
    return frames,info


def main():
    idle,idata = read_clip("idle")
    entry,edata = read_clip("walk-start")
    walk,wdata = read_clip("walk-right")
    stop,sdata = stop_clip(walk,idle)
    assert np.array_equal(idle[0],entry[0])
    timeline = [(idle[i],r["ms"],0) for i,r in enumerate(idata["frames"]) if i>=18]
    timeline.extend((im,r["ms"],r["root_px"]) for im,r in zip(entry,edata["frames"]))
    start = edata["advance_px"]
    count = 2*FRAMES+sdata["from_walk_frame"]
    for i in range(count):
        f = i%FRAMES
        timeline.append((walk[f],wdata["frames"][f]["ms"],start+i*ADVANCE/SCALE))
    start += count*ADVANCE/SCALE
    timeline.extend((im,r["ms"],start+r["root_px"]) for im,r in zip(stop,sdata["frames"]))
    end = start+sdata["advance_px"]
    timeline.extend((im,r["ms"],end) for im,r in zip(idle,idata["frames"]))

    stage = Image.new("RGB",(720,398),(39,32,45))
    pen = ImageDraw.Draw(stage)
    for y,col in ((372,(69,57,71)),(376,(108,89,106))):
        pen.line((16,y,704,y),fill=col)
        for x in range(25,700,48):
            pen.line((x,y+1,x-3,y+3),fill=col)
    # A shared palette keeps the stationary backdrop and the art consistent.
    samples = Image.new("RGB",(8*CELL[0],4*CELL[1]),stage.getpixel((0,0)))
    for n,(frame,_,_) in enumerate(timeline[::6]):
        samples.paste(frame,(n%8*CELL[0],n//8*CELL[1]),frame)
    samples.paste(stage.crop((0,370,80,380)),(0,0))
    palette = samples.quantize(256,dither=Image.Dither.NONE)
    frames,times = [],[]
    for frame,ms,distance in timeline:
        art = frame.resize((2*CELL[0],2*CELL[1]),Image.Resampling.NEAREST)
        image = stage.copy()
        image.paste(art,(14+round(distance*2),10),art)
        frames.append(image.quantize(palette=palette,dither=Image.Dither.NONE))
        times.append(ms)
    # Play once so the character stays at her destination after the last breath.
    frames[0].save(HERE/"idle-walk-stop.gif",save_all=True,append_images=frames[1:],
                   duration=times,disposal=1,optimize=False)


if __name__=="__main__":
    main()

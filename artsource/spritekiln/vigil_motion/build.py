"""Build Vigil's B locomotion atlases from the approved idle and painted pose sheets."""
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageColor, ImageFilter

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent / "studies" / "vigil_ab"
DEST = HERE.parents[2] / "assets" / "actors" / "vigil" / "locomotion"
CAL = json.loads((STUDY / "calibration.json").read_text(encoding="utf8"))
SWATCHES = np.array([ImageColor.getrgb(p[0]) for p in CAL["palette"]], dtype=float)
INKS = np.array([ImageColor.getrgb(p[1]) for p in CAL["palette"]], dtype=np.uint8)
CLIPS = {"idle": (6, 160), "walk": (8, 105), "run": (8, 75)}
PIX = 64
GRID = (512, 384)


def read_grid(img, col, row, cols, rows):
    w, h = img.size
    return img.crop((round(col*w/cols), round(row*h/rows),
                     round((col+1)*w/cols), round((row+1)*h/rows)))


def landmarks(img):
    alpha = np.asarray(img.getchannel("A")) >= 132
    yy, xx = np.where(alpha)
    top, bottom = yy.min(), yy.max() + 1
    # The upper dome is clear of the weapon and trailing hair on every guide.
    crown = np.median(xx[(yy >= top) & (yy < top + (bottom-top)*0.07)]) + 0.5
    return float(crown), int(top), int(bottom)


def connected(mask):
    """Keep the character and its attached equipment after alpha reduction."""
    todo = set(zip(*np.where(mask)))
    largest = set()
    while todo:
        part = {todo.pop()}
        stack = list(part)
        while stack:
            y, x = stack.pop()
            for dy, dx in ((-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)):
                q = y+dy, x+dx
                if q in todo:
                    todo.remove(q)
                    part.add(q)
                    stack.append(q)
        if len(part) > len(largest):
            largest = part
    result = np.zeros_like(mask)
    for y, x in largest:
        result[y, x] = True
    return result


def sample_paint(source, guide, sign):
    sx, sy, sb = landmarks(source)
    gx, gy, gb = landmarks(guide)
    # y=57 is the ground line expressed as an edge, below the last sole pixel.
    gb = min(gb, 57)
    ratio = (sb-sy)/(gb-gy)
    left, top = sx-gx*ratio, sy-gy*ratio
    rect = (left, top, left+PIX*ratio, top+PIX*ratio)
    sampled = source.convert("RGBa").transform((512,512), Image.Transform.EXTENT, rect,
                                                Image.Resampling.BILINEAR)
    pixels = np.array(sampled.resize((PIX,PIX), Image.Resampling.BOX).convert("RGBA"))
    coverage = pixels[:,:,3].copy()
    mask = coverage >= 105
    rgb = pixels[:,:,:3].astype(float)
    ids = np.argmin(np.sum((rgb[:,:,None,:]-SWATCHES)**2, axis=3), axis=2)
    # At the tapered end, select the most covered steel sample of each column.
    for x in range(PIX):
        if sign*(x-gx) < 7:
            continue
        rows = np.flatnonzero(coverage[gy:gy+int((gb-gy)*0.55),x] >= 15) + gy
        if 0 < len(rows) <= 4 and rows.max()-rows.min() <= 3:
            y = rows[np.argmax(coverage[rows,x])]
            mask[y,x] = True
            ids[y,x] = 6 if coverage[y,x] < 150 else 7
    fg = connected(mask)
    out = np.zeros((64,64,4),np.uint8)
    out[fg,:3] = INKS[ids[fg]]
    out[fg,3] = 255
    return out


def idle_frame(base, index, sign):
    # Warp the selected B pixels around the feet; the hair tips and wrist lag the rib cage.
    phase = index*math.tau/6
    y,x = np.mgrid[0:64,0:64]
    torso = np.clip((52-y)/20,0,1)
    forward = (x-32)*sign
    hair = np.clip((-forward-1)/9,0,1)*np.clip((43-y)/11,0,1)
    dx = sign*1.65*np.cos(phase+0.20)*hair
    dy = -0.90*np.sin(phase)*torso
    px = np.clip(np.rint(x-dx).astype(int),0,63)
    py = np.clip(np.rint(y-dy).astype(int),0,63)
    return base[py,px].copy()


def rounded_height(mask, radius):
    surface = Image.fromarray(mask.astype(np.uint8)*255)
    result = np.zeros(mask.shape, float)
    for step in range(radius):
        result += np.asarray(surface)/255 / (1+step*0.35)
        surface = surface.filter(ImageFilter.MinFilter(3))
    return result


def light_maps(color, sign):
    mask = color[:,:,3] > 0
    y,x = np.where(mask)
    top, height = y.min(), y.max()-y.min()+1
    # Register the garnet to the upper front edge of the bodice, independently per drawing.
    cy = int(round(top+height*0.273))
    crown = np.median(x[y < top + height*0.08])
    row = np.flatnonzero(mask[cy])
    # The raised blade can cross this scan line. Use the torso interval at the
    # base of the neck, keeping the clasp within the collar even during a stride.
    spans = np.split(row, np.flatnonzero(np.diff(row)>1)+1)
    neck = min(spans,key=lambda span: np.min(abs(span-(crown-sign))))
    target = np.clip(crown+sign,neck[0],neck[-1])
    cx = int(neck[np.argmin(abs(neck-target))])
    color[cy,cx,:3] = [157,90,109]
    emissive = np.zeros_like(color)
    emissive[cy,cx] = [111,40,57,255]

    rgb = color[:,:,:3].astype(float)
    ids = np.argmin(np.sum((rgb[:,:,None,:]-INKS.astype(float))**2,axis=3),axis=2)
    hair = mask & (ids>=5) & (ids<=8)
    skin = mask & (ids>=9)
    cloth = mask & ~hair & ~skin
    relief = rounded_height(mask,5)*0.56
    for region, strength in ((hair,0.72),(skin,0.75),(cloth,0.56)):
        relief += rounded_height(region,4)*strength
    # Shallow fabric folds follow the final painted clusters, including their movement.
    relief += np.where(cloth,ids*0.14,0)
    height_map = Image.fromarray(np.uint8(np.clip(relief*28,0,255))).filter(ImageFilter.GaussianBlur(0.70))
    dh_y,dh_x = np.gradient(np.asarray(height_map,dtype=float)/28)
    norm = np.stack((-dh_x,dh_y,np.ones_like(dh_x)*1.3),axis=2)
    norm /= np.linalg.norm(norm,axis=2,keepdims=True)
    normal = np.zeros_like(color)
    normal[:,:,:3] = np.rint((norm+1)*127.5).astype(np.uint8)
    normal[:,:,3] = color[:,:,3]
    # Visible blade end in the forward half, expressed in pixels from the foot pivot.
    ys,xs = np.where(mask & (np.indices(mask.shape)[0] < top+height*0.62))
    n = np.argmax(sign*xs)
    return normal,emissive,{"clasp":[cx-32,cy-57],"tip":[int(xs[n])-32,int(ys[n])-57]}


def preview(frames):
    for clip in CLIPS:
        count, ms = CLIPS[clip]
        images = []
        for i in range(count):
            display = Image.new("RGB",(512,256),"#44434e")
            for side in range(2):
                art = frames[(clip,side,i)].resize((256,256),Image.Resampling.NEAREST)
                display.paste(art,(side*256,0),art)
            images.append(display)
        images[0].save(HERE/f"{clip}.gif",save_all=True,append_images=images[1:],
                       duration=[round((i+1)*ms/10)*10-round(i*ms/10)*10 for i in range(count)],
                       loop=0,disposal=2,optimize=False)


def main():
    DEST.mkdir(parents=True,exist_ok=True)
    atlases = [Image.new("RGBA",GRID) for _ in range(3)]
    frames = {}
    meta = {"frame_size":64,"pivot":[32,57],"columns":8,"rows":6,"clips":{}}
    for number,(clip,(count,ms)) in enumerate(CLIPS.items()):
        data = {"count":count,"ms":ms,"row_e":2*number,"row_w":2*number+1,"sockets":{}}
        if clip != "idle":
            data["ground_speed"] = {"walk":42.6, "run":84.2}[clip]
        meta["clips"][clip] = data
        for side,direction in enumerate(("e","w")):
            sign = (1,-1)[side]
            if clip == "idle":
                base = np.array(Image.open(STUDY/"imagegen_pixel"/f"idle_{direction}.png").convert("RGBA"))
            else:
                paint = Image.open(HERE/f"{clip}_{direction}_paint.png").convert("RGBA")
                guides = Image.open(HERE/f"{clip}_{direction}_guide.png").convert("RGBA")
            sockets = []
            for i in range(count):
                if clip == "idle":
                    color = idle_frame(base,i,sign)
                else:
                    guide = read_grid(guides,i%4,i//4,4,2).resize((64,64),Image.Resampling.NEAREST)
                    color = sample_paint(read_grid(paint,i%4,i//4,4,2),guide,sign)
                normal, glow, points = light_maps(color,sign)
                sockets.append(points)
                assert np.array_equal(color[:,:,3],normal[:,:,3])
                assert np.all(glow[:,:,3] <= color[:,:,3])
                for atlas,array in zip(atlases,(color,normal,glow)):
                    atlas.paste(Image.fromarray(array),(i*64,(2*number+side)*64))
                frames[clip,side,i] = Image.fromarray(color)
            data["sockets"][direction] = sockets
    for atlas,name in zip(atlases,("color","normal","emissive")):
        atlas.save(DEST/f"{name}.png")
    (DEST/"clips.json").write_text(json.dumps(meta,indent=2)+"\n",encoding="utf8")
    preview(frames)


if __name__ == "__main__":
    main()

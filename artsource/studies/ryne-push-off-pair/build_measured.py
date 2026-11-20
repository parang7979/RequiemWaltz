"""Repose the painted pixels of run frame 5 using fixed-length planar links."""
from pathlib import Path
from math import atan2, cos, radians, sin

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
SHEET = HERE.parents[1]/"pixellab/ryne_idle_16_three_quarter/run_se_v2_clean.png"
CELL, AA = 64, 6

# Joint centres in the 64 px cell. The far shoulder and the hip roots are
# inferred underneath the jacket and shorts; they are not rig data from PixelLab.
# Angles describe the *new direction* of each original rigid link, in screen XY.
CHAINS = {
    "near_leg": ([(34.0,29.8),(28.4,37.3),(19.6,43.0),(17.4,48.5)], [4,103,67]),
    "far_leg":  ([(37.6,28.8),(44.2,34.8),(40.8,45.8),(42.3,51.0)], [134,131,125]),
    "near_arm": ([(35.8,19.4),(38.0,23.5),(44.6,23.5),(48.5,23.0)], [144,151,120]),
    "far_arm":  ([(33.5,19.2),(29.0,23.4),(28.6,26.8),(27.0,28.3)], [18,-23,-48]),
}


def scanlines(im,ranges):
    gate = Image.new("L",im.size)
    pen = ImageDraw.Draw(gate)
    for y,l,r in ranges:
        pen.line((l,y,r,y),fill=255)
    return Image.composite(im,Image.new("RGBA",im.size),gate)


def limbs(im):
    # The crotch splits the two leg silhouettes; below it the background already
    # separates the boots. Keep the colours on their original anatomical limb.
    far = [(y,l,51) for y,l in [(28,37),(29,38),(30,38),(31,37),(32,38),(33,41)]]
    far += [(y,37,51) for y in range(34,53)]
    near = [(y,l,r) for y,l,r in [(28,31,36),(29,30,36),(30,29,37),
                    (31,29,36),(32,28,36),(33,29,37),(34,28,36)]]
    near += [(y,14,36) for y in range(35,51)]
    arm = [(y,l,r) for y,l,r in [(18,35,38),(19,34,38),(20,34,39),(21,34,40),
                                    (22,34,49),(23,34,49),(24,35,49),(25,37,49)]]
    rear = [(y,l,r) for y,l,r in [(19,32,34),(20,31,33),(21,31,33),(22,29,33),
                   (23,29,32),(24,28,31),(25,28,29),(26,28,29),(27,26,30),(28,27,30),(29,28,30)]]
    return {"near_leg":scanlines(im,near),"far_leg":scanlines(im,far),
            "near_arm":scanlines(im,arm),"far_arm":scanlines(im,rear)}


def repose(texture,chain):
    joints,angles = chain
    joints = np.array(joints,dtype=float)
    bones = np.diff(joints,axis=0)
    lengths = np.linalg.norm(bones,axis=1)
    dirs = np.array([[cos(radians(a)),sin(radians(a))] for a in angles])
    tips = joints[0]+np.cumsum(dirs*lengths[:,None],axis=0)
    target = np.vstack([joints[0],tips])
    assert np.allclose(np.linalg.norm(np.diff(target,axis=0),axis=1),lengths)
    # Assign the original pixels to rigid links, with a joint-width overlap.
    yy,xx = np.indices((CELL*AA,CELL*AA))
    dest = np.stack(((xx+.5)/AA,(yy+.5)/AA),axis=-1)
    out = np.zeros((*xx.shape,4),dtype=np.uint8)
    paint = np.asarray(texture)
    tangents = bones/lengths[:,None]
    dividers = tangents[:-1]+tangents[1:]
    dividers /= np.linalg.norm(dividers,axis=1)[:,None]
    for i,(bone,angle) in enumerate(zip(bones,angles)):
        turn = radians(angle)-atan2(bone[1],bone[0])
        c,s = cos(turn),sin(turn)
        src = (dest-target[i]) @ np.array([[c,-s],[s,c]])+joints[i]
        valid = np.ones(xx.shape,dtype=bool)
        if i:
            valid &= (src-joints[i]) @ dividers[i-1] >= -1.35
        if i<len(bones)-1:
            valid &= (src-joints[i+1]) @ dividers[i] <= 1.35
        ix,iy = np.clip(np.floor(src).astype(int),0,CELL-1).transpose(2,0,1)
        rgba = paint[iy,ix]
        valid &= rgba[:,:,3]>0
        out[valid] = rgba[valid]
    return Image.fromarray(out)


def make():
    with Image.open(SHEET) as sheet:
        original = sheet.convert("RGBA").crop((0,64,CELL,128))
    parts = limbs(original)
    # Keep the original collar, ponytail, torso and pouch on their fixed root.
    trunk = scanlines(original,
        [(y,0,63) for y in range(18)]+[(y,0,28) for y in range(18,26)]+
        [(y,l,r) for y,l,r in [(18,32,40),(19,32,40),(20,32,41),(21,32,41),
          (22,32,40),(23,32,40),(24,33,39),(25,33,40),(26,32,40),
          (27,31,40),(28,30,40),(29,29,39),(30,27,36),(31,26,33),(32,26,31),(33,27,30)]])
    # The near sleeve uncovers a few pixels of the bodice. Continue its local
    # colours under the shoulder instead of leaving the old forearm on the ribs.
    draw = ImageDraw.Draw(trunk)
    draw.polygon([(35,19),(39,20),(40,21),(40,23),(37,24),(35,24)],
                 fill=original.getpixel((37,25)))
    draw.line([(37,20),(39,21),(40,21)],fill=original.getpixel((39,23)))
    draw.line([(37,21),(39,22)],fill=original.getpixel((40,23)))
    big = (CELL*AA,CELL*AA)
    layers = {n:repose(parts[n],chain) for n,chain in CHAINS.items()}
    canvas = Image.new("RGBA",big)
    # The fist comes out in front of the chest while the rear shoulder remains behind it.
    glove = layers["far_arm"].crop((38*AA,0,big[0],24*AA))
    for layer in [layers['far_arm'],layers['far_leg'],layers['near_leg'],
                  trunk.resize(big,Image.Resampling.NEAREST),layers['near_arm']]:
        canvas.alpha_composite(layer)
    canvas.alpha_composite(glove,(38*AA,0))
    # Dominant covered source colour within each output pixel keeps the same
    # pixel clusters and avoids generating a second, softer palette.
    blocks = np.asarray(canvas).reshape(CELL,AA,CELL,AA,4).transpose(0,2,1,3,4).reshape(CELL,CELL,AA*AA,4)
    output = np.zeros((CELL,CELL,4),np.uint8)
    for y,x in zip(*np.nonzero((blocks[:,:,:,3]>127).sum(2)>=AA*AA*.40)):
        samples = blocks[y,x]; samples = samples[samples[:,3]>127]
        values,counts = np.unique(samples,axis=0,return_counts=True)
        output[y,x]=values[np.argmax(counts)]
    opposite = Image.fromarray(output)
    opposite.save(HERE/"measured-opposite.png")
    pair = Image.new("RGBA",(2*CELL,CELL))
    pair.paste(original,(0,0)); pair.paste(opposite,(CELL,0))
    pair.save(HERE/"measured-pair.png")
    plates = []
    for art in (original,opposite):
        card = Image.new("RGB",(320,320),(51,45,55))
        enlarged = art.resize(card.size,Image.Resampling.NEAREST)
        card.paste(enlarged,(0,0),enlarged)
        plates.append(card)
    swatch = Image.new("RGB",(640,320))
    swatch.paste(plates[0]); swatch.paste(plates[1],(320,0))
    palette = swatch.quantize(256,dither=Image.Dither.NONE)
    frames = [card.quantize(palette=palette,dither=Image.Dither.NONE) for card in plates]
    frames[0].save(HERE/"measured-pair.gif",save_all=True,append_images=frames[1:],
                   duration=460,loop=0,disposal=1,optimize=False)


if __name__=="__main__":
    make()

"""Separate the profile at anatomical seams and finish what the visible arm covers."""
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw

HERE = Path(__file__).resolve().parent
ARM = [(201,237),(207,226),(214,219),(230,216),(244,218),(251,226),(255,239),
       (254,250),(256,271),(260,279),(255,289),(248,295),(244,313),
       (242,345),(247,347),(249,359),(253,371),(255,387),(253,404),(249,407),
       (248,414),(243,416),(240,419),(234,420),(230,414),(225,413),(219,405),
       (216,390),(214,373),(214,355),(220,346),(215,320),(211,310),
       (202,313),(197,306),(198,296),(187,293),(181,285),(181,278),(188,270),
       (196,261),(200,253)]


def mask(size, points):
    out = Image.new("L",size)
    ImageDraw.Draw(out).polygon(points, fill=255)
    return out


def cut(src, gate):
    piece = src.copy()
    piece.putalpha(ImageChops.multiply(src.getchannel("A"),gate))
    return piece


def painted_panel(donor, size, rows):
    """Sample a section of the other view with independently registered side edges."""
    target = Image.new("RGBA",size)
    ys, left, right, src_y, src_l, src_r = np.asarray(rows).T
    for y in range(ys[0],ys[-1]+1):
        l,r,sy,sl,sr = [round(np.interp(y,ys,v)) for v in (left,right,src_y,src_l,src_r)]
        scan = donor.crop((sl-30,sy,sr-30+1,sy+1)).resize((r-l+1,1),Image.Resampling.BILINEAR)
        target.paste(scan,(l,y))
    outline = list(zip(left,ys))+list(zip(right[::-1],ys[::-1]))
    ImageDraw.Draw(target).line(outline+[outline[0]],fill=(33,22,34,255),width=3)
    return target


def shadow(piece):
    rgb = np.asarray(piece).copy()
    rgb[:,:,:3] = np.clip(rgb[:,:,:3]*[.73,.72,.79]+[4,2,5],0,255)
    return Image.fromarray(rgb)


def pieces():
    src = Image.open(HERE/"profile.png").convert("RGBA")
    donor = Image.open(HERE.parent/"ryne-turnaround-idle"/"pose-source.png").convert("RGBA")
    arm_gate = mask(src.size,ARM)
    arm = cut(src,arm_gate)
    # Restore the top of the sleeve behind the raised collar.
    shoulder = Image.new("RGBA",src.size)
    d = ImageDraw.Draw(shoulder)
    d.ellipse((207,215,251,247),fill="#751d32",outline="#301824",width=3)
    shoulder.alpha_composite(arm)
    arm = shoulder

    body = painted_panel(donor,src.size,[
        (209,217,259,263,260,302),(238,209,280,267,255,311),
        (265,208,286,277,256,312),(300,211,282,304,251,316),
        (321,210,289,324,244,317),(349,205,291,346,245,318),
        (366,211,289,355,250,322),(378,220,279,361,263,319)])
    torso_outline = [(193,191),(269,193),(288,218),(307,238),(305,259),
                     (289,280),(291,305),(302,323),(302,353),(291,375),
                     (266,377),(230,368),(208,352),(215,316),(209,291),
                     (211,262),(202,236)]
    visible = ImageChops.subtract(mask(src.size,torso_outline),arm_gate)
    body.alpha_composite(cut(src,visible))
    head = mask(src.size,[(45,10),(340,10),(340,211),(277,211),(255,216),
                          (226,223),(205,221),(188,211),(164,211),(163,303),(44,303)])
    body.alpha_composite(cut(src,head))

    leg = painted_panel(donor,src.size,[
        (349,225,262,347,275,308),(365,213,279,358,297,337),
        (381,209,282,379,296,343),(400,207,279,402,295,341),
        (420,209,274,419,296,342),(436,210,271,436,296,339),
        (448,211,264,448,294,334)])
    # The complete stocking, laced boot, heel and toe are the original side view.
    gate = mask(src.size,[(150,442),(209,441),(218,437),(263,438),(275,430),
                          (297,452),(310,718),(147,718)])
    leg.alpha_composite(cut(src,gate))
    hem = cut(src,mask(src.size,[(214,316),(227,323),(220,354),(211,379),
                                  (204,425),(160,426),(163,389),(183,346)]))
    # The belt pouch hangs from the waist while the thigh underneath moves.
    pouch = cut(src,mask(src.size,[(248,325),(282,316),(292,328),(287,355),
                                   (279,368),(271,389),(257,399),(254,377),(249,354)]))
    return dict(far_arm=shadow(arm),far_leg=shadow(leg),hem=hem,near_leg=leg,
                body=body,pouch=pouch,near_arm=arm)

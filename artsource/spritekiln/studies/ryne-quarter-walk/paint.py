"""Bind separate painted surfaces from the second figure on the turnaround."""
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw
from skin import cut, mask

HERE = Path(__file__).resolve().parent


def turn_boot(front,travel,t):
    if t<=0:
        return front
    if t>=1:
        return travel
    # Register both painted outlines before mixing the pixels of an in-between.
    out = front.copy()
    for y in range(624,711):
        strips = [im.crop((0,y,im.width,y+1)) for im in (front,travel)]
        bounds = [s.getchannel("A").getbbox() for s in strips]
        if not all(bounds):
            out.paste(Image.blend(*strips,t),(0,y))
            continue
        l,r = [round((1-t)*bounds[0][i]+t*bounds[1][i]) for i in (0,2)]
        registered = [s.crop(b).convert("RGBa").resize((r-l,1),Image.Resampling.BILINEAR)
                      for s,b in zip(strips,bounds)]
        out.paste((0,0,0,0),(0,y,out.width,y+1))
        out.paste(Image.blend(*registered,t).convert("RGBA"),(l,y))
    return out


def pieces(turn=1.0, source=None):
    src = source if source is not None else Image.open(HERE/"quarter.png").convert("RGBA")
    def region(points):
        return mask(src.size, points)

    near_arm = region([(179,225),(183,217),(193,214),(207,217),(214,224),
                       (216,238),(211,254),(208,271),(205,287),(205,299),
                       (197,306),(190,312),(179,319),(163,344),(163,355),
                       (160,368),(160,386),(159,409),(152,410),(149,402),
                       (145,397),(144,402),(147,413),(145,424),(116,429),
                       (106,412),(107,384),(118,366),(119,346),(143,341),
                       (153,308),(145,304),(146,296),(140,284),(142,272),
                       (163,256),(174,240)])
    far_arm = region([(290,223),(302,230),(304,258),(315,265),(330,277),
                      (331,293),(322,299),(322,306),(333,340),(346,341),
                      (350,363),(365,384),(365,415),(349,430),(329,425),
                      (321,413),(323,394),(317,406),(311,402),(313,384),
                      (313,370),(310,352),(297,323),(291,312),(286,299),
                      (291,280),(297,264),(285,252)])
    # The far sleeve's cap is occluded by the chest in the reference.
    far = Image.new("RGBA",src.size)
    pen = ImageDraw.Draw(far)
    pen.polygon([(278,223),(291,220),(300,227),(311,263),(315,278),
                 (294,287),(282,267)],fill="#841f33",outline="#331924",width=3)
    visible_far = ImageChops.subtract(far_arm, region([(276,213),(305,213),(307,249),
                           (304,260),(296,266),(286,266),(277,253)]))
    far.alpha_composite(cut(src,visible_far))

    near_pouch = region([(164,349),(215,347),(230,346),(226,365),(220,382),
                         (215,405),(211,431),(201,436),(154,431),(153,410),
                         (159,388),(160,365)])
    # Extend the visible near-thigh paint behind the pouch along the downward
    # slope of the garter. Its two borders meet exactly when the hip uncovers it.
    rows = np.array([(343,213,245,236),(361,200,254,236),(382,191,257,226),
                     (399,187,255,221),(417,184,250,218),(433,183,248,215),
                     (440,183,246,204),(451,182,242,182)])
    y,x = np.indices((src.height,src.width))
    left,right,edge = [np.interp(y,rows[:,0],v) for v in rows.T[1:]]
    sx = np.where(x<edge,np.minimum(edge+(edge-x)*.37,right-2),x)
    sy = y + (sx-x)*.22
    tex = np.asarray(src)[np.clip(np.rint(sy).astype(int),0,src.height-1),
                          np.clip(np.rint(sx).astype(int),0,src.width-1)].copy()
    tex[:,:,3] *= (x>=left)&(x<=right)&(y>=343)&(y<=451)
    near_leg = Image.fromarray(tex)
    ImageDraw.Draw(near_leg).line([(int(l),int(k)) for k,l,*_ in rows],fill="#35232e",width=3)
    visible_near = region([(180,440),(210,438),(246,440),(241,462),(228,503),
                           (211,548),(211,718),(110,718),(111,542),(171,450)])
    near_leg.alpha_composite(cut(src,visible_near))
    far_leg = cut(src,region([(270,346),(305,342),(313,366),(317,399),(315,438),
                              (321,526),(351,717),(215,717),(216,554),(231,550),
                              (246,487),(250,454),(250,428),(254,402),(260,369)]))
    # The standing right boot faces the viewer. Register the more side-facing
    # toe box from the other boot below its ankle strap for the travel pose.
    donor = far_leg.transform(src.size,Image.Transform.AFFINE,
                              (1/.86,0,251-157/.86,0,1,-6),
                              Image.Resampling.BICUBIC)
    # Blend in premultiplied colour so the outer edge keeps its ink.
    transition = np.clip((y-624)/23,0,1)
    gate = Image.fromarray(np.rint(255*transition**2*(3-2*transition)).astype("uint8"))
    turned = Image.composite(donor.convert("RGBa"),near_leg.convert("RGBa"),gate).convert("RGBA")
    near_leg = turn_boot(near_leg,turned,turn)
    body = Image.new("RGBA",src.size)
    # Dark jacket lining behind the raised arms and shorts behind the belt pouch.
    pen = ImageDraw.Draw(body)
    pen.polygon([(191,216),(219,216),(230,246),(222,292),(206,309),(197,303),
                 (203,276)],fill="#691b2b",outline="#321825",width=3)
    pen.polygon([(288,238),(300,243),(304,264),(293,307),(280,302)],
                fill="#642131",outline="#321825",width=3)
    pen.polygon([(226,316),(287,318),(304,347),(310,363),(285,366),(261,376),
                 (246,370),(210,361),(206,348)], fill="#342431",outline="#251b25",width=3)
    raw_body = region([(170,192),(304,193),(311,215),(314,245),(309,264),
                       (296,276),(294,301),(304,323),(314,346),(314,365),
                       (295,363),(278,370),(264,376),(253,374),(231,360),
                       (215,360),(217,341),(181,348),(191,326),(211,302),
                       (214,290),(203,274),(179,230)])
    body.alpha_composite(cut(src,ImageChops.subtract(ImageChops.subtract(
        raw_body,near_arm),visible_far)))
    top = region([(34,9),(333,9),(336,211),(311,217),(290,228),(263,224),
                  (229,232),(207,220),(179,219),(161,213),(153,236),
                  (142,266),(140,311),(33,316)])
    body.alpha_composite(cut(src,top))
    pouch = cut(src,ImageChops.subtract(near_pouch,near_arm))
    return {"far_arm":far,"far_leg":far_leg,"near_leg":near_leg,"body":body,
            "pouch":pouch,"near_arm":cut(src,near_arm)}

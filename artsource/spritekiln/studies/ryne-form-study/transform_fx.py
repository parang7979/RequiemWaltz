"""Pixel effects over the SpriteKiln form-change, hover and turn frames."""

from math import cos, hypot, pi, sin

from PIL import Image, ImageChops, ImageDraw, ImageFilter


WINE = (128, 32, 83, 235)
ROSE = (227, 68, 134, 255)
PINK = (255, 139, 187, 255)
PEARL = (255, 224, 232, 255)
WHITE = (255, 247, 238, 255)
FLASH = (0, 0, 0, 0, 0, 0.035, 0.08, 0.21, 1, 0.99, 0.96, 0.92,
         0.84, 0.72, 0.58, 0.43, 0.25, 0.16, 0.10, 0.05, 0.025)


def _curve(points, t):
    u = 1 - t
    weights = (u ** 3, 3 * u * u * t, 3 * u * t * t, t ** 3)
    return tuple(sum(p[axis] * w for p, w in zip(points, weights)) for axis in (0, 1))


def _filament(draw, points, width, start=0, end=1, colors=(WINE, ROSE, PEARL)):
    """A tapered swash with the light on its inner bevel; all vertices are native pixels."""
    if end <= start:
        return
    steps = max(8, int((end - start) * 48))
    samples = []
    for i in range(steps + 1):
        along = i / steps
        t = start + along * (end - start)
        x, y = _curve(points, t)
        a, b = _curve(points, max(0, t - .008)), _curve(points, min(1, t + .008))
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = max(.01, hypot(dx, dy))
        size = width * sin(pi * along) ** .82 * (.35 + along)
        samples.append((x, y, -dy / length, dx / length, size))

    def strip(sel, left, right, color):
        if len(sel) < 2:
            return
        edge = lambda k, s: (round(s[0] + k * s[2] * s[4]), round(s[1] + k * s[3] * s[4]))
        draw.polygon([edge(left, s) for s in sel] + [edge(right, s) for s in reversed(sel)], fill=color)

    strip(samples, -1, 1, colors[0])
    strip(samples[steps // 9:], -.62, .83, colors[1])
    strip(samples[steps // 3: -max(1, steps // 12)], -.51, -.04, colors[2])


def _spark(draw, x, y, size=2, warm=False):
    x, y = round(x), round(y)
    color = (255, 189, 153, 255) if warm else PINK
    if size <= 1:
        draw.point((x, y), fill=color)
        return
    draw.line((x, y - size, x, y + size), fill=color)
    draw.line((x - size + 1, y, x + size - 1, y), fill=color)
    draw.line((x, y - 1, x, y + 1), fill=PEARL)
    draw.point((x, y), fill=WHITE)


def _shard(draw, x, y, ux, uy, length, width):
    normal = (-uy, ux)
    draw.polygon([(round(x - length * ux), round(y - length * uy)),
                  (round(x + normal[0] * width), round(y + normal[1] * width)),
                  (round(x + ux * 2), round(y + uy * 2)),
                  (round(x - normal[0] * width), round(y - normal[1] * width))], fill=PINK)
    draw.line((round(x - ux * length * .48), round(y - uy * length * .48),
               round(x + ux), round(y + uy)), fill=PEARL)


def _charge(back, front, f):
    # Flares rise out of a flattened reflection. The wisps describe offset crescents,
    # leaving a clear opening over Ryne's face.
    growth = min(1, (f - 1) / 6)
    decay = min(1, max(0, (13 - f) / 5))
    if growth <= 0 or decay <= 0:
        return
    spread, rise = (14 + 23 * growth), (8 + 49 * growth)
    ground = 79
    left = ((48, ground), (48 - .72 * spread, ground + 1),
            (43 - spread, ground - .64 * rise), (53 - .48 * spread, ground - rise))
    right = ((49, ground), (51 + .85 * spread, ground + 2),
             (56 + spread, ground - .52 * rise), (52 + .61 * spread, ground - .89 * rise))
    start = max(0, (f - 7) * .095)
    _filament(back, left, (1.0 + 1.25 * growth) * decay, start, .72 + .28 * growth)
    _filament(back, right, (1.4 + 1.70 * growth) * decay, start, .70 + .24 * growth)
    _filament(front, ((48 - spread * .78, ground - rise * .37),
                      (45 - spread, ground + 1), (45 - spread * .27, ground + 2),
                      (57, ground - 4)), (1.05 + growth * .65) * decay, start, 1,
              (WINE, PINK, PEARL))
    if f >= 4:
        # A finer echo breaks away to the left, with a different radius and timing.
        _filament(back, ((31 - growth * 4, ground - 3), (12, ground - 12),
                          (10, ground - 33), (25, ground - 40)), .76 * decay,
                  max(.12, start), .24 + .72 * growth, (WINE, ROSE, PINK))
    if 5 <= f <= 10:
        spin = (f - 5) / 5
        # One broken oblique helix crests above the head as the side curls reach full height.
        top = ((62, 67), (79, 40), (69, 3), (39, 12))
        _filament(back, top, .9 + .8 * sin(pi * spin), max(0, spin * 1.33 - .46),
                  min(1, .22 + 1.4 * spin), (WINE, ROSE, PINK))
        if 7 <= f <= 9:
            x, y = _curve(top, min(.96, .22 + 1.4 * spin))
            _spark(back, x, y, 2)
    if 3 <= f <= 10:
        # A very shallow, interrupted ankle-level ring establishes the floor on lift-off.
        foot_arc = ((23, ground - 2), (33, ground + 4), (59, ground + 4), (73, ground - 2))
        u = (f - 3) / 7
        _filament(front, foot_arc, .75, max(0, u * .94 - .13), min(1, .27 + 1.19 * u),
                  (WINE, ROSE, PEARL))
    for k in range(9):
        phase = ((f - 2) * .103 + k * .179) % 1
        if phase > growth or phase > decay + .32:
            continue
        a = pi * (k / 8)
        x = 48 + cos(a) * (8 + 26 * phase)
        y = ground - 1 - phase * (8 + 22 * abs(cos(1.8 * a)) + 9 * growth)
        _spark(front, x, y, 2 if k in (2, 7) and .36 < phase < .81 else 1)


def _burst(back, front, f):
    if not 8 <= f <= 18:
        return
    age = f - 8
    heart = (49, 43 - min(6, age))
    angles = (-2.92, -2.48, -2.24, -1.98, -1.44, -1.06, -.68, -.28,
              .14, .53, 1.01, 1.34, 1.88, 2.48, 2.82)
    for k, a in enumerate(angles):
        delay = (k * 7 % 5) * .48
        u = (age - delay) / (4.5 + k % 4)
        if not 0 <= u < 1:
            continue
        ux, uy = cos(a), sin(a)
        r = 12 + (13 + 4 * (k % 4)) * (1 - (1 - u) ** 2)
        x, y = heart[0] + ux * r, heart[1] + uy * r
        _shard(back if k % 3 else front, x, y, ux, uy, 1.3 + (1 - u) * (3 + k % 5),
               1.2 * (1 - u))
    for k, (x, y) in enumerate(((19, 26), (74, 20), (77, 55), (24, 65), (65, 12), (36, 17))):
        if (age + k) % 6 in (1, 2) and age < 8:
            _spark(front, x + sin(k + age * .3) * 2, y - age * .5, 2)


def _flight(back, front, clip, f):
    if clip == "hover":
        # A few embers behind the feet and tips let the hair silhouette breathe.
        trails = [(23, 67), (16, 47), (26, 54)]
        for k, (x, y) in enumerate(trails):
            phase = (f / 8 + k * .37) % 1
            if .16 <= phase <= .80:
                back.line((round(x - 8 * phase), round(y + 3 * phase),
                           round(x - 8 * phase + 1), round(y + 3 * phase)), fill=PINK if k == 0 else ROSE)
        return
    # The bank leaves a single curling wake and a smaller echo, dissipating on exit.
    if f < 2 or f > 13:
        return
    t = (f - 2) / 11
    curve = ((26, 37), (2, 67), (39, 90), (76, 61))
    echo = ((26, 44), (14, 73), (54, 84), (78, 53))
    start = max(0, 1.30 * t - .44)
    end = min(1, .12 + 1.38 * t)
    _filament(back, curve, .8 + 1.2 * sin(pi * t), start, end)
    if .17 < t < .93:
        _filament(back, echo, .58, max(0, start - .18), max(0, end - .16), (WINE, ROSE, PINK))
    if 3 <= f <= 13:
        x, y = _curve(curve, min(.97, end))
        _spark(front, x, y, 2 if f in (6, 7, 10) else 1)


def _layers(size, clip, frame, direction):
    back = Image.new("RGBA", (96, 96))
    front = Image.new("RGBA", (96, 96))
    behind, ahead = ImageDraw.Draw(back), ImageDraw.Draw(front)
    flash = 0
    if clip == "transform":
        flash = FLASH[frame] if 0 <= frame < len(FLASH) else 0
        _charge(behind, ahead, frame)
        _burst(behind, ahead, frame)
        if 15 <= frame <= 26:
            for k, (x, y) in enumerate(((25, 48), (65, 29), (37, 19), (59, 69), (20, 37))):
                age = frame - 15 - k
                if 0 <= age < 5:
                    _spark(ahead, x + 1.2 * sin(age * .6), y - age,
                           2 if age in (1, 2) and k % 2 else 1)
    elif clip == "launch" and frame >= 6:
        _flight(behind, ahead, "hover", (frame - 8) % 8)
    elif clip in ("hover", "air_turn"):
        _flight(behind, ahead, clip, frame)
    # The actor and its effects share the raised ground pivot in the revised framing.
    def align_to_ground(layer):
        placed = Image.new("RGBA", layer.size)
        placed.paste(layer, (0, 6))
        return placed
    back, front = align_to_ground(back), align_to_ground(front)
    if direction == "w":
        back, front = (layer.transpose(Image.Transpose.FLIP_LEFT_RIGHT) for layer in (back, front))
    if size != (96, 96):
        back, front = (layer.resize(size, Image.Resampling.NEAREST) for layer in (back, front))
    return back, front, flash


def _lit_actor(actor, flash):
    if not flash:
        return actor
    # A single paper-white silhouette at release, then restore the costume's values from its midtones.
    result = Image.blend(actor, Image.new("RGBA", actor.size, (255, 238, 246, 255)), flash)
    result.putalpha(actor.getchannel("A"))
    return result


def _rim_glow(actor, flash):
    alpha = actor.getchannel("A")
    outer = ImageChops.subtract(alpha.filter(ImageFilter.MaxFilter(5)), alpha)
    outer = outer.point(lambda x: round(x * .30 * flash))
    inner = ImageChops.subtract(alpha.filter(ImageFilter.MaxFilter(3)), alpha)
    inner = inner.point(lambda x: round(x * .74 * flash))
    halo = Image.new("RGBA", actor.size, (235, 67, 151, 0))
    halo.putalpha(outer)
    rim = Image.new("RGBA", actor.size, (255, 149, 209, 0))
    rim.putalpha(inner)
    return Image.alpha_composite(halo, rim)


def _compose(actor, clip, frame, direction):
    back, front, flash = _layers(actor.size, clip, frame, direction)
    if flash > 0:
        back = Image.alpha_composite(back, _rim_glow(actor, flash))
    lit = _lit_actor(actor, flash)
    result = Image.alpha_composite(Image.alpha_composite(back, lit), front)
    return result, back, front, flash, lit


def finish_frame(image, clip_name, frame_index, direction):
    """Return one native-resolution color frame. Directions are e or w, indices start at zero."""
    return _compose(image.convert("RGBA"), clip_name, frame_index, direction)[0]


def finish_layers(color, normal, emissive, clip_name, frame_index, direction):
    """Return aligned RGBA color, camera-space normal, and light-emission images."""
    color = color.convert("RGBA")
    result, back, front, flash, lit = _compose(color, clip_name, frame_index, direction)
    visible_back = back.copy()
    visible_back.putalpha(ImageChops.multiply(back.getchannel("A"), ImageChops.invert(color.getchannel("A"))))
    emission = Image.alpha_composite(visible_back, emissive.convert("RGBA"))
    if flash:
        glow = lit.copy()
        glow.putalpha(color.getchannel("A").point(lambda x: round(x * flash)))
        emission = Image.alpha_composite(emission, glow)
    emission = Image.alpha_composite(emission, front)
    normals = Image.new("RGBA", color.size, (128, 128, 255, 255))
    normals = Image.alpha_composite(normals, normal.convert("RGBA"))
    normals.putalpha(result.getchannel("A"))
    return result, normals, emission

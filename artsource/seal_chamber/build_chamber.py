"""Paint the Seal Chamber at the native game resolution."""

from pathlib import Path
from random import Random

from PIL import Image, ImageDraw


OUTPUT = Path(__file__).resolve().parents[2] / "assets/rooms/seal_chamber.png"


def chamber():
    rng = Random(124)
    image = Image.new("RGB", (640, 360), "#1a1427")
    d = ImageDraw.Draw(image)
    d.polygon([(53, 79), (587, 79), (627, 311), (609, 329), (32, 329), (13, 311)], fill="#39273d")
    d.polygon([(64, 93), (574, 93), (607, 308), (578, 316), (59, 316), (34, 306)], fill="#352641")
    for row, y in enumerate(range(103, 314, 15)):
        width = 32
        left = 59 - row * 2
        palette = ["#372943", "#3a2b46", "#3e2e4b", "#42304d", "#382943", "#402d48"]
        for x in range(left - (row % 2) * 16, 640 - left - 15, width):
            right = min(x + width - 2, 640 - left)
            start = max(x, left)
            d.rectangle((start, y, right, min(y + 13, 314)), fill=rng.choice(palette))
            d.line((start + 1, y, right - 1, y), fill="#4a3651")
            for _ in range(3):
                xx = rng.randint(start + 1, max(start + 1, right - 4))
                yy = min(313, y + rng.randint(2, 12))
                d.line((xx, yy, min(right, xx + rng.randrange(1, 5)), yy), fill=rng.choice(["#33263e", "#47324b"]))
    d.polygon([(56, 107), (57, 104), (582, 104), (598, 305), (42, 305)], outline="#59405a")
    d.polygon([(62, 114), (576, 114), (593, 300), (47, 300)], outline="#4f3a54")
    for x in range(71, 580, 12):
        d.line((x, 308, x + 4, 308), fill="#634660")
    d.rectangle((33, 50, 606, 105), fill="#31253a")
    for row, y in enumerate(range(51, 105, 9)):
        for x in range(35 - (row % 2) * 14, 607, 29):
            d.rectangle((max(34, x), y, min(x + 27, 605), y + 7),
                        fill=rng.choice(["#3e2f47", "#42324b", "#3a2c44", "#44324b"]))
            d.line((max(35, x + 1), y, min(x + 26, 605), y), fill="#4e3a52")
    d.rectangle((32, 47, 607, 52), fill="#4e3b54")
    d.rectangle((32, 101, 607, 106), fill="#5b4259")
    d.rectangle((32, 106, 607, 110), fill="#251e33")
    for x in (139, 226, 320, 414, 501):
        door = x == 320
        top = 51 if door else 58
        for width, tint in [(16, "#644960"), (13, "#4e3653"), (10, "#222034")]:
            d.polygon([(x - width, 99), (x - width, top + 16), (x - width + 5, top + 8),
                       (x, top), (x + width - 5, top + 8), (x + width, top + 16),
                       (x + width, 99)], fill=tint)
        if not door:
            for dx in (-4, 0, 4):
                d.line((x + dx, top + 16, x + dx, 96), fill="#634665")
    for x in (52, 180, 460, 588):
        d.rectangle((x-9, 50, x+8, 111), fill="#241c31")
        d.rectangle((x-7, 50, x+6, 106), fill="#513a54")
        d.line((x-6, 53, x-6, 103), fill="#79566a", width=2)
        d.line((x+5, 56, x+5, 102), fill="#3a293f", width=2)
        for y in (52, 96, 102, 109):
            d.rectangle((x-10, y, x+9, y+3), fill="#594057")
            d.line((x-10, y, x+8, y), fill="#806070")
        if x in (180, 460):
            d.polygon([(x-14, 60), (x+14, 60), (x+14, 88), (x+9, 93),
                       (x, 98), (x-10, 93), (x-14, 88)], fill="#5a263f")
            d.line((x-13, 62, x-13, 88, x, 96, x+13, 88, x+13, 62), fill="#a0656d")
            d.polygon([(x, 67), (x+6, 76), (x, 85), (x-6, 76)], outline="#d19979")
            d.line((x, 71, x, 83), fill="#d19979")
    for x, y in ((73, 133), (567, 133), (61, 290), (579, 290)):
        glow = Image.new("RGBA", image.size)
        gd = ImageDraw.Draw(glow)
        for radius, alpha in [(23, 14), (15, 19), (9, 28)]:
            gd.ellipse((x-radius, y-radius//2, x+radius, y+radius//2), fill=(226, 132, 116, alpha))
        image.paste(glow, (0, 0), glow)
        d.rectangle((x-4, y-1, x+4, y+4), fill="#2a2036")
        d.line((x-4, y, x+4, y), fill="#bf7c75")
        d.polygon([(x-3, y-2), (x-3, y-6), (x, y-12), (x+3, y-8), (x+3, y-3),
                   (x+1, y)], fill="#ea927b")
        d.line((x, y-8, x, y-2), fill="#ffe4aa", width=2)
    for x, y in ((92, 116), (540, 115), (92, 295), (550, 296), (260, 113), (389, 112)):
        for _ in range(24):
            xx = x + rng.randrange(-12, 13)
            yy = y + rng.randrange(-5, 6)
            d.line((xx, yy, xx + rng.randrange(1, 4), yy),
                   fill=rng.choice(["#563759", "#6d4167", "#895378", "#43344a"]))
    cx, cy = 320, 209
    for rad, ink in [(76, "#5d435f"), (72, "#513a58"), (59, "#4c3653"), (39, "#554059")]:
        d.ellipse((cx-rad, cy-rad//2, cx+rad, cy+rad//2), outline=ink)
    d.polygon([(cx-70, cy), (cx, cy-31), (cx+70, cy), (cx, cy+31)], outline="#59405a")
    d.polygon([(cx-43, cy), (cx, cy-19), (cx+43, cy), (cx, cy+19)], outline="#634761")
    d.polygon([(cx-12, cy), (cx, cy-8), (cx+12, cy), (cx, cy+8)], fill="#4b3455", outline="#6b4d69")
    image.save(OUTPUT)


if __name__ == "__main__":
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    chamber()

"""Paint the seal chamber and independent actors at native game resolution."""

from pathlib import Path
from random import Random

from PIL import Image, ImageDraw


OUT = Path(__file__).resolve().parents[2] / "assets" / "waltz_combat"
OUT.mkdir(parents=True, exist_ok=True)
INK = "#201225"
BURGUNDY, WINE, RED, ROSE = "#52213e", "#82233f", "#af3155", "#d84a69"
GOLD, LIGHT_GOLD = "#d29264", "#f5bf80"
HAIR_SHADOW, HAIR, HAIR_LIGHT = "#a997bc", "#ddd2e6", "#f6ecf6"
SKIN_SHADOW, SKIN = "#df9fa5", "#f9c7b5"


def waltz(view, pose):
    sprite = Image.new("RGBA", (40, 44))
    d = ImageDraw.Draw(sprite)
    p = d.polygon
    step = [0, -2, 2, 0][pose]
    back = view == 1
    side = view == 2
    foot_x = 1 if side else 0
    for index, x in enumerate((13 + foot_x, 23 + foot_x)):
        y = 39 + (step if index == 0 else -step)
        p([(x - 2, y - 5), (x + 4, y - 5), (x + 5, y + 2),
           (x + 2, y + 3), (x - 3, y + 3), (x - 4, y + 1)], fill=INK)
        p([(x - 1, y - 4), (x + 3, y - 4), (x + 3, y + 1),
           (x - 2, y + 1)], fill=BURGUNDY)
        d.line((x - 1, y, x + 2, y), fill=GOLD)
    hem = 1 if step else 0
    p([(12, 20), (27, 20), (30, 27), (32, 35 + hem), (27, 40),
       (19, 39), (11, 40), (4, 36), (7, 29)], fill=INK)
    p([(12, 23), (26, 23), (28, 28), (30, 35 + hem), (26, 38),
       (19, 37), (11, 38), (6, 35), (9, 29)], fill=WINE)
    p([(11, 25), (16, 27), (14, 35), (10, 36), (7, 34)], fill=RED)
    p([(23, 25), (27, 28), (28, 35), (24, 37), (20, 35)], fill=BURGUNDY)
    d.line((7, 34, 11, 36, 19, 35, 26, 36, 29, 34), fill=GOLD)
    for x, y in [(10, 34), (13, 35), (22, 35), (26, 34)]:
        d.point((x, y), fill=LIGHT_GOLD)
    if not back:
        p([(14, 26), (23, 25), (23, 31), (21, 34), (14, 33)], fill="#381d39")
        d.line((14, 32, 22, 32), fill=GOLD)
        d.point((18, 32), fill=LIGHT_GOLD)
        d.line((10, 27, 10, 31 + (step < 0)), fill=RED, width=3)
        d.line((11, 31 + (step < 0), 12, 31 + (step < 0)), fill=SKIN)
        d.line((25, 27, 26, 30 + (step > 0)), fill=ROSE, width=3)
        d.line((26, 30 + (step > 0), 27, 30 + (step > 0)), fill=SKIN)

    # Repaint the hood as a single small cluster, with one pixel of gait bob.
    bob = 1 if pose == 2 else 0
    head = Image.new("RGBA", (40, 28))
    h = ImageDraw.Draw(head)
    p = h.polygon
    if side:
        p([(9, 5), (15, 1), (24, 1), (30, 5), (34, 12), (35, 19),
           (31, 24), (24, 26), (15, 26), (8, 23), (4, 24), (6, 17), (6, 11)], fill=INK)
        p([(10, 6), (16, 3), (24, 3), (29, 6), (32, 11), (33, 18),
           (29, 23), (22, 25), (15, 24), (8, 21), (7, 16)], fill=WINE)
        p([(8, 16), (10, 7), (18, 4), (24, 4), (29, 8), (25, 11),
           (19, 13), (16, 18), (10, 22)], fill=RED)
        p([(10, 10), (15, 5), (23, 4), (27, 6), (17, 7), (14, 11)], fill=ROSE)
        p([(21, 11), (28, 9), (32, 13), (33, 19), (29, 23), (23, 23), (20, 19)], fill=SKIN_SHADOW)
        p([(25, 13), (30, 13), (31, 17), (32, 19), (29, 22), (24, 21), (23, 17)], fill=SKIN)
        p([(21, 11), (28, 9), (31, 12), (29, 14), (26, 13), (25, 17), (22, 19), (21, 16)], fill=HAIR)
        h.line((22, 13, 26, 11, 29, 11), fill=HAIR_LIGHT)
        h.line((18, 17, 20, 12, 25, 9, 28, 8, 31, 11), fill=GOLD)
        h.point((22, 11), fill=LIGHT_GOLD)
        h.point((28, 9), fill=LIGHT_GOLD)
        if pose == 3:
            h.line((27, 18, 29, 18), fill=INK)
        else:
            h.rectangle((27, 16, 29, 18), fill="#542442")
            h.point((28, 16), fill="#fff0e4")
        h.point((30, 20), fill="#b96779")
        h.point((25, 20), fill="#e88a97")
    else:
        p([(13, 3), (18, 1), (24, 1), (29, 4), (33, 9), (35, 17),
           (33, 23), (29, 26), (11, 26), (6, 23), (5, 17), (7, 9)], fill=INK)
        p([(13, 5), (18, 3), (24, 3), (29, 6), (32, 11), (33, 18),
           (31, 22), (28, 24), (11, 24), (8, 21), (7, 17), (9, 10)], fill=WINE)
        p([(9, 16), (10, 10), (14, 6), (19, 4), (24, 4), (29, 7),
           (31, 13), (27, 11), (19, 10), (12, 15), (10, 19)], fill=RED)
        p([(10, 11), (14, 6), (19, 4), (24, 4), (27, 6), (18, 6), (14, 11)], fill=ROSE)
        if back:
            p([(18, 7), (24, 7), (29, 12), (29, 20), (25, 24), (17, 24),
               (12, 21), (12, 15)], fill=RED)
            h.line((22, 7, 23, 12, 23, 21), fill=WINE)
            h.line((17, 23, 24, 24, 29, 21), fill=GOLD)
            h.point((10, 20), fill=LIGHT_GOLD)
        else:
            p([(12, 13), (16, 9), (23, 8), (28, 11), (30, 16), (29, 22),
               (24, 26), (17, 26), (12, 22), (10, 18)], fill=BURGUNDY)
            p([(13, 14), (17, 10), (23, 10), (27, 13), (28, 18), (27, 22),
               (23, 24), (18, 24), (14, 22), (12, 18)], fill=SKIN)
            p([(13, 14), (17, 10), (23, 10), (26, 12), (27, 16), (24, 15),
               (21, 13), (21, 17), (18, 14), (16, 19), (13, 20), (12, 18)], fill=HAIR)
            h.line((15, 14, 17, 11, 23, 11, 25, 13), fill=HAIR_LIGHT)
            h.point((14, 17), fill=HAIR_SHADOW)
            h.point((23, 14), fill=HAIR_SHADOW)
            h.line((10, 18, 11, 13, 15, 9, 20, 7, 25, 8, 29, 12, 31, 18), fill=GOLD)
            for at in ((11, 15), (14, 10), (18, 8), (23, 8), (27, 10), (30, 15)):
                h.point(at, fill=LIGHT_GOLD)
            for x in (16, 24):
                if pose == 3:
                    h.line((x, 19, x + 2, 19), fill=INK)
                    continue
                h.rectangle((x, 17, x + 2, 20), fill="#6c2949")
                h.point((x + 1, 17), fill="#fff6e9")
                h.point((x + 1, 20), fill="#bc5a79")
            h.line((13, 21, 15, 21), fill="#e58a94")
            h.line((25, 21, 27, 21), fill="#e58a94")
            h.point((21, 22), fill="#9d526c")
    sprite.alpha_composite(head, (0, bob))
    if not back:
        d.polygon([(19, 26), (22, 25), (24, 27), (21, 30), (19, 29)], fill=BURGUNDY)
        d.point((21, 27), fill=LIGHT_GOLD)
    return sprite


def requiem():
    sprite = Image.new("RGBA", (96, 92))
    d = ImageDraw.Draw(sprite)
    p = d.polygon
    p([(59, 51), (56, 60), (64, 67), (77, 65), (89, 58), (92, 52),
       (90, 68), (82, 76), (68, 79), (54, 75), (45, 75), (34, 80),
       (30, 87), (38, 90), (26, 90), (19, 85), (20, 76), (30, 65), (37, 58)], fill="#49276d")
    p([(55, 56), (52, 63), (63, 72), (73, 72), (83, 69), (90, 63),
       (84, 72), (75, 76), (62, 76), (54, 73), (44, 72), (32, 77),
       (26, 84), (31, 88), (24, 85), (23, 79), (28, 72), (40, 64)], fill="#8846b9")
    p([(52, 59), (48, 66), (52, 69), (41, 69), (33, 73), (26, 79),
       (29, 72), (41, 65)], fill="#c77fe9")
    p([(36, 32), (57, 29), (67, 34), (71, 41), (78, 47), (85, 41), (89, 40),
       (87, 52), (80, 56), (72, 54), (65, 51), (60, 62), (48, 68),
       (34, 63), (31, 54), (24, 51), (18, 57), (10, 55), (7, 47), (10, 38),
       (13, 44), (17, 46), (25, 40)], fill="#38204f")
    p([(27, 42), (35, 36), (57, 33), (65, 37), (69, 46), (77, 50),
       (85, 46), (83, 51), (79, 53), (70, 51), (62, 47), (58, 59),
       (49, 64), (39, 61), (35, 54), (32, 48), (23, 47), (16, 53), (12, 51), (11, 46),
       (16, 49), (20, 46)], fill="#9e52cb")
    p([(38, 40), (49, 40), (57, 43), (55, 54), (49, 61), (40, 57), (35, 49)], fill="#633586")
    d.line((32, 43, 38, 51, 49, 57, 58, 50, 66, 41), fill="#dc9ef2", width=2)
    d.line((34, 45, 40, 52, 50, 57), fill="#ffe2b5")
    p([(49, 53), (52, 57), (48, 62), (44, 57)], fill="#f6b9f3")
    p([(27, 12), (26, 6), (29, 1), (31, 10), (38, 15), (42, 14), (49, 4),
       (55, 0), (53, 9), (56, 14), (64, 11), (70, 2), (72, 7), (69, 16),
       (64, 22), (65, 30), (60, 39), (50, 46), (37, 40), (30, 32), (27, 23), (20, 20),
       (17, 14), (18, 9), (22, 15)], fill="#452360")
    p([(28, 10), (28, 5), (31, 12), (38, 18), (43, 17), (49, 9), (53, 5), (51, 12),
       (56, 18), (65, 15), (70, 7), (68, 14), (62, 21), (63, 29), (58, 36),
       (50, 42), (39, 37), (32, 30), (29, 22), (22, 19), (19, 14), (23, 17), (31, 18)], fill="#a351d0")
    p([(32, 22), (40, 19), (49, 14), (57, 20), (61, 21), (61, 30),
       (55, 37), (50, 41), (41, 37), (35, 31)], fill="#312140")
    p([(35, 25), (42, 26), (47, 30), (42, 32), (37, 29)], fill="#fac8f9")
    p([(53, 28), (60, 24), (58, 29), (54, 32), (51, 31)], fill="#fac8f9")
    p([(44, 34), (49, 36), (56, 33), (52, 38), (48, 39)], fill="#e080df")
    d.polygon([(49, 16), (53, 21), (49, 25), (45, 21)], fill="#ffc494")
    d.line((27, 15, 37, 18, 47, 19, 63, 16, 69, 12), fill="#f3a9ee")
    d.line((51, 8, 48, 12, 46, 14), fill="#e69afb")
    d.line((29, 7, 31, 12, 36, 15), fill="#e69afb")
    for x, y in ((13, 30), (78, 22), (79, 59), (11, 62), (57, 82)):
        d.line((x-2, y, x+2, y), fill="#c77fe9")
        d.line((x, y-2, x, y+2), fill="#efb7ef")
    return sprite


def weapons():
    """Three right-facing weapon cel rows, with the grip at [18, 21]."""
    sheet = Image.new("RGBA", (80, 126))
    lavender, orchid, white = "#8f55bd", "#cc86e9", "#fff0f0"
    # Blade.
    blade = Image.new("RGBA", (80, 42))
    d = ImageDraw.Draw(blade)
    d.polygon([(7, 20), (11, 17), (22, 17), (19, 9), (25, 10), (30, 15),
               (56, 10), (65, 11), (79, 19), (66, 26), (29, 27), (25, 32),
               (18, 33), (21, 25), (10, 25)], fill=INK)
    d.polygon([(26, 17), (57, 12), (66, 13), (76, 19), (66, 24), (29, 25)], fill=lavender)
    d.polygon([(31, 17), (57, 12), (65, 13), (74, 18), (62, 17), (33, 21)], fill="#f1bded")
    d.line((40, 16, 56, 13, 64, 13, 71, 16), fill=white)
    d.line((26, 19, 31, 18, 37, 19, 34, 23, 29, 23), fill="#fdc78a")
    d.point((32, 20), fill=white)
    d.line((38, 24, 63, 22, 72, 20), fill="#6b3c9d")
    d.line((19, 12, 24, 13, 27, 19, 24, 28, 20, 31), fill=GOLD, width=2)
    d.line((10, 20, 22, 20), fill="#a16380", width=3)
    d.line((10, 19, 12, 19), fill=LIGHT_GOLD, width=3)
    sheet.alpha_composite(blade, (0, 0))

    bow = Image.new("RGBA", (80, 42))
    d = ImageDraw.Draw(bow)
    d.line((39, 2, 21, 20, 38, 39), fill="#e0a8ef")
    d.line((39, 2, 34, 9, 44, 15, 47, 21, 43, 27, 34, 32, 38, 39),
           fill=INK, width=6)
    d.line((39, 2, 35, 9, 44, 15, 47, 21, 43, 27, 35, 32, 38, 39),
           fill=lavender, width=4)
    d.line((39, 3, 36, 8, 41, 12, 46, 17, 47, 21, 44, 26, 36, 33, 38, 37),
           fill=GOLD, width=2)
    d.polygon([(39, 0), (42, 3), (39, 7), (36, 4)], fill=LIGHT_GOLD)
    d.polygon([(38, 35), (41, 39), (38, 41), (35, 38)], fill=LIGHT_GOLD)
    d.polygon([(47, 17), (51, 21), (47, 25), (43, 21)], fill=orchid)
    d.point((47, 20), fill=white)
    sheet.alpha_composite(bow, (0, 42))

    cannon = Image.new("RGBA", (80, 42))
    d = ImageDraw.Draw(cannon)
    d.polygon([(15, 13), (24, 10), (37, 10), (37, 6), (42, 5), (47, 9), (61, 8),
               (66, 4), (73, 5), (79, 10), (79, 30), (72, 36), (65, 36), (61, 31),
               (45, 31), (40, 36), (35, 34), (33, 28), (22, 28), (15, 24)], fill=INK)
    d.polygon([(17, 15), (24, 12), (62, 10), (67, 6), (73, 7), (77, 12), (77, 29),
               (71, 34), (66, 34), (62, 29), (24, 26), (17, 23)], fill="#62407e")
    d.polygon([(23, 14), (59, 12), (63, 15), (59, 18), (24, 19)], fill=lavender)
    d.line((24, 14, 60, 12), fill=orchid, width=2)
    for x in (31, 45, 62):
        d.line((x, 10, x + 2, 14, x + 2, 26, x, 30), fill=GOLD, width=2)
        d.point((x + 1, 13), fill=LIGHT_GOLD)
    d.ellipse((66, 8, 77, 32), fill=lavender, outline=LIGHT_GOLD, width=2)
    d.ellipse((69, 12, 76, 28), fill="#301d48", outline=orchid)
    d.line((73, 15, 73, 25), fill="#ffbafb", width=2)
    d.point((73, 19), fill=white)
    sheet.alpha_composite(cannon, (0, 84))
    return sheet


def imp():
    sprite = Image.new("RGBA", (32, 36))
    d = ImageDraw.Draw(sprite)
    d.polygon([(9, 20), (22, 20), (26, 29), (24, 34), (20, 34), (17, 30), (13, 30),
               (10, 34), (6, 34), (5, 29)], fill=INK)
    d.polygon([(10, 22), (21, 22), (23, 28), (19, 29), (14, 27), (8, 30)], fill="#805069")
    d.polygon([(8, 10), (11, 6), (14, 5), (14, 1), (18, 4), (20, 5), (25, 2),
               (24, 9), (27, 13), (26, 20), (21, 24), (11, 23), (5, 19), (5, 13)], fill=INK)
    d.polygon([(9, 11), (13, 7), (21, 7), (25, 12), (24, 18), (20, 21), (12, 21),
               (7, 17), (7, 13)], fill="#553651")
    d.line((9, 12, 13, 8, 21, 8, 24, 12), fill="#926278")
    d.polygon([(11, 14), (15, 13), (21, 13), (23, 17), (19, 21), (13, 21), (9, 18)], fill="#d4aa9d")
    d.line((11, 16, 14, 17), fill="#39203b", width=2)
    d.line((18, 17, 21, 16), fill="#39203b", width=2)
    d.point((13, 16), fill="#ff996e")
    d.point((20, 16), fill="#ff996e")
    d.line((20, 29, 29, 20), fill="#80526f", width=2)
    d.line((23, 26, 30, 20), fill="#e5b58c")
    return sprite


def weapon_spirit():
    sprite = Image.new("RGBA", (59, 45))
    d = ImageDraw.Draw(sprite)
    p = d.polygon
    p([(47, 14), (55, 16), (58, 22), (53, 26), (45, 25), (39, 33), (32, 37),
       (21, 35), (12, 37), (9, 41), (12, 44), (5, 42), (4, 37), (8, 31),
       (18, 29), (11, 26), (3, 27), (0, 23), (7, 24), (15, 21), (22, 23),
       (25, 16), (32, 13), (38, 15)], fill="#4f286d")
    p([(49, 16), (54, 18), (55, 22), (51, 24), (44, 23), (38, 30), (31, 34),
       (22, 32), (13, 34), (8, 39), (7, 36), (10, 32), (18, 30), (22, 28),
       (15, 24), (7, 26), (5, 25), (15, 23), (23, 25), (27, 17), (33, 15),
       (38, 17)], fill="#a255d3")
    p([(23, 27), (28, 25), (31, 28), (39, 25), (43, 20), (51, 17), (54, 20),
       (50, 20), (42, 23), (36, 30), (29, 32)], fill="#db8ef5")
    p([(30, 17), (28, 10), (31, 4), (34, 12), (38, 14), (45, 10),
       (48, 5), (49, 11), (46, 17), (48, 23), (42, 28), (35, 27), (30, 24)], fill="#6f37a0")
    p([(31, 8), (33, 13), (36, 15), (42, 14), (47, 9), (46, 14), (43, 19),
       (36, 19), (32, 17)], fill="#d689ee")
    p([(34, 19), (39, 18), (44, 18), (45, 23), (40, 27), (35, 24)], fill="#36204f")
    p([(37, 21), (41, 20), (43, 20), (41, 23), (38, 23)], fill="#ffe9ed")
    d.point((54, 13), fill="#ecb9f7")
    d.point((16, 38), fill="#cf82ec")
    return sprite


def paint_sprites():
    sheet = Image.new("RGBA", (160, 132))
    for row in range(3):
        for col in range(4):
            sheet.alpha_composite(waltz(row, col), (40 * col, 44 * row))
    sheet.save(OUT / "waltz.png")
    requiem().save(OUT / "requiem.png")
    weapon_spirit().save(OUT / "weapon_spirit.png")
    weapons().save(OUT / "weapons.png")
    imp().save(OUT / "imp.png")


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
    image.save(OUT / "chamber.png")


if __name__ == "__main__":
    paint_sprites()
    chamber()

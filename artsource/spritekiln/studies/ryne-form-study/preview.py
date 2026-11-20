"""Review sheets and timed previews. All pixel art is displayed at integer scale."""

from bisect import bisect_right
from itertools import accumulate
from pathlib import Path
import json

from PIL import Image, ImageDraw, ImageFont
import numpy as np


ROOT = Path(__file__).resolve().parent
PAPER = (22, 20, 32)
WHITE = (247, 232, 228)
MUTED = (180, 162, 178)
PINK = (249, 150, 186)
RULE = (75, 60, 80)
NEAREST = Image.Resampling.NEAREST
LABELS = {
    "idle": "대기", "run": "달리기", "jump": "점프", "slash": "에너지 참격",
    "wave": "손 흔들기", "interact": "상호작용", "transform": "변신",
    "launch": "비행 진입", "run_start": "달리기 시작", "run_stop": "감속", "hover": "호버 이동", "air_turn": "공중 방향 전환",
}


def font(size, latin=False, bold=False):
    win = Path("C:/Windows/Fonts")
    candidates = ([win / ("georgiai.ttf" if latin else "malgunbd.ttf" if bold else "malgun.ttf"),
                   Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
                   Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")])
    return next((ImageFont.truetype(str(path), size) for path in candidates if path.exists()),
                ImageFont.load_default())


def label(draw, xy, value, size, color=WHITE, bold=False, latin=False, anchor="la"):
    draw.text(xy, value, fill=color, font=font(size, latin, bold), anchor=anchor)


def load_track(group):
    path = ROOT / "atlases" / f"ryne_{group}.json"
    meta = json.loads(path.read_text(encoding="utf-8"))
    with Image.open(path.parent / meta["meta"]["image"]) as source:
        px = meta["spritekiln"]["pivot"]
        result = dict(pivot=(round(px["x"]), round(px["y"])))
        for name, clip in meta["spritekiln"]["animations"].items():
            for direction, entry in clip["directions"].items():
                frames = []
                for key in entry["frames"]:
                    r = meta["frames"][key]["frame"]
                    frames.append(source.crop((r["x"], r["y"], r["x"] + r["w"], r["y"] + r["h"])))
                result[name, direction] = (frames, entry["durations"])
        return result


def sprite(canvas, frame, x, baseline, pivot, scale):
    x -= pivot[0] * scale
    baseline -= pivot[1] * scale
    art = frame.resize((frame.width * scale, frame.height * scale), NEAREST) if scale > 1 else frame
    canvas.paste(art, (int(x), int(baseline)), art)


def board(base, form):
    canvas = Image.new("RGB", (1120, 856), PAPER)
    draw = ImageDraw.Draw(canvas)
    label(draw, (36, 18), "리네", 42, bold=True)
    label(draw, (147, 27), "Ryne", 33, PINK, latin=True)
    label(draw, (1084, 43), "SpriteKiln   /   캐릭터 스터디", 16, MUTED, anchor="rm")
    draw.line((36, 90, 1084, 90), fill=RULE)
    heroes = [(base, "idle", 0, "기본형", "Base form", (42, 35, 48), (51, 42, 56)),
              (form, "transform", -1, "변신형", "Awakened form", (45, 30, 51), (62, 39, 62))]
    for i, (track, clip, idx, title, sub, bottom, top) in enumerate(heroes):
        x, y, w, h = 36 + i * 531, 111, 517, 326
        for j in range(h):
            t = j / h
            c = tuple(round(a + (b-a)*t) for a,b in zip(top, bottom))
            draw.line((x, y+j, x+w-1, y+j), fill=c)
        draw.line((x, y, x+w-1, y), fill=(114, 83, 104))
        draw.line((x+22, y+h-25, x+w-22, y+h-25), fill=RULE)
        label(draw, (x+23, y+17), sub, 19, PINK, latin=True)
        label(draw, (x+22, y+46), title, 29, bold=True)
        frame = track[clip, "e"][0][idx]
        sprite(canvas, frame, x+95, y+h-25, track["pivot"], 1)
        label(draw, (x+24, y+h-29), "1×", 14, MUTED, anchor="ls")
        sprite(canvas, frame, x+338, y+h-25, track["pivot"], 4)

    label(draw, (36, 449), "기본 동작", 20, bold=True)
    ground = [("idle", 0), ("run", 0.18), ("jump", 0.48), ("slash", 0.53),
              ("wave", 0.5), ("interact", 0.55)]
    for k, (name, phase) in enumerate(ground):
        x = 36 + k * 177
        seq = base[name, "e"][0]
        frame = seq[round(phase * (len(seq)-1))]
        sprite(canvas, frame, x+90, 625, base["pivot"], 2)
        label(draw, (x+84, 644), LABELS[name], 15, MUTED, anchor="ma")
    draw.line((36, 685, 1084, 685), fill=RULE)
    label(draw, (36, 700), "폼 체인지", 20, bold=True)
    label(draw, (1084, 713), "28 프레임", 15, MUTED, anchor="rm")
    for k, idx in enumerate([0, 4, 7, 9, 13, 16, 21, 27]):
        x = 98 + k * 132
        frame = form["transform", "e"][0][idx]
        sprite(canvas, frame, x, 810, form["pivot"], 1)
        label(draw, (x, 821), str(idx+1).zfill(2), 13, MUTED, anchor="ma")
    canvas.save(ROOT / "ryne.png")


def form_sheet(track):
    canvas = Image.new("RGB", (1136, 855), PAPER)
    draw = ImageDraw.Draw(canvas)
    label(draw, (30, 18), "폼 체인지", 32, bold=True)
    label(draw, (1104, 44), "변신 28   /   호버 8   /   방향 전환 16", 16, MUTED, anchor="rm")
    rows = [("transform", range(0, 7)), ("transform", range(7, 14)),
            ("transform", range(14, 21)), ("transform", range(21, 28)),
            ("hover", range(8)), ("air_turn", range(8)), ("air_turn", range(8, 16))]
    for k, (name, indices) in enumerate(rows):
        y = 81 + k * 109
        draw.line((30,y,1105,y), fill=RULE)
        label(draw, (30, y+27), LABELS[name], 17, bold=True)
        label(draw, (30, y+57), f"{indices[0]+1:02d} – {indices[-1]+1:02d}", 15, PINK)
        for j, idx in enumerate(indices):
            x = 213 + j * 119
            sprite(canvas, track[name,"e"][0][idx], x, y+87, track["pivot"], 1)
            label(draw, (x, y+90), str(idx+1).zfill(2), 12, MUTED, anchor="ma")
    canvas.save(ROOT / "form-sheet.png")


def film(track, playlist, output):
    # The deck keeps one fixed pixel origin, even when Ryne lifts from the ground.
    frames, durations = [], []
    for clip, direction in playlist:
        src, ms = track[clip, direction]
        stage = Image.new("RGB", (512, 450), PAPER)
        draw = ImageDraw.Draw(stage)
        draw.line((28, 53, 484, 53), fill=RULE)
        draw.line((28, 405, 484, 405), fill=RULE)
        label(draw, (28, 12), "Ryne", 24, PINK, latin=True)
        label(draw, (484, 24), LABELS[clip], 17, WHITE, anchor="rm")
        label(draw, (28, 417), "SPRITEKILN", 13, MUTED)
        for i, frame in enumerate(src):
            show = stage.copy()
            sprite(show, frame, 263, 378, track["pivot"], 4)
            mark = ImageDraw.Draw(show)
            label(mark, (484, 426), f"{i+1:02d} / {len(src):02d}", 14, MUTED, anchor="rm")
            frames.append(show)
        durations.extend(ms)
    # GIF supports 10 ms ticks. Error diffusion keeps the total playback time accurate.
    ticks, elapsed, written = [], 0, 0
    for duration in durations:
        elapsed += duration
        new = round(elapsed / 10) * 10
        ticks.append(new - written)
        written = new
    frames[0].save(ROOT / output, save_all=True, append_images=frames[1:], duration=ticks,
                   loop=0, optimize=True, disposal=1)


def reference_comparison(base, form):
    attachments = ROOT.parents[3] / ".codex-attachments"
    refs = [
        (next(attachments.rglob("501.png"), None), (33, 8, 96, 95), base["idle", "e"][0][0], "기본형"),
        (next(attachments.rglob("503.png"), None), (1152, 311, 1253, 410), form["transform", "e"][0][-1], "변신형"),
    ]
    if any(path is None for path, *_ in refs):
        return
    canvas = Image.new("RGB", (824, 628), PAPER)
    draw = ImageDraw.Draw(canvas)
    label(draw, (28, 19), "리네", 29, bold=True)
    label(draw, (225, 32), "첨부 시안", 18, MUTED, anchor="mm")
    label(draw, (594, 32), "SpriteKiln", 21, PINK, latin=True, anchor="mm")
    for i, (path, box, model, title) in enumerate(refs):
        y = 67 + i*276
        draw.line((27, y, 797, y), fill=RULE)
        label(draw, (28, y+18), title, 17, MUTED)
        with Image.open(path) as sheet:
            ref = sheet.crop(box).convert("RGBA")
        # Remove the sheet background only for measuring the reference's visible height.
        rgb = np.array(ref, dtype=int)[:, :, :3]
        background = np.median(rgb[:3, :4], axis=(0, 1))
        keep = np.max(abs(rgb - background), axis=2)
        bbox = Image.fromarray((keep > 40).astype("uint8")*255).getbbox()
        ref = ref.crop(bbox)
        art = model.crop(model.getchannel("A").getbbox())
        scale = max(1, min(4, 225 // art.height))
        h = art.height*scale
        w = round(ref.width*h/ref.height)
        ref = ref.resize((w, h), NEAREST)
        art = art.resize((art.width*scale, h), NEAREST)
        top = y + (272-h)//2
        # Display the supplied pixels with their original background tone.
        left = tuple(int(c) for c in background)
        draw.rectangle((102,y+7,348,y+266), fill=left)
        canvas.paste(ref,(225-w//2,top))
        canvas.paste(art,(595-art.width//2,top),art)
    canvas.save(ROOT/"reference-comparison.png")


def run_comparison(track):
    """Both runners use their own frame timing and measured ground speed."""
    with Image.open(ROOT / "comparison" / "previous-run.png") as source:
        previous = [source.crop((x, 0, x + 96, 96)) for x in range(0, source.width, 96)]
        old_ms = json.loads(source.info["timing"])
        old_pivot = json.loads(source.info["pivot"])
        old_speed = float(source.info["ground_speed"])
    current, new_ms = track["run", "e"]
    qa = json.loads((ROOT / "atlases" / "ryne_base_qa.json").read_text(encoding="utf-8"))
    new_speed = qa["info"]["ground_speed"]["run"]["px_per_s"]
    lanes = [(previous, list(accumulate(old_ms)), (round(old_pivot["x"]), round(old_pivot["y"])), old_speed),
             (current, list(accumulate(new_ms)), track["pivot"], new_speed)]
    template = Image.new("RGB", (760, 306), PAPER)
    draw = ImageDraw.Draw(template)
    for x, title in [(16, "이전 달리기"), (388, "수정한 달리기")]:
        draw.rectangle((x, 14, x+355, 288), fill=(42, 35, 49))
        label(draw, (x+16, 22), title, 18, WHITE, bold=True)
        draw.line((x+12, 252, x+343, 252), fill=(103, 82, 101))
    frames = []
    length = 4800
    for elapsed in range(0, length, 20):
        page = template.copy()
        pen = ImageDraw.Draw(page)
        for j, (seq, times, pivot, speed) in enumerate(lanes):
            x = 16 + j * 372
            distance = speed * length / 1000
            pitch = distance / round(distance / 22)
            phase = (elapsed * speed / 1000) % pitch
            for tile in range(-1, 9):
                marker = x + round((tile * pitch - phase) * 3)
                if x+13 <= marker <= x+337:
                    pen.line((marker,253,marker-3,258), fill=(96, 74, 93), width=2)
            idx = bisect_right(times, elapsed % times[-1])
            sprite(page, seq[idx], x+194, 252, pivot, 3)
        frames.append(page)
    frames[0].save(ROOT / "run-comparison.gif", save_all=True, append_images=frames[1:],
                   duration=20, loop=0, optimize=True, disposal=1)


def make_previews():
    base, form = load_track("base"), load_track("awakened")
    run_comparison(base)
    board(base, form)
    form_sheet(form)
    reference_comparison(base, form)
    film(base, [(n, "e") for n in ("idle", "run_start", "run", "run", "run_stop", "jump", "slash", "wave", "interact")],
         "base-actions.gif")
    film(form, [("transform", "e"), ("launch", "e"), ("hover", "e"), ("air_turn", "e"), ("hover", "w")],
         "form-change.gif")


if __name__ == "__main__":
    make_previews()

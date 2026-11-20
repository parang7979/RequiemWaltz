"""Extract the Godot preview's 56px front, half-turn and travel toe artwork."""
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
SOURCE = HERE/"pixelated-56"
DEST = HERE/"toe-study"
TOE = (25,54,33,58)


def main():
    idle = Image.open(SOURCE/"idle-sheet.png").convert("RGBA").crop((0,0,64,64))
    # The old slash starts with a flat, travel-facing right boot. Its cell has
    # sixteen extra pixels on either side of the same character registration.
    slash = Image.open(SOURCE/"slash-sheet.png").convert("RGBA").crop((16,0,80,64))
    front = idle.crop(TOE)
    travel = slash.crop(TOE)
    half = Image.new("RGBA",front.size)
    for y in range(front.height):
        box = (0,y,front.width,y+1)
        rows = [im.crop(box) for im in (front,travel)]
        bounds = [im.getchannel("A").getbbox() for im in rows]
        left,right = [round((bounds[0][i]+bounds[1][i])/2) for i in (0,2)]
        aligned = [im.crop(b).convert("RGBa").resize((right-left,1),Image.Resampling.BOX)
                   for im,b in zip(rows,bounds)]
        half.paste(Image.blend(*aligned,.5).convert("RGBA"),(left,y))
    # Reveal one new silhouette pixel at half-turn, two at full turn.
    half.putpixel((7,3),(0,0,0,0))
    atlas = Image.new("RGBA",(front.width*3,front.height))
    body = idle.copy()
    body.paste((0,0,0,0),TOE)
    for i,patch in enumerate((front,half,travel)):
        atlas.paste(patch,(i*front.width,0))
        check = body.copy()
        check.paste(patch,TOE[:2])
        assert check.crop((0,58,64,64)).tobytes()==idle.crop((0,58,64,64)).tobytes()
        if i==0:
            assert np.array_equal(check,idle)
    DEST.mkdir(parents=True,exist_ok=True)
    atlas.save(DEST/"right_toes.png")
    body.save(DEST/"idle_body.png")


if __name__=="__main__":
    main()

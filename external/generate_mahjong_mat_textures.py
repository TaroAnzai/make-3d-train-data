"""Create flat, subtly textured teal material maps for build_mahjong_mat.py."""

from pathlib import Path
import random

from PIL import Image, ImageDraw, ImageFilter


OUT = Path(__file__).resolve().parent.parent / "output" / "table_assets" / "textures"
OUT.mkdir(parents=True, exist_ok=True)


def fabric_texture(path, base, seed, fibers=False):
    rng = random.Random(seed)
    n = 1024
    noise = Image.effect_noise((n, n), 24).convert("L")
    broad = noise.filter(ImageFilter.GaussianBlur(14))
    fine = noise.load()
    broad_px = broad.load()
    img = Image.new("RGB", (n, n))
    px = img.load()
    for y in range(n):
        for x in range(n):
            d = (fine[x, y] - 128) * (0.10 if fibers else 0.07)
            d += (broad_px[x, y] - 128) * 0.22
            px[x, y] = tuple(max(0, min(255, round(c + d))) for c in base)
    draw = ImageDraw.Draw(img, "RGBA")
    if fibers:
        for _ in range(46000):
            x, y = rng.randrange(n), rng.randrange(n)
            length = rng.choice((1, 2, 2, 3, 4))
            shade = rng.choice((0, 255))
            draw.line((x, y, x + length, y + rng.choice((0, 1))),
                      fill=(shade, shade, shade, rng.randrange(5, 17)), width=1)
    else:
        for _ in range(1500):
            x, y = rng.randrange(n), rng.randrange(n)
            draw.line((x, y, x + rng.randrange(4, 22), y),
                      fill=(255, 255, 255, rng.randrange(2, 8)), width=1)
    img.save(path, optimize=True)


fabric_texture(OUT / "felt_teal.png", (13, 105, 105), 6923, fibers=True)
fabric_texture(OUT / "rubber_teal.png", (11, 139, 148), 2309)

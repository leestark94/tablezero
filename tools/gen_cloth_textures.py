"""Procedural, tileable cloth textures for 이서연 (no external assets, no credits).

  python tools/gen_cloth_textures.py [out_dir]

Writes (default blender/out/seoyeon/textures):
  seoyeon_knit_diffuse.png / seoyeon_knit_normal.png    brown chunky cable knit (approved reference look)
  seoyeon_trousers_diffuse.png / seoyeon_trousers_normal.png   dark charcoal wool twill
Everything is built from periodic functions on a 1024 px tile, so the maps repeat seamlessly.
"""
import os, sys
import numpy as np
from PIL import Image

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, 'blender', 'out', 'seoyeon', 'textures')
N = 1024
rng = np.random.default_rng(302)


def tile_noise(n, cells, octaves=4, seed=0):
    """Tileable value noise (sum of octaves of bilinearly upsampled periodic random grids)."""
    r = np.random.default_rng(seed); acc = np.zeros((n, n)); amp = 1.0; tot = 0.0
    for o in range(octaves):
        c = cells * (2 ** o)
        g = r.random((c, c))
        y = np.arange(n) * c / n; x = y
        y0 = np.floor(y).astype(int); x0 = y0; fy = y - y0; fx = fy
        fy = fy * fy * (3 - 2 * fy); fx = fy
        y1 = (y0 + 1) % c; x1 = y1
        a = g[np.ix_(y0, x0)]; b = g[np.ix_(y0, x1)]; cc = g[np.ix_(y1, x0)]; d = g[np.ix_(y1, x1)]
        top = a + (b - a) * fx[None, :]; bot = cc + (d - cc) * fx[None, :]
        acc += amp * (top + (bot - top) * fy[:, None]); tot += amp; amp *= 0.5
    return acc / tot


def normal_from_height(h, strength):
    dx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5 * strength
    dy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5 * strength
    nz = np.ones_like(h); l = np.sqrt(dx * dx + dy * dy + nz * nz)
    # OpenGL convention (Unity): +Y up in tangent space; image rows go down, so invert dy
    n = np.stack([-dx / l, dy / l, nz / l], -1)
    return Image.fromarray(((n * 0.5 + 0.5) * 255).clip(0, 255).astype(np.uint8))


def save(img, name):
    os.makedirs(OUT, exist_ok=True); p = os.path.join(OUT, name); img.save(p); print('WROTE', p)


def knit():
    y, x = np.mgrid[0:N, 0:N].astype(float)
    # layout per 256 px horizontal repeat (4 repeats per tile): purl gutter | rib | cable (112) | rib | purl gutter
    P = 256.0; u = x % P
    # --- stockinette stitch field: V-shaped loops, 16 px wide columns x 12 px rows
    sw, sh = 16.0, 12.0
    cu = (x % sw) / sw - 0.5; cv = (y % sh) / sh
    left = np.exp(-(((cu + 0.22) + (cv - 0.5) * 0.55) ** 2) / 0.018 - ((cv - 0.5) ** 2) / 0.22)
    right = np.exp(-(((cu - 0.22) - (cv - 0.5) * 0.55) ** 2) / 0.018 - ((cv - 0.5) ** 2) / 0.22)
    stitch = np.maximum(left, right)
    # --- purl (reverse stockinette): horizontal bumpy ridges
    purl = 0.55 + 0.45 * np.cos(2 * np.pi * y / 8.0) * (0.6 + 0.4 * np.cos(2 * np.pi * (x + (y // 8) * 5) / 10.0))
    # --- cable: two ropes crossing every 96 px, inside u in [72,184]
    cx0, cw, period = 128.0, 112.0, 96.0
    phase = 2 * np.pi * y / period
    off = 0.27 * cw * np.sin(phase)
    d1 = np.abs(u - (cx0 + off)); d2 = np.abs(u - (cx0 - off))
    rope_w = 22.0
    r1 = np.clip(1 - (d1 / rope_w) ** 2, 0, None); r2 = np.clip(1 - (d2 / rope_w) ** 2, 0, None)
    # rope cable: at every crossing the strand travelling left is on top -> order flips half-way between crossings
    front_is_1 = (np.floor((y + period / 4) / (period / 2)) % 2 == 1)
    # cable crossing: the strand in front fully occludes the one behind (with a groove at its edge)
    fr = np.where(front_is_1, r1, r2); bk = np.where(front_is_1, r2, r1)
    rope = np.where(fr > 0.04, np.sqrt(fr), np.sqrt(bk) * 0.7)
    # yarn twist along each strand: diagonal ridges that read as plied stitches
    twist = 0.5 + 0.5 * np.cos(2 * np.pi * (u * 0.9 + y * np.where(front_is_1, 1.0, -1.0)) / 11.0)
    rope = rope * (0.82 + 0.18 * twist)
    # stitches follow the rope direction a little (shifted field)
    stitch_r = np.maximum(
        np.exp(-((((u - cx0 - off) % sw) / sw - 0.5 + 0.22) + (cv - 0.5) * 0.55) ** 2 / 0.018 - ((cv - 0.5) ** 2) / 0.22),
        np.exp(-((((u - cx0 - off) % sw) / sw - 0.5 - 0.22) - (cv - 0.5) * 0.55) ** 2 / 0.018 - ((cv - 0.5) ** 2) / 0.22))
    in_cable = (u > cx0 - cw / 2) & (u < cx0 + cw / 2)
    cable_h = np.where(rope > 0.02, 0.45 + 0.55 * rope * (0.75 + 0.25 * stitch_r), 0.18 * purl)
    # --- ribs (2 stitch columns, raised) either side of the cable
    rib = ((u > 40) & (u < 66)) | ((u > 190) & (u < 216))
    h = np.where(in_cable, cable_h, np.where(rib, 0.55 + 0.4 * stitch, 0.22 + 0.25 * purl))
    fuzz = tile_noise(N, 64, 3, 1); yarn = tile_noise(N, 8, 4, 2)
    h = h + 0.06 * fuzz
    # diffuse: warm brown yarn, heather variation, cavities darker (AO from height), slight fuzz highlights
    base = np.array([0.30, 0.20, 0.14])
    heather = 0.85 + 0.3 * (yarn - 0.5) + 0.18 * (tile_noise(N, 256, 1, 3) - 0.5)
    ao = 0.18 + 0.82 * np.clip(h, 0, 1) ** 1.3
    col = base[None, None, :] * (heather * ao)[..., None]
    col = np.clip(col, 0, 1) ** (1 / 2.2) * 255  # stored as sRGB
    save(Image.fromarray(col.astype(np.uint8)), 'seoyeon_knit_diffuse.png')
    save(normal_from_height(h, 9.0), 'seoyeon_knit_normal.png')


def trousers():
    y, x = np.mgrid[0:N, 0:N].astype(float)
    tw = 0.5 + 0.5 * np.cos(2 * np.pi * (x + y) / 6.0)                 # 2/2 twill diagonal
    weft = 0.5 + 0.5 * np.cos(2 * np.pi * y / 3.0)
    n1 = tile_noise(N, 32, 4, 11); n2 = tile_noise(N, 512, 1, 12)
    h = 0.55 * tw + 0.15 * weft + 0.2 * n1 + 0.1 * n2
    base = np.array([0.075, 0.075, 0.085])
    shade = 0.82 + 0.25 * (h - 0.5) + 0.12 * (n1 - 0.5)
    col = np.clip(base[None, None, :] * shade[..., None], 0, 1) ** (1 / 2.2) * 255
    save(Image.fromarray(col.astype(np.uint8)), 'seoyeon_trousers_diffuse.png')
    save(normal_from_height(h, 2.2), 'seoyeon_trousers_normal.png')


def hair_strands():
    """RGBA hair-card texture (512x1024): many fine dark strands, alpha tapers to wisps at the tip (v = bottom)."""
    W, H = 512, 1024
    y, x = np.mgrid[0:H, 0:W].astype(float)
    t = y / (H - 1)                                    # 0 = root, 1 = tip
    alpha = np.zeros((H, W)); shade = np.zeros((H, W))
    r = np.random.default_rng(7)
    for _ in range(260):
        x0 = r.uniform(0, W); amp = r.uniform(2, 14); fq = r.uniform(0.5, 2.0); ph = r.uniform(0, 6.28)
        length = r.uniform(0.55, 1.0); wdt = r.uniform(0.8, 2.2); val = r.uniform(0.6, 1.0)
        cx = x0 + amp * np.sin(2 * np.pi * fq * t + ph) + 18 * t * r.uniform(-1, 1)
        d = np.abs(((x - cx + W / 2) % W) - W / 2)
        a = np.clip(1 - d / wdt, 0, 1) * np.clip((length - t) / 0.12, 0, 1)
        alpha = np.maximum(alpha, a); shade = np.maximum(shade, a * val)
    root = np.clip(1 - t / 0.05, 0, 1)                 # dense at the root so cards join the scalp
    alpha = np.clip(alpha * (1.15 - 0.35 * t) + 0.5 * root, 0, 1)
    base = np.array([0.050, 0.038, 0.032])             # near-black brown (approved profile)
    col = base[None, None, :] * (0.7 + 0.9 * shade)[..., None]
    col = np.clip(col, 0, 1) ** (1 / 2.2) * 255
    rgba = np.dstack([col, alpha * 255]).astype(np.uint8)
    save(Image.fromarray(rgba, 'RGBA'), 'seoyeon_fringe_diffuse.png')


if __name__ == '__main__':
    knit(); trousers(); hair_strands()

"""Shared utilities for playlist cover generation and upload."""

import io
import base64
import math
import requests
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SIZE = 640


def lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def gradient_bg(draw, w, h, top, bottom, diagonal=False):
    for y in range(h):
        t = y / h
        if diagonal:
            for x in range(w):
                c = lerp_color(top, bottom, (t + x / w) / 2)
                draw.point((x, y), fill=c)
        else:
            draw.line([(0, y), (w, y)], fill=lerp_color(top, bottom, t))


def upload_cover(sp, playlist_id: str, img: Image.Image) -> int:
    """Upload a PIL image as the cover for a Spotify playlist.

    Tries decreasing JPEG quality until the base64-encoded payload fits
    within Spotify's 256 KB limit.

    Returns the HTTP status code (200/202/204 = success).
    """
    b64 = None
    quality_used = 80
    for quality in (80, 65, 50, 35):
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        b64 = base64.b64encode(buf.getvalue())
        quality_used = quality
        if len(b64) <= 256 * 1024:
            break

    print(f"    {len(b64) // 1024}KB (q={quality_used})", flush=True)
    token = sp.auth_manager.get_access_token(as_dict=False)
    r = requests.put(
        f"https://api.spotify.com/v1/playlists/{playlist_id}/images",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "image/jpeg"},
        data=b64,
    )
    return r.status_code


# ── Series 1 generators — genre-based playlists ──────────────────────────────

def make_rap(rng: np.random.Generator) -> Image.Image:
    """Urban concrete aesthetic: neon grids, spray blocks, hard geometry."""
    img = Image.new("RGB", (SIZE, SIZE))
    draw = ImageDraw.Draw(img)
    gradient_bg(draw, SIZE, SIZE, (10, 10, 14), (25, 5, 40))

    for x in range(0, SIZE, 38):
        a = rng.uniform(0.05, 0.25)
        draw.line([(x, 0), (x, SIZE)], fill=tuple(int(v * a) for v in (255, 210, 0)), width=1)
    for y in range(0, SIZE, 38):
        a = rng.uniform(0.03, 0.12)
        draw.line([(0, y), (SIZE, y)], fill=tuple(int(v * a) for v in (255, 210, 0)), width=1)

    for _ in range(6):
        x0 = rng.integers(0, SIZE - 150)
        y0 = rng.integers(0, SIZE - 150)
        w  = rng.integers(60, 200)
        h  = rng.integers(60, 200)
        hue = rng.choice(np.array([(255, 50, 0), (0, 220, 120), (180, 0, 255), (255, 200, 0)]))
        a = rng.uniform(0.04, 0.18)
        draw.rectangle([int(x0), int(y0), int(x0 + w), int(y0 + h)],
                       fill=tuple(int(v * a) for v in hue))

    draw.line([(0, SIZE), (SIZE, 0)], fill=(255, 190, 0), width=3)
    draw.line([(0, SIZE - 60), (SIZE, 60)], fill=(255, 80, 0), width=1)

    cx, cy, r = SIZE // 2, SIZE // 2, 110
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(255, 200, 0), width=3)
    draw.ellipse([cx - r + 12, cy - r + 12, cx + r - 12, cy + r - 12],
                 outline=(200, 60, 255), width=1)

    arr = np.array(img)
    noise = rng.integers(0, 12, arr.shape, dtype=np.uint8)
    return Image.fromarray(np.clip(arr.astype(np.int16) + noise, 0, 255).astype(np.uint8))


def make_mpb(rng: np.random.Generator) -> Image.Image:
    """Warm sepia, organic waves, vinyl texture."""
    img = Image.new("RGB", (SIZE, SIZE))
    draw = ImageDraw.Draw(img)
    gradient_bg(draw, SIZE, SIZE, (80, 45, 15), (180, 110, 40), diagonal=True)

    for i in range(20):
        y_base = int(SIZE * i / 20)
        pts = []
        for x in range(0, SIZE + 1, 8):
            amp  = rng.uniform(8, 28)
            freq = rng.uniform(0.008, 0.02)
            pts.append((x, y_base + int(amp * math.sin(freq * x + i))))
        a = rng.uniform(0.04, 0.14)
        if len(pts) >= 2:
            draw.line(pts, fill=tuple(int(v * a) for v in (255, 220, 140)), width=1)

    cx, cy = SIZE // 2, SIZE // 2
    for r in range(40, 280, 18):
        a = rng.uniform(0.06, 0.20)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                     outline=tuple(int(v * a) for v in (255, 240, 180)), width=1)

    draw.ellipse([cx - 18, cy - 18, cx + 18, cy + 18], fill=(60, 30, 10))
    draw.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=(100, 55, 20))

    img = img.filter(ImageFilter.GaussianBlur(0.8))
    arr = np.array(img)
    noise = rng.integers(0, 20, arr.shape, dtype=np.uint8)
    return Image.fromarray(np.clip(arr.astype(np.int16) + noise - 10, 0, 255).astype(np.uint8))


def make_rock(rng: np.random.Generator) -> Image.Image:
    """Post-punk haze, lightning bolts, near-monochromatic."""
    img = Image.new("RGB", (SIZE, SIZE))
    draw = ImageDraw.Draw(img)
    gradient_bg(draw, SIZE, SIZE, (8, 8, 12), (30, 18, 35))

    for _ in range(400):
        x = int(rng.integers(0, SIZE))
        y = int(rng.integers(0, SIZE))
        r = int(rng.integers(20, 90))
        hue = rng.choice(np.array([(140, 0, 180), (60, 0, 120), (200, 200, 220)]))
        a = rng.uniform(0.01, 0.06)
        draw.ellipse([x - r, y - r, x + r, y + r], fill=tuple(int(v * a) for v in hue))

    for start_x in (SIZE // 2, SIZE // 3):
        lx, ly = start_x, 0
        pts = [(lx, ly)]
        while ly < SIZE:
            lx += int(rng.integers(-40, 40))
            ly += int(rng.integers(30, 70))
            pts.append((lx, min(ly, SIZE)))
        if len(pts) >= 2:
            draw.line(pts, fill=(200, 180, 255) if start_x == SIZE // 2 else (100, 80, 160),
                      width=2 if start_x == SIZE // 2 else 1)
        if start_x == SIZE // 2 and len(pts) >= 2:
            draw.line(pts, fill=(255, 255, 255), width=1)

    img = img.filter(ImageFilter.GaussianBlur(1.2))
    arr = np.array(img)
    noise = rng.integers(0, 8, arr.shape, dtype=np.uint8)
    return Image.fromarray(np.clip(arr.astype(np.int16) + noise, 0, 255).astype(np.uint8))


def make_jazz(rng: np.random.Generator) -> Image.Image:
    """Deep blue, club spotlights, floating particles."""
    img = Image.new("RGB", (SIZE, SIZE))
    draw = ImageDraw.Draw(img)
    gradient_bg(draw, SIZE, SIZE, (5, 15, 45), (20, 5, 60))

    cx = SIZE // 2
    for _ in range(12):
        angle = rng.uniform(-0.5, 0.5)
        x_end = int(cx + SIZE * math.sin(angle))
        hue = rng.choice(np.array([(30, 80, 200), (60, 10, 140), (10, 100, 180), (80, 40, 200)]))
        a = rng.uniform(0.04, 0.12)
        draw.polygon([(cx - 8, 0), (cx + 8, 0), (x_end + 60, SIZE), (x_end - 60, SIZE)],
                     fill=tuple(int(v * a) for v in hue))

    for _ in range(60):
        x = int(rng.integers(0, SIZE))
        y = int(rng.integers(0, SIZE))
        r = int(rng.integers(1, 5))
        a = rng.uniform(0.3, 0.9)
        draw.ellipse([x - r, y - r, x + r, y + r],
                     fill=tuple(int(v * a) for v in (120, 180, 255)))

    for r in range(120, 280, 22):
        start = int(rng.integers(180, 220))
        end   = int(rng.integers(300, 360))
        a = rng.uniform(0.08, 0.22)
        draw.arc([SIZE // 2 - r, SIZE // 2 - r, SIZE // 2 + r, SIZE // 2 + r],
                 start=start, end=end,
                 fill=tuple(int(v * a) for v in (100, 160, 255)), width=3)

    img = img.filter(ImageFilter.GaussianBlur(1.5))
    arr = np.array(img)
    noise = rng.integers(0, 6, arr.shape, dtype=np.uint8)
    return Image.fromarray(np.clip(arr.astype(np.int16) + noise, 0, 255).astype(np.uint8))


def make_folk(rng: np.random.Generator) -> Image.Image:
    """Watercolor, morning mist, tree silhouettes."""
    img = Image.new("RGB", (SIZE, SIZE))
    draw = ImageDraw.Draw(img)
    gradient_bg(draw, SIZE, SIZE, (210, 215, 200), (140, 155, 140))

    for _ in range(300):
        x = int(rng.integers(0, SIZE))
        y = int(rng.integers(0, SIZE))
        r = int(rng.integers(30, 120))
        a = rng.uniform(0.01, 0.05)
        draw.ellipse([x - r, y - r, x + r, y + r],
                     fill=tuple(int(v * a) for v in (240, 240, 235)))

    for _ in range(5):
        tx = int(rng.integers(60, SIZE - 60))
        th = int(rng.integers(120, 240))
        tw = int(rng.integers(2, 5))
        a  = rng.uniform(0.15, 0.35)
        tc = tuple(int(v * a) for v in (50, 60, 45))
        draw.rectangle([tx - tw, SIZE - th, tx + tw, SIZE], fill=tc)
        for _ in range(int(rng.integers(3, 8))):
            bx = tx + int(rng.integers(-50, 50))
            by = SIZE - th + int(rng.integers(0, th // 2))
            draw.line([(tx, by), (bx, by - int(rng.integers(10, 40)))],
                      fill=tc, width=max(1, tw - 1))

    sx, sy = int(rng.integers(150, SIZE - 150)), int(rng.integers(60, 200))
    for r in range(60, 0, -5):
        a = (60 - r) / 60 * 0.06
        draw.ellipse([sx - r, sy - r, sx + r, sy + r],
                     fill=tuple(int(v * a) for v in (255, 240, 180)))

    img = img.filter(ImageFilter.GaussianBlur(2.0))
    arr = np.array(img)
    noise = rng.integers(0, 15, arr.shape, dtype=np.uint8)
    return Image.fromarray(np.clip(arr.astype(np.int16) + noise - 7, 0, 255).astype(np.uint8))


# ── Series 2 generators — mood-based playlists ───────────────────────────────

def make_concentracao(rng: np.random.Generator) -> Image.Image:
    """Minimalist circuit board, dark teal, fine grid."""
    img = Image.new("RGB", (SIZE, SIZE))
    draw = ImageDraw.Draw(img)
    gradient_bg(draw, SIZE, SIZE, (4, 12, 20), (8, 25, 40))

    step = 32
    for x in range(0, SIZE, step):
        a = rng.uniform(0.04, 0.12)
        draw.line([(x, 0), (x, SIZE)],
                  fill=tuple(int(v * a) for v in (0, 210, 180)), width=1)
    for y in range(0, SIZE, step):
        a = rng.uniform(0.03, 0.08)
        draw.line([(0, y), (SIZE, y)],
                  fill=tuple(int(v * a) for v in (0, 210, 180)), width=1)

    for _ in range(12):
        cx = int(rng.integers(0, SIZE // step) * step)
        cy = int(rng.integers(0, SIZE // step) * step)
        r  = int(rng.integers(3, 8))
        a  = rng.uniform(0.4, 0.9)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                     fill=tuple(int(v * a) for v in (0, 220, 190)))

    cx, cy = SIZE // 2, SIZE // 2
    for r in [60, 90, 130, 180]:
        a = 0.15 - r / 1800
        draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                     outline=tuple(int(v * a) for v in (0, 255, 210)), width=1)
    draw.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], fill=(0, 200, 170))

    arr = np.array(img)
    noise = rng.integers(0, 6, arr.shape, dtype=np.uint8)
    return Image.fromarray(np.clip(arr.astype(np.int16) + noise, 0, 255).astype(np.uint8))


def make_energia(rng: np.random.Generator) -> Image.Image:
    """Aggressive diagonals, red/orange, high contrast."""
    img = Image.new("RGB", (SIZE, SIZE))
    draw = ImageDraw.Draw(img)
    gradient_bg(draw, SIZE, SIZE, (12, 5, 3), (35, 8, 5))

    for i in range(0, SIZE + 200, 28):
        a = rng.uniform(0.06, 0.25)
        color = rng.choice(np.array([(255, 50, 0), (255, 150, 0), (200, 10, 0)]))
        w = int(rng.integers(1, 4))
        draw.line([(i, 0), (i - SIZE, SIZE)],
                  fill=tuple(int(v * a) for v in color), width=w)

    for _ in range(8):
        x0 = int(rng.integers(0, SIZE - 100))
        y0 = int(rng.integers(0, SIZE - 60))
        w  = int(rng.integers(40, 160))
        h  = int(rng.integers(4, 20))
        a  = rng.uniform(0.10, 0.35)
        color = rng.choice(np.array([(255, 60, 0), (255, 200, 0), (255, 30, 30)]))
        draw.rectangle([x0, y0, x0 + w, y0 + h],
                       fill=tuple(int(v * a) for v in color))

    cx, cy = SIZE // 2, SIZE // 2
    for t in [2, 1]:
        draw.line([(cx - 80, cy), (cx + 80, cy)], fill=(255, 80, 0), width=t + 1)
        draw.line([(cx, cy - 80), (cx, cy + 80)], fill=(255, 40, 0), width=t)

    arr = np.array(img)
    noise = rng.integers(0, 10, arr.shape, dtype=np.uint8)
    return Image.fromarray(np.clip(arr.astype(np.int16) + noise, 0, 255).astype(np.uint8))


def make_noite(rng: np.random.Generator) -> Image.Image:
    """Deep purple, fog layers, floating particles, no horizon."""
    img = Image.new("RGB", (SIZE, SIZE))
    draw = ImageDraw.Draw(img)
    gradient_bg(draw, SIZE, SIZE, (6, 3, 14), (18, 5, 38))

    for _ in range(6):
        cx = int(rng.integers(100, SIZE - 100))
        cy = int(rng.integers(100, SIZE - 100))
        r  = int(rng.integers(80, 200))
        a  = rng.uniform(0.02, 0.07)
        color = rng.choice(np.array([(100, 0, 180), (60, 0, 120), (180, 0, 200), (20, 10, 80)]))
        draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                     fill=tuple(int(v * a) for v in color))

    img = img.filter(ImageFilter.GaussianBlur(12))
    draw2 = ImageDraw.Draw(img)

    for _ in range(80):
        x = int(rng.integers(0, SIZE))
        y = int(rng.integers(0, SIZE))
        r = int(rng.integers(1, 3))
        a = rng.uniform(0.2, 0.7)
        draw2.ellipse([x - r, y - r, x + r, y + r],
                      fill=tuple(int(v * a) for v in (200, 150, 255)))

    for i in range(0, SIZE, 3):
        a = rng.uniform(0.005, 0.02)
        draw2.line([(0, i), (SIZE, i)],
                   fill=tuple(int(v * a) for v in (120, 0, 255)), width=1)

    arr = np.array(img)
    noise = rng.integers(0, 8, arr.shape, dtype=np.uint8)
    return Image.fromarray(np.clip(arr.astype(np.int16) + noise, 0, 255).astype(np.uint8))


def make_viagem(rng: np.random.Generator) -> Image.Image:
    """Horizontal landscape bands, road-trip palette."""
    img = Image.new("RGB", (SIZE, SIZE))
    draw = ImageDraw.Draw(img)
    gradient_bg(draw, SIZE, SIZE, (20, 50, 100), (200, 120, 60))

    horizon = int(SIZE * 0.62)
    for y0, y1, top, bot in [
        (horizon,      SIZE,      (30, 40, 25), (50, 65, 40)),
        (horizon - 30, horizon,   (60, 80, 50), (80, 105, 65)),
    ]:
        for y in range(y0, y1):
            t = (y - y0) / max(y1 - y0, 1)
            draw.line([(0, y), (SIZE, y)], fill=lerp_color(top, bot, t))

    sx = int(rng.integers(SIZE // 3, SIZE * 2 // 3))
    for r in range(45, 0, -3):
        t_sun = 1 - r / 45
        c = lerp_color((255, 200, 60), (255, 100, 20), t_sun)
        a_factor = 0.4 + 0.6 * t_sun
        draw.ellipse([sx - r, horizon - r - 10, sx + r, horizon + r - 10],
                     fill=tuple(int(v * a_factor) for v in c))

    road_cx = SIZE // 2
    draw.polygon([(road_cx - 60, SIZE), (road_cx + 60, SIZE),
                  (road_cx + 10, horizon), (road_cx - 10, horizon)],
                 fill=(40, 35, 28))
    for y in range(horizon, SIZE, 30):
        t = (y - horizon) / (SIZE - horizon)
        w = max(1, int(4 * t))
        draw.line([(road_cx - w // 2, y), (road_cx + w // 2, y)],
                  fill=(200, 180, 90), width=w)

    img = img.filter(ImageFilter.GaussianBlur(0.6))
    arr = np.array(img)
    noise = rng.integers(0, 10, arr.shape, dtype=np.uint8)
    return Image.fromarray(np.clip(arr.astype(np.int16) + noise, 0, 255).astype(np.uint8))


SERIES1_GENERATORS = {
    "rap":  make_rap,
    "mpb":  make_mpb,
    "rock": make_rock,
    "jazz": make_jazz,
    "folk": make_folk,
}

SERIES2_GENERATORS = {
    "concentracao": make_concentracao,
    "energia":      make_energia,
    "noite":        make_noite,
    "viagem":       make_viagem,
}

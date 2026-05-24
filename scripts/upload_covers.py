#!/usr/bin/env python3
"""
Series 1 — Generate and upload covers for the 5 genre-based playlists.
Each style is procedurally generated via Pillow + NumPy with a fixed seed.

Update PLAYLISTS below with your own playlist IDs before running.

Série 1 — Gera e sobe capas para as 5 playlists por gênero.
Atualize PLAYLISTS abaixo com os IDs das suas playlists antes de rodar.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import numpy as np
from config import COVERS_DIR
from spotify_curation.client import get_spotify
from spotify_curation.covers import SERIES1_GENERATORS, upload_cover

os.makedirs(COVERS_DIR, exist_ok=True)

# Replace these IDs with your own playlist IDs after running create_curated_playlists.py
PLAYLISTS = [
    {"id": "2IvwXP4CaC9u3ucXAutAhG", "name": "Rap Brasileiro",   "style": "rap"},
    {"id": "6FunQKjgNG8VYXDni99gcK", "name": "MPB Fundo do Baú", "style": "mpb"},
    {"id": "1ybGMMJf8zitN2BSpnPAB5", "name": "Rock Alternativo", "style": "rock"},
    {"id": "3iwd4H8A82DnddHdIf655B", "name": "Jazz & Fusão",     "style": "jazz"},
    {"id": "2jI8z5OkCVeSslN34GH9cc", "name": "Voz & Silêncio",   "style": "folk"},
]


def main():
    sp  = get_spotify()
    rng = np.random.default_rng(42)

    for pl in PLAYLISTS:
        print(f"Generating: {pl['name']}...", flush=True)
        img  = SERIES1_GENERATORS[pl["style"]](rng)
        path = os.path.join(COVERS_DIR, f"{pl['style']}.jpg")
        img.save(path, format="JPEG", quality=90)

        status = upload_cover(sp, pl["id"], img)
        if status in (200, 202, 204):
            print("  ✓ Cover uploaded")
        else:
            print(f"  ✗ Failed (status {status})")


if __name__ == "__main__":
    main()

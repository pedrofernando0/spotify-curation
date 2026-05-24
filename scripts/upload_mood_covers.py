#!/usr/bin/env python3
"""
Series 2 — Generate and upload covers for the 4 mood-based playlists.
Distinct visual design from Series 1.

Update PLAYLISTS below with your own playlist IDs before running.

Série 2 — Gera e sobe capas para as 4 playlists por mood.
Design visual distinto da Série 1.

Atualize PLAYLISTS abaixo com os IDs das suas playlists antes de rodar.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import numpy as np
from config import COVERS_DIR
from spotify_curation.client import get_spotify
from spotify_curation.covers import SERIES2_GENERATORS, upload_cover

os.makedirs(COVERS_DIR, exist_ok=True)

# Replace these IDs with your own playlist IDs after running create_mood_playlists.py
PLAYLISTS = [
    {"id": "5IIYNUmhBP8WinULZMOPwj", "name": "Foco Profundo", "style": "concentracao"},
    {"id": "0NVCoMiHzWsWvkiT5dqIck", "name": "Ignição",       "style": "energia"},
    {"id": "1iBuFgHeEnBhIUlYsufzcL", "name": "Madrugada",     "style": "noite"},
    {"id": "5YyR4s6yVw8B2v9okFtMK4", "name": "Janela Aberta", "style": "viagem"},
]


def main():
    sp  = get_spotify()
    rng = np.random.default_rng(99)

    for pl in PLAYLISTS:
        print(f"Generating cover: {pl['name']} ({pl['style']})...", flush=True)
        img  = SERIES2_GENERATORS[pl["style"]](rng)
        path = os.path.join(COVERS_DIR, f"mood_{pl['style']}.jpg")
        img.save(path, format="JPEG", quality=90)
        print(f"  Saved to {path}")

        status = upload_cover(sp, pl["id"], img)
        if status in (200, 202, 204):
            print("  ✓ Cover uploaded")
        else:
            print(f"  ✗ Failed (status {status})")


if __name__ == "__main__":
    main()

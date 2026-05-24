#!/usr/bin/env python3
"""
Series 2 — Generate and upload procedural covers for mood-based playlists.

After running create_mood_playlists.py, paste the returned playlist IDs
into PLAYLISTS below. The "style" key selects the visual generator.

Available styles: concentracao | energia | noite | viagem
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import numpy as np
from config import COVERS_DIR
from spotify_curation.client import get_spotify
from spotify_curation.covers import SERIES2_GENERATORS, upload_cover

os.makedirs(COVERS_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# CUSTOMIZE THIS — paste your playlist IDs after running create_mood_playlists.py.
# Pick a "style" key matching the mood aesthetic you want.
# ---------------------------------------------------------------------------
PLAYLISTS = [
    {"id": "<YOUR_PLAYLIST_ID_1>", "name": "Focus Playlist",   "style": "concentracao"},
    {"id": "<YOUR_PLAYLIST_ID_2>", "name": "Energy Playlist",  "style": "energia"},
    {"id": "<YOUR_PLAYLIST_ID_3>", "name": "Night Playlist",   "style": "noite"},
    {"id": "<YOUR_PLAYLIST_ID_4>", "name": "Journey Playlist", "style": "viagem"},
]


def main():
    sp  = get_spotify()
    rng = np.random.default_rng(99)

    for pl in PLAYLISTS:
        if pl["id"].startswith("<"):
            print(f"Skipping '{pl['name']}' — no playlist ID set.")
            continue
        if pl["style"] not in SERIES2_GENERATORS:
            print(f"Unknown style '{pl['style']}'. Available: {list(SERIES2_GENERATORS)}")
            continue

        print(f"Generating cover: {pl['name']} ({pl['style']})...", flush=True)
        img  = SERIES2_GENERATORS[pl["style"]](rng)
        path = os.path.join(COVERS_DIR, f"mood_{pl['style']}.jpg")
        img.save(path, format="JPEG", quality=90)
        print(f"  Saved to {path}")

        status = upload_cover(sp, pl["id"], img)
        if status in (200, 202, 204):
            print("  ✓ Cover uploaded")
        else:
            print(f"  ✗ Failed (HTTP {status})")


if __name__ == "__main__":
    main()

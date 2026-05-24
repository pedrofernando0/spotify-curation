#!/usr/bin/env python3
"""
Series 1 — Generate and upload procedural covers for genre-based playlists.

After running create_curated_playlists.py, paste the returned playlist IDs
into PLAYLISTS below. The "style" key selects the visual generator.

Available styles: rap | mpb | rock | jazz | folk
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import numpy as np
from config import COVERS_DIR
from spotify_curation.client import get_spotify
from spotify_curation.covers import SERIES1_GENERATORS, upload_cover

os.makedirs(COVERS_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# CUSTOMIZE THIS — paste your playlist IDs after running create_curated_playlists.py.
# Pick a "style" key for each playlist's visual aesthetic.
# ---------------------------------------------------------------------------
PLAYLISTS = [
    {"id": "<YOUR_PLAYLIST_ID_1>", "name": "My Playlist 1", "style": "rock"},
    {"id": "<YOUR_PLAYLIST_ID_2>", "name": "My Playlist 2", "style": "jazz"},
    {"id": "<YOUR_PLAYLIST_ID_3>", "name": "My Playlist 3", "style": "folk"},
]


def main():
    sp  = get_spotify()
    rng = np.random.default_rng(42)

    for pl in PLAYLISTS:
        if pl["id"].startswith("<"):
            print(f"Skipping '{pl['name']}' — no playlist ID set.")
            continue
        if pl["style"] not in SERIES1_GENERATORS:
            print(f"Unknown style '{pl['style']}'. Available: {list(SERIES1_GENERATORS)}")
            continue

        print(f"Generating cover: {pl['name']} ({pl['style']})...", flush=True)
        img  = SERIES1_GENERATORS[pl["style"]](rng)
        path = os.path.join(COVERS_DIR, f"{pl['style']}.jpg")
        img.save(path, format="JPEG", quality=90)

        status = upload_cover(sp, pl["id"], img)
        if status in (200, 202, 204):
            print("  ✓ Cover uploaded")
        else:
            print(f"  ✗ Failed (HTTP {status})")


if __name__ == "__main__":
    main()

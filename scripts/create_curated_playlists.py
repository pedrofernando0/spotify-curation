#!/usr/bin/env python3
"""
Series 1 — Create genre-based curated playlists via Spotify Web API.
Filters against do_not_include.json; max 2 tracks per artist.

Customize PLAYLISTS below with genres and artists that match YOUR profile.
The goal is to discover tracks from artists you don't yet have in your library.
"""

import json
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import LIBRARY_DIR
from spotify_curation.client import get_spotify

# ---------------------------------------------------------------------------
# CUSTOMIZE THIS — define your playlists and target artists.
#
# Strategy: pick artists that are *adjacent* to what you already love but
# absent (or rare) in your library. Run export_library.py first to know
# which artists you already have covered.
#
# Rules applied automatically:
#   - Tracks already in your library (do_not_include.json) are excluded
#   - Max MAX_PER_ARTIST tracks picked per artist
#   - Artists are searched in order; stops at TARGET_TOTAL tracks
# ---------------------------------------------------------------------------
PLAYLISTS = [
    {
        "name": "My Playlist — Genre 1",
        "description": "Short description shown in Spotify.",
        "artists": [
            # Replace with artists you want to explore in this genre.
            # Example (Alternative Rock):
            "Radiohead",
            "The National",
            "Interpol",
            "Pixies",
            "Pavement",
        ],
    },
    {
        "name": "My Playlist — Genre 2",
        "description": "Short description shown in Spotify.",
        "artists": [
            # Example (Contemporary Jazz):
            "Kamasi Washington",
            "Robert Glasper",
            "BadBadNotGood",
            "Thundercat",
            "Nubya Garcia",
        ],
    },
    {
        "name": "My Playlist — Genre 3",
        "description": "Short description shown in Spotify.",
        "artists": [
            # Example (Folk / Acoustic):
            "Nick Drake",
            "Iron & Wine",
            "Fleet Foxes",
            "Sufjan Stevens",
            "Gillian Welch",
        ],
    },
]

MAX_PER_ARTIST = 2
TARGET_TOTAL   = 20


def load_blocked_ids():
    path = os.path.join(LIBRARY_DIR, "do_not_include.json")
    with open(path) as f:
        return set(json.load(f))


def search_artist_top_tracks(sp, artist_name, blocked_ids):
    results = sp.search(q=f"artist:{artist_name}", type="track", limit=10)
    items   = (results.get("tracks") or {}).get("items") or []
    tracks  = []
    seen    = set()
    for t in items:
        if not t.get("id") or t["id"] in blocked_ids or t["id"] in seen:
            continue
        track_artists = [a["name"].lower() for a in (t.get("artists") or [])]
        if not any(artist_name.lower() in a or a in artist_name.lower()
                   for a in track_artists):
            continue
        seen.add(t["id"])
        tracks.append({
            "id":         t["id"],
            "uri":        t["uri"],
            "name":       t["name"],
            "artist":     (t.get("artists") or [{}])[0].get("name", artist_name),
            "popularity": t.get("popularity", 0),
        })
    return tracks


def curate_playlist_tracks(sp, artist_names, blocked_ids):
    selected = []
    for artist_name in artist_names:
        if len(selected) >= TARGET_TOTAL:
            break
        candidates = sorted(
            search_artist_top_tracks(sp, artist_name, blocked_ids),
            key=lambda x: x["popularity"],
            reverse=True,
        )
        picked = 0
        for track in candidates:
            if picked >= MAX_PER_ARTIST:
                break
            selected.append(track)
            blocked_ids.add(track["id"])
            picked += 1
        time.sleep(0.1)
    return selected[:TARGET_TOTAL]


def create_playlist_with_tracks(sp, name, description, tracks):
    pl    = sp._post("me/playlists", payload={"name": name, "description": description, "public": True})
    pl_id = pl["id"]
    uris  = [t["uri"] for t in tracks]
    for i in range(0, len(uris), 100):
        sp.playlist_add_items(pl_id, uris[i:i + 100])
    return pl_id, pl["external_urls"]["spotify"]


def main():
    sp          = get_spotify(show_dialog=True)
    blocked_ids = load_blocked_ids()

    print(f"Blocked library: {len(blocked_ids)} IDs\n")

    for pl_def in PLAYLISTS:
        print(f"=== {pl_def['name']} ===")
        tracks = curate_playlist_tracks(sp, pl_def["artists"], blocked_ids)
        print(f"  {len(tracks)} tracks selected:")
        for t in tracks:
            print(f"    · {t['artist']} — {t['name']}")

        if len(tracks) < 5:
            print("  WARNING: fewer than 5 tracks, skipping creation.\n")
            continue

        pl_id, url = create_playlist_with_tracks(
            sp, pl_def["name"], pl_def["description"], tracks
        )
        print(f"  ✓ Created: {url}\n")


if __name__ == "__main__":
    main()

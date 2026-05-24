#!/usr/bin/env python3
"""
Series 2 — Discover artists by category and mood tag.
Uses search(type=track) to find top tracks per artist — avoids deprecated
endpoints that require Spotify Extended Quota Mode.

Filters out already-known artists (followed or 3+ liked tracks).
Saves library/recommendations.json for use by create_mood_playlists.py.
Supports automatic checkpointing: safe to interrupt and re-run.

Customize DISCOVERY_ARTISTS below with artists that match YOUR discovery goals.
"""

import json
import re
import sys
import os
import time
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import LIBRARY_DIR
from spotify_curation.client import get_spotify

# ---------------------------------------------------------------------------
# CUSTOMIZE THIS — editorial list of artists you want to discover.
#
# Structure: { "Category Label": [ ("Artist Name", ["mood1", "mood2"]), ... ] }
#
# Available moods (used by create_mood_playlists.py to group tracks):
#   focus | energy | night | journey
#   (or define your own — just keep them consistent with PLAYLISTS in
#    create_mood_playlists.py)
#
# How artists are filtered automatically:
#   - Artists you already follow are skipped
#   - Artists with 3+ liked tracks in your library are skipped
#   - Tracks already in your library are excluded from results
#
# Strategy: pick artists adjacent to your profile that you haven't deeply
# explored yet. Run export_library.py first to see what you already have.
# ---------------------------------------------------------------------------
DISCOVERY_ARTISTS = {
    "Category 1 — e.g. Contemporary Hip-Hop": [
        # Replace with artists you want to explore in this category.
        # Example artists — adjust popularity/obscurity to your taste:
        ("Saba",            ["focus", "night"]),
        ("JID",             ["energy", "night"]),
        ("Noname",          ["focus", "night"]),
        ("JPEGMAFIA",       ["energy", "night"]),
        ("Earl Sweatshirt", ["night", "focus"]),
    ],
    "Category 2 — e.g. Post-Punk / Indie Rock": [
        # Example artists:
        ("Fontaines D.C.",   ["energy", "journey"]),
        ("Shame",            ["energy"]),
        ("DIIV",             ["night", "focus"]),
        ("Beach House",      ["night", "focus"]),
        ("Wolf Alice",       ["energy", "night"]),
    ],
    "Category 3 — e.g. Post-Rock / Ambient": [
        # Example artists:
        ("Explosions in the Sky", ["focus", "journey"]),
        ("Sigur Rós",             ["focus", "journey"]),
        ("Russian Circles",       ["energy", "focus"]),
        ("God Is an Astronaut",   ["focus", "journey"]),
        ("Mogwai",                ["night", "focus"]),
    ],
}

_SUFFIX_RE = re.compile(r'\s*[-–(].*$')


def canonical_name(s: str) -> str:
    """Strips live/remaster suffixes for deduplication."""
    return _SUFFIX_RE.sub("", s).strip().lower()


def load_known_artists():
    path = os.path.join(LIBRARY_DIR, "followed_artists.json")
    with open(path) as f:
        data = json.load(f)
    return {(a.get("name", "") if isinstance(a, dict) else str(a)).lower() for a in data}


def load_artist_track_counts():
    path = os.path.join(LIBRARY_DIR, "saved_tracks.json")
    with open(path) as f:
        tracks = json.load(f)
    counts = defaultdict(int)
    for t in tracks:
        for a in t.get("artists", []):
            counts[a.lower()] += 1
    return counts


def load_blocked_ids():
    path = os.path.join(LIBRARY_DIR, "do_not_include.json")
    with open(path) as f:
        return set(json.load(f))


def search_top_tracks(sp, artist_name, blocked_ids, n=3, retries=3):
    for attempt in range(retries):
        try:
            results = sp.search(q=f"artist:{artist_name}", type="track", limit=10)
            break
        except Exception as e:
            if attempt < retries - 1 and "timeout" in str(e).lower():
                wait = 2 ** attempt
                print(f"    timeout, retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise

    items      = (results.get("tracks") or {}).get("items") or []
    candidates = []
    seen_ids   = set()
    seen_names = set()

    for t in items:
        if not t.get("id") or t["id"] in blocked_ids or t["id"] in seen_ids:
            continue
        track_artists = [a["name"].lower() for a in (t.get("artists") or [])]
        if not any(artist_name.lower() in a or a in artist_name.lower()
                   for a in track_artists):
            continue
        cname = canonical_name(t["name"])
        if cname in seen_names:
            continue
        seen_ids.add(t["id"])
        seen_names.add(cname)
        candidates.append({
            "name":       t["name"],
            "uri":        t["uri"],
            "id":         t["id"],
            "popularity": t.get("popularity", 0),
            "artist":     (t.get("artists") or [{}])[0].get("name", artist_name),
        })

    candidates.sort(key=lambda x: -x["popularity"])
    return candidates[:n]


def main():
    sp           = get_spotify(show_dialog=True)
    known        = load_known_artists()
    track_counts = load_artist_track_counts()
    blocked_ids  = load_blocked_ids()

    output_path = os.path.join(LIBRARY_DIR, "recommendations.json")
    if os.path.exists(output_path):
        with open(output_path) as f:
            existing = json.load(f)
        recommendations = {r["name"]: r for r in existing}
        print(f"  Resuming from checkpoint: {len(recommendations)} artists already processed")
    else:
        recommendations = {}

    total = sum(len(v) for v in DISCOVERY_ARTISTS.values())
    done  = 0

    for category, artist_list in DISCOVERY_ARTISTS.items():
        for (artist_name, moods) in artist_list:
            done += 1
            name_lower = artist_name.lower()

            skip_reason = None
            if artist_name in recommendations:
                skip_reason = "checkpoint"
            elif name_lower in known:
                skip_reason = "already followed"
            elif track_counts.get(name_lower, 0) >= 3:
                skip_reason = f"{track_counts[name_lower]} liked tracks"

            if skip_reason:
                print(f"  [{done}/{total}] {artist_name} — skip ({skip_reason})")
                continue

            tracks = search_top_tracks(sp, artist_name, blocked_ids)
            time.sleep(0.15)

            if not tracks:
                print(f"  [{done}/{total}] {artist_name} — no tracks found")
                continue

            pop = tracks[0]["popularity"] if tracks else 0
            print(f"  [{done}/{total}] {artist_name} (pop:{pop}) — {len(tracks)} tracks")

            if artist_name not in recommendations:
                recommendations[artist_name] = {
                    "name":       artist_name,
                    "popularity": pop,
                    "categories": [],
                    "moods":      [],
                    "top_tracks": tracks,
                }

            if category not in recommendations[artist_name]["categories"]:
                recommendations[artist_name]["categories"].append(category)
            for m in moods:
                if m not in recommendations[artist_name]["moods"]:
                    recommendations[artist_name]["moods"].append(m)

            with open(output_path, "w") as f:
                json.dump(list(recommendations.values()), f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    for category in DISCOVERY_ARTISTS.keys():
        artists_in_cat = sorted(
            [r for r in recommendations.values() if category in r["categories"]],
            key=lambda x: -x["popularity"],
        )
        print(f"\n{category}  ({len(artists_in_cat)} artists)")
        for meta in artists_in_cat:
            moods_str = " · ".join(meta["moods"])
            print(f"  {meta['name']}  (pop: {meta['popularity']})  [{moods_str}]")

    mood_counts = defaultdict(int)
    for r in recommendations.values():
        for m in r["moods"]:
            mood_counts[m] += 1
    print(f"\n✓ {len(recommendations)} artists saved to {output_path}")
    print("\nArtists per mood:")
    for mood, count in sorted(mood_counts.items()):
        print(f"  {mood}: {count}")


if __name__ == "__main__":
    main()

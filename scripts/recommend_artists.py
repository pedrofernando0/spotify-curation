#!/usr/bin/env python3
"""
Series 2 — Discover artists by category and mood tag.
Uses search(type=track) to find top tracks per artist (avoids deprecated endpoints
that require Spotify Extended Quota Mode).

Filters out already-known artists (followed or 3+ liked tracks).
Saves library/recommendations.json for use by create_mood_playlists.py.
Supports automatic checkpointing: safe to interrupt and re-run.

---

Série 2 — Recomenda artistas de descoberta por categoria e mood.
Usa search(type=track) — endpoints /top-tracks e /recommendations exigem
Extended Quota no Spotify, search não.

Filtra artistas já conhecidos (seguidos ou 3+ músicas curtidas).
Suporta checkpoint automático: seguro interromper e re-executar.
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

# Editorial curation by style proximity + mood mapping.
# moods: concentracao | energia | noite | viagem
DISCOVERY_ARTISTS = {
    "Rock BR": [
        ("Boogarins",         ["viagem", "concentracao"]),
        ("Fresno",            ["noite", "energia"]),
        ("Supercombo",        ["energia", "viagem"]),
        ("Pato Fu",           ["viagem", "noite"]),
        ("Bixiga 70",         ["energia", "viagem"]),
        ("Maglore",           ["noite", "concentracao"]),
        ("Deafkids",          ["energia", "concentracao"]),
        ("Cidadão Instigado", ["noite", "concentracao"]),
        ("Cachorro Grande",   ["energia", "viagem"]),
        ("Dead Fish",         ["energia"]),
        ("Plebe Rude",        ["noite", "energia"]),
        ("Ratos de Porão",    ["energia"]),
        ("Garage Fuzz",       ["energia", "noite"]),
    ],
    "Hip-Hop Internacional": [
        ("Saba",            ["concentracao", "noite"]),
        ("JID",             ["energia", "noite"]),
        ("Smino",           ["noite", "concentracao"]),
        ("Noname",          ["concentracao", "noite"]),
        ("ScHoolboy Q",     ["energia", "noite"]),
        ("Earl Sweatshirt", ["noite", "concentracao"]),
        ("JPEGMAFIA",       ["energia", "noite"]),
        ("Denzel Curry",    ["energia"]),
        ("Joey Bada$$",     ["concentracao", "energia"]),
        ("Ab-Soul",         ["noite", "concentracao"]),
        ("Aminé",           ["energia", "viagem"]),
        ("Navy Blue",       ["concentracao", "noite"]),
        ("billy woods",     ["noite", "concentracao"]),
        ("Fly Anakin",      ["concentracao", "noite"]),
        ("Quelle Chris",    ["noite", "concentracao"]),
    ],
    "Rock Internacional": [
        ("Tame Impala",           ["noite", "viagem", "concentracao"]),
        ("The War on Drugs",      ["viagem", "concentracao"]),
        ("Beach House",           ["noite", "concentracao"]),
        ("Portishead",            ["noite", "concentracao"]),
        ("Massive Attack",        ["noite", "concentracao"]),
        ("Fontaines D.C.",        ["energia", "viagem"]),
        ("Shame",                 ["energia"]),
        ("Yard Act",              ["energia", "noite"]),
        ("DIIV",                  ["noite", "concentracao"]),
        ("Squid",                 ["energia", "noite"]),
        ("Wolf Alice",            ["energia", "noite"]),
        ("Nothing But Thieves",   ["energia", "noite"]),
        ("Cigarettes After Sex",  ["noite"]),
        ("Explosions in the Sky", ["concentracao", "viagem"]),
        ("Sigur Rós",             ["concentracao", "viagem"]),
        ("God Is an Astronaut",   ["concentracao", "viagem"]),
        ("Russian Circles",       ["energia", "concentracao"]),
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

    print("\n\n" + "=" * 62)
    print("  DISCOVERY RECOMMENDATIONS / RECOMENDAÇÕES DE DESCOBERTA")
    print("=" * 62)

    for category in DISCOVERY_ARTISTS.keys():
        artists_in_cat = sorted(
            [r for r in recommendations.values() if category in r["categories"]],
            key=lambda x: -x["popularity"],
        )
        print(f"\n\n{'─' * 62}")
        print(f"  {category.upper()}  ({len(artists_in_cat)} artists)")
        print(f"{'─' * 62}")
        for meta in artists_in_cat:
            moods_str = " · ".join(meta["moods"])
            print(f"\n  {meta['name']}  (pop: {meta['popularity']})  [{moods_str}]")
            for i, t in enumerate(meta["top_tracks"], 1):
                print(f"    {i}. {t['name']}")
                print(f"       {t['uri']}")

    mood_counts = defaultdict(int)
    for r in recommendations.values():
        for m in r["moods"]:
            mood_counts[m] += 1
    print(f"\n\n✓ {len(recommendations)} artists saved to {output_path}")
    print("\n  Artists per mood:")
    for mood, count in sorted(mood_counts.items()):
        print(f"    {mood}: {count}")


if __name__ == "__main__":
    main()

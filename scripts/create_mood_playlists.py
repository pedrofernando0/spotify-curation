#!/usr/bin/env python3
"""
Series 2 — Create 4 mood-based playlists from recommendations.json.
Filters against do_not_include.json; max 2 tracks per artist.

Série 2 — Cria 4 playlists por mood a partir de recommendations.json.
Filtra contra do_not_include.json; máx 2 tracks por artista.
"""

import json
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import LIBRARY_DIR
from spotify_curation.client import get_spotify

PLAYLISTS = [
    {
        "mood":       "concentracao",
        "name":       "Foco Profundo — Instrumental e Flow",
        "description":"Post-rock, trip-hop e hip-hop introspectivo. Sem distração.",
        "max_tracks": 25,
    },
    {
        "mood":       "energia",
        "name":       "Ignição — Rock e Rap de Alta Tensão",
        "description":"Pós-punk, noise rock BR, hip-hop agressivo. Pra ligar o motor.",
        "max_tracks": 25,
    },
    {
        "mood":       "noite",
        "name":       "Madrugada — Peso e Densidade",
        "description":"Trip-hop, dream pop, rap noturno e rock que respira devagar.",
        "max_tracks": 25,
    },
    {
        "mood":       "viagem",
        "name":       "Janela Aberta — Pra Rodar",
        "description":"Rock BR e pós-rock que abre espaço. Pra estrada, pra escapar.",
        "max_tracks": 25,
    },
]

MAX_PER_ARTIST = 2


def load_blocked_ids():
    path = os.path.join(LIBRARY_DIR, "do_not_include.json")
    with open(path) as f:
        return set(json.load(f))


def load_recommendations():
    path = os.path.join(LIBRARY_DIR, "recommendations.json")
    with open(path) as f:
        return json.load(f)


def curate_tracks(recommendations, mood, blocked_ids, max_tracks):
    eligible    = [r for r in recommendations if mood in r.get("moods", [])]
    selected    = []
    used_artists = set()
    used_blocked = set(blocked_ids)

    for artist_data in eligible:
        if len(selected) >= max_tracks:
            break
        name = artist_data["name"]
        if name in used_artists:
            continue
        picked = 0
        for track in artist_data.get("top_tracks", []):
            if picked >= MAX_PER_ARTIST:
                break
            if track["id"] in used_blocked:
                continue
            selected.append({
                "uri":    track["uri"],
                "id":     track["id"],
                "name":   track["name"],
                "artist": name,
            })
            used_blocked.add(track["id"])
            picked += 1
        if picked > 0:
            used_artists.add(name)

    return selected[:max_tracks]


def create_playlist_with_tracks(sp, name, description, tracks):
    pl    = sp._post("me/playlists", payload={"name": name, "description": description, "public": True})
    pl_id = pl["id"]
    uris  = [t["uri"] for t in tracks]
    for i in range(0, len(uris), 100):
        sp.playlist_add_items(pl_id, uris[i:i + 100])
    return pl_id, pl["external_urls"]["spotify"]


def main():
    sp              = get_spotify(show_dialog=True)
    blocked_ids     = load_blocked_ids()
    recommendations = load_recommendations()

    print(f"Recommendations loaded: {len(recommendations)} artists")
    print(f"Blocked IDs: {len(blocked_ids)}\n")

    results = []
    for pl_def in PLAYLISTS:
        mood   = pl_def["mood"]
        tracks = curate_tracks(recommendations, mood, blocked_ids, pl_def["max_tracks"])

        print(f"=== {pl_def['name']} ===")
        print(f"  mood: {mood}  |  {len(tracks)} tracks")
        for t in tracks:
            print(f"    · {t['artist']} — {t['name']}")

        if len(tracks) < 5:
            print("  WARNING: fewer than 5 tracks, skipping creation.\n")
            continue

        pl_id, url = create_playlist_with_tracks(
            sp, pl_def["name"], pl_def["description"], tracks
        )
        print(f"  ✓ {url}\n")
        results.append({"name": pl_def["name"], "id": pl_id, "url": url, "tracks": len(tracks)})
        time.sleep(0.5)

    print("\n=== SUMMARY ===")
    for r in results:
        print(f"  {r['name']}")
        print(f"    {r['url']}")
        print(f"    {r['tracks']} tracks | ID: {r['id']}")


if __name__ == "__main__":
    main()

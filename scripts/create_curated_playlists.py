#!/usr/bin/env python3
"""
Series 1 — Create 5 genre-based curated playlists via Spotify Web API.
Filters against do_not_include.json; max 2 tracks per artist.

Série 1 — Cria 5 playlists curadas por gênero via Spotify Web API.
Filtra contra do_not_include.json; máx 2 tracks por artista.
"""

import json
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import LIBRARY_DIR
from spotify_curation.client import get_spotify

# Target artists per playlist: adjacent to the profile, absent or rare in the library.
# Artistas-alvo: adjacentes ao perfil, ausentes ou raros na biblioteca.
PLAYLISTS = [
    {
        "name": "Rap Brasileiro — O Que o Algoritmo Escondeu",
        "description": "Underground e alternativo do rap BR, além dos seus fixos.",
        "artists": [
            "Rincon Sapiência", "Matuê", "Rashid", "Cynthia Luz", "Rico Dalasam",
            "Ryan SP", "Kayuá", "Ao Cubo", "Dexter", "Aldeia",
            "Rael", "RDD", "Deco Bronk", "Xênia França", "Funkero",
            "Azagaia", "Muzzike", "Pregador Luo", "Sagu Boyz", "Rapadura",
        ],
    },
    {
        "name": "MPB Fundo do Baú",
        "description": "Raridades e faixas menos óbvias da MPB e samba.",
        "artists": [
            "Milton Nascimento", "Edu Lobo", "Nara Leão", "Baden Powell",
            "Joyce Moreno", "Ivan Lins", "Francis Hime", "Clara Nunes",
            "Gal Costa", "Maria Bethânia", "Chico Buarque", "Paulinho da Viola",
            "Alceu Valença", "Lenine", "Fagner", "Elza Soares",
            "Sivuca", "Hermeto Pascoal", "Tom Zé", "Gonzaguinha",
        ],
    },
    {
        "name": "Rock Alternativo — Além do Que Você Segue",
        "description": "Do pós-punk ao indie, adjacente ao seu universo rock.",
        "artists": [
            "Interpol", "The National", "Nick Cave & The Bad Seeds", "Editors",
            "Placebo", "Foals", "Pixies", "Modest Mouse", "Suede",
            "Bauhaus", "Joy Division", "Wire", "Pavement", "Dinosaur Jr.",
            "My Bloody Valentine", "Smashing Pumpkins", "Failure", "Afghan Whigs",
            "Spiritualized", "Guided by Voices",
        ],
    },
    {
        "name": "Jazz & Fusão Contemporânea",
        "description": "Do hard bop ao jazz moderno — pra quem tem Coltrane no coração.",
        "artists": [
            "Kamasi Washington", "Robert Glasper", "BadBadNotGood", "Hiatus Kaiyote",
            "Christian Scott", "Esperanza Spalding", "Ambrose Akinmusire",
            "Nubya Garcia", "Shabaka Hutchings", "Makaya McCraven",
            "Thundercat", "Flying Lotus", "Brad Mehldau", "Vijay Iyer",
            "Charles Mingus", "Thelonious Monk", "Bill Evans", "Miles Davis",
            "Chet Baker", "Art Blakey",
        ],
    },
    {
        "name": "Voz & Silêncio — Folk e Canção Nua",
        "description": "Pra quem guarda Asaf Avidan e José González — raiz, voz, essência.",
        "artists": [
            "Iron & Wine", "Nick Drake", "Sufjan Stevens", "Gregory Alan Isakov",
            "Bon Iver", "Fleet Foxes", "Damien Rice", "Elliott Smith",
            "Simon & Garfunkel", "Leonard Cohen", "Townes Van Zandt",
            "John Prine", "Gillian Welch", "Adrianne Lenker", "Perfume Genius",
            "Julien Baker", "Hand Habits", "Phoebe Bridgers", "Big Thief", "Waxahatchee",
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
    pl     = sp._post("me/playlists", payload={"name": name, "description": description, "public": True})
    pl_id  = pl["id"]
    uris   = [t["uri"] for t in tracks]
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

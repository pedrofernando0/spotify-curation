#!/usr/bin/env python3
"""
Export complete Spotify library:
  - Liked songs (saved tracks)
  - Owned playlists + their tracks
  - Followed artists
  - Generates do_not_include.json (all known track IDs, used to avoid repeats)

Exporta biblioteca completa do Spotify:
  - Músicas salvas (liked songs)
  - Playlists próprias + tracks
  - Artistas seguidos
  - Gera do_not_include.json (todos os track IDs já conhecidos)
"""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import LIBRARY_DIR
from spotify_curation.client import get_spotify


def safe_track(t):
    if not t or not t.get("id"):
        return None
    return {
        "id":         t.get("id"),
        "uri":        t.get("uri"),
        "name":       t.get("name", ""),
        "artists":    [a.get("name", "") for a in (t.get("artists") or [])],
        "album":      (t.get("album") or {}).get("name", ""),
        "popularity": t.get("popularity"),
    }


def paginate_items(sp, fn, *args, **kwargs):
    results = []
    response = fn(*args, **kwargs)
    while response:
        for item in (response.get("items") or []):
            results.append(item)
        response = sp.next(response) if response.get("next") else None
    return results


def export_saved_tracks(sp):
    print("Exporting liked songs / Exportando músicas salvas...", flush=True)
    items = paginate_items(sp, sp.current_user_saved_tracks, limit=50)
    tracks = []
    for item in items:
        t = safe_track(item.get("track"))
        if not t:
            continue
        t["added_at"] = item.get("added_at")
        tracks.append(t)
    path = os.path.join(LIBRARY_DIR, "saved_tracks.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(tracks, f, ensure_ascii=False, indent=2)
    print(f"  {len(tracks)} tracks → {path}")
    return tracks


def export_followed_artists(sp):
    print("Exporting followed artists / Exportando artistas seguidos...", flush=True)
    artists = []
    response = sp.current_user_followed_artists(limit=50)
    data = response.get("artists", {})
    while data:
        for a in (data.get("items") or []):
            artists.append({
                "id":         a.get("id"),
                "name":       a.get("name", ""),
                "genres":     a.get("genres") or [],
                "popularity": a.get("popularity"),
                "followers":  (a.get("followers") or {}).get("total"),
            })
        data = sp.next(data).get("artists", {}) if data.get("next") else None
    path = os.path.join(LIBRARY_DIR, "followed_artists.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(artists, f, ensure_ascii=False, indent=2)
    print(f"  {len(artists)} artists → {path}")
    return artists


def export_playlists(sp):
    print("Exporting owned playlists / Exportando playlists...", flush=True)
    me = sp.current_user().get("id")
    items = paginate_items(sp, sp.current_user_playlists, limit=50)

    playlists_dir = os.path.join(LIBRARY_DIR, "owned_playlists")
    os.makedirs(playlists_dir, exist_ok=True)

    all_track_ids = set()
    summary = []

    for pl in items:
        if (pl.get("owner") or {}).get("id") != me:
            continue
        pl_id   = pl.get("id")
        pl_name = pl.get("name", "unnamed")

        track_items = paginate_items(sp, sp.playlist_items, pl_id, limit=100)
        tracks = []
        for item in track_items:
            t = safe_track(item.get("track"))
            if not t:
                continue
            tracks.append(t)
            all_track_ids.add(t["id"])

        safe_name = "".join(c for c in pl_name if c.isalnum() or c in " _-")[:60].strip()
        path = os.path.join(playlists_dir, f"{safe_name}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"id": pl_id, "name": pl_name, "tracks": tracks},
                      f, ensure_ascii=False, indent=2)
        summary.append({"id": pl_id, "name": pl_name, "track_count": len(tracks)})
        print(f"  '{pl_name}': {len(tracks)} tracks")

    summary_path = os.path.join(LIBRARY_DIR, "playlists_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    return all_track_ids


def build_do_not_include(saved_tracks, playlist_track_ids):
    print("Building do_not_include.json / Gerando blocklist...", flush=True)
    ids = {t["id"] for t in saved_tracks if t.get("id")} | playlist_track_ids
    path = os.path.join(LIBRARY_DIR, "do_not_include.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(sorted(ids), f, indent=2)
    print(f"  {len(ids)} blocked IDs → {path}")


def main():
    os.makedirs(LIBRARY_DIR, exist_ok=True)
    sp = get_spotify()
    saved = export_saved_tracks(sp)
    export_followed_artists(sp)
    playlist_ids = export_playlists(sp)
    build_do_not_include(saved, playlist_ids)
    print("\nDone / Exportação concluída.")


if __name__ == "__main__":
    main()

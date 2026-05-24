# Architecture — spotify-curation

> **Language:** English (primary) | Portuguese (supplementary)

---

## 1. Introduction and Goals

### 1.1. Problem Statement

Spotify's algorithm optimises for engagement, not discovery. The user's existing library is never used as a hard filter — tracks the user already owns reappear in recommendations, and the "discovery" surface is controlled by a black box.

### 1.2. Solution

**spotify-curation** is a CLI tool that puts the user in full control of playlist creation:

1. **Export** the complete Spotify library (saved tracks, followed artists, owned playlists).
2. **Block** every known track ID so it never appears again.
3. **Curate** playlists from user-defined artist lists (two series: genre-based and mood-based).
4. **Beautify** playlists with procedurally generated cover art (Pillow + NumPy).

### 1.3. Quality Goals

| Goal | Description |
|------|-------------|
| Reproducibility | Cover generation uses fixed random seed — identical output across runs |
| Transparency | No ML, no opaque recommendations; every track selection is traceable to a user-defined artist |
| Offline-first | Library export produces static JSON files — curation logic works without live API access |
| Minimal dependencies | Only spotipy, Pillow, NumPy, requests, python-dotenv |

### 1.4. Portuguese — Objetivos

Ferramenta CLI para criação de playlists personalizadas no Spotify. O usuário define listas de artistas, a ferramenta exporta a biblioteca, bloqueia faixas já conhecidas e cria playlists com capas procedurais.

---

## 2. Constraints

| Constraint | Impact |
|------------|--------|
| **Spotify Web API rate limits** | All scripts throttle requests with `time.sleep(0.1–0.5)` |
| **Deprecated endpoints (Nov 2024)** | `related-artists`, `top-tracks`, `recommendations` return `403` for most apps. The project uses `search(type=track)` instead |
| **JPEG size limit (256 KB)** | `upload_cover` degrades quality iteratively (80→65→50→35) until the base64 payload fits |
| **Python 3.8+** | `ruff.toml` targets py38; avoids 3.9+ features |
| **OAuth browser popup** | First run requires interactive browser for Spotify authorisation |
| **No test suite** | CONTRIBUTING.md explicitly states this — manual verification against a real account is the current standard |

---

## 3. Context and Scope

### 3.1. C4 Level 1 — System Context Diagram

```mermaid
C4Context
  title System Context — spotify-curation

  Person(user, "Spotify User", "Owns a library of saved tracks, followed artists, and playlists")

  System_Boundary(c0, "spotify-curation") {
    System(cli, "CLI Scripts", "6 entry points in scripts/")
  }

  System_Ext(spotify, "Spotify Web API", "REST API v1 — search, playlists, images, auth")
  System_Ext(filesystem, "Local Filesystem", "JSON exports, JPEG covers, OAuth cache")

  Rel(user, cli, "Runs python scripts/", "Terminal")
  Rel(cli, spotify, "HTTPS requests", "SpotifyOAuth + Bearer token")
  Rel(cli, filesystem, "Reads/writes JSON + images", "library/ & output/")

  UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

### 3.2. Scope

**In scope:**
- Export library to JSON (saved tracks, followed artists, owned playlists)
- Block known tracks via `do_not_include.json`
- Create genre-based playlists from user-defined artist lists (Series 1)
- Discover artists by category + mood tag (Series 2)
- Create mood-based playlists (Series 2)
- Generate procedural JPEG covers and upload via Spotify API
- Portuguese/English bilingual README

**Out of scope:**
- Real-time sync or webhook subscriptions (no persistent server)
- Collaborative playlist management
- Spotify playback control
- Machine learning or recommendation engine
- Mobile or web UI

---

## 4. Solution Strategy

### 4.1. Architectural Style

**Pipeline architecture** with two independent series that share a common foundation:

```
                    ┌──────────────────────────────┐
                    │       Shared Foundation        │
                    │  config.py · client.py         │
                    │  covers.py · .env              │
                    └──────────┬───────────────────┘
                               │
              ┌────────────────┼────────────────┐
              │                                 │
    ┌─────────▼──────────┐        ┌─────────────▼──────────┐
    │   Series 1          │        │   Series 2              │
    │   Genre-based       │        │   Mood-based            │
    │                     │        │                         │
    │   export_library.py │        │   export_library.py     │
    │         ↓           │        │         ↓               │
    │ create_curated_     │        │ recommend_artists.py    │
    │   playlists.py      │        │         ↓               │
    │         ↓           │        │ create_mood_            │
    │ upload_covers.py    │        │   playlists.py          │
    │                     │        │         ↓               │
    └─────────────────────┘        │ upload_mood_covers.py   │
                                   └─────────────────────────┘
```

### 4.2. Key Decisions

| Decision | Rationale |
|----------|-----------|
| JSON files as state (no database) | Keeps dependencies minimal; files are human-readable and debuggable; checkpoints enable resume on interrupt |
| Fixed-seed NumPy RNG | Cover art is deterministic and reproducible across runs |
| `search(type=track)` over deprecated endpoints | Available to all Spotify apps without Extended Quota Mode |
| Module-level `sys.path.insert(0, ...)` in scripts | Avoids packaging overhead; scripts run directly with `python scripts/foo.py` |
| `ruff.toml` over `pyproject.toml` | Keeps config minimal; no packaging metadata needed in a script-based project |

---

## 5. Building Block View

### 5.1. C4 Level 2 — Component Diagram

```mermaid
C4Container
  title Component Diagram — spotify-curation

  Person(user, "Spotify User", "Runs CLI scripts")

  System_Boundary(sc, "spotify-curation") {

    Container(config, "config.py", "Python", "Reads env vars; exports paths + scopes")
    Container(client, "client.py", "Python", "Spotipy factory with OAuth")
    Container(covers, "covers.py", "Python", "9 procedural cover generators + upload utility")

    Container(export, "export_library.py", "Python CLI", "Exports saved tracks, followed artists, playlist tracks")
    Container(curated, "create_curated_playlists.py", "Python CLI", "Series 1: genre playlists from artist lists")
    Container(upload1, "upload_covers.py", "Python CLI", "Series 1: covers for genre playlists")
    Container(recommend, "recommend_artists.py", "Python CLI", "Series 2: discover artists, filter known, tag moods")
    Container(mood, "create_mood_playlists.py", "Python CLI", "Series 2: mood playlists from recommendations")
    Container(upload2, "upload_mood_covers.py", "Python CLI", "Series 2: covers for mood playlists")
  }

  System_Ext(spotify, "Spotify Web API", "REST API v1")
  System_Ext(fs, "Filesystem", "library/ · output/")

  Rel(user, export, "python scripts/export_library.py")
  Rel(user, curated, "python scripts/create_curated_playlists.py")
  Rel(user, upload1, "python scripts/upload_covers.py")
  Rel(user, recommend, "python scripts/recommend_artists.py")
  Rel(user, mood, "python scripts/create_mood_playlists.py")
  Rel(user, upload2, "python scripts/upload_mood_covers.py")

  Rel(export, client, "Uses", "get_spotify()")
  Rel(curated, client, "Uses", "get_spotify()")
  Rel(upload1, client, "Uses", "get_spotify()")
  Rel(recommend, client, "Uses", "get_spotify()")
  Rel(mood, client, "Uses", "get_spotify()")
  Rel(upload2, client, "Uses", "get_spotify()")

  Rel(upload1, covers, "Uses", "SERIES1_GENERATORS + upload_cover")
  Rel(upload2, covers, "Uses", "SERIES2_GENERATORS + upload_cover")

  Rel(export, config, "Imports", "LIBRARY_DIR")
  Rel(curated, config, "Imports", "LIBRARY_DIR")
  Rel(recommend, config, "Imports", "LIBRARY_DIR")
  Rel(mood, config, "Imports", "LIBRARY_DIR")

  Rel(client, config, "Imports", "CLIENT_ID, CLIENT_SECRET, ...")
  Rel(upload1, config, "Imports", "COVERS_DIR")
  Rel(upload2, config, "Imports", "COVERS_DIR")

  Rel(export, fs, "Writes JSON", "library/")
  Rel(curated, fs, "Reads", "library/do_not_include.json")
  Rel(recommend, fs, "Reads/Writes checkpoint", "library/")
  Rel(mood, fs, "Reads", "library/recommendations.json")
  Rel(upload1, fs, "Saves JPEG", "output/covers/")

  Rel(curated, spotify, "search + playlist create", "HTTPS")
  Rel(upload1, spotify, "PUT images", "HTTPS")
  Rel(recommend, spotify, "search", "HTTPS")

  UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="2")
```

### 5.2. Module Overview

| Module | Responsibility | Key Exports |
|--------|---------------|-------------|
| `config.py` | Environment-based configuration | `CLIENT_ID`, `CLIENT_SECRET`, `REDIRECT_URI`, `SCOPES`, `LIBRARY_DIR`, `COVERS_DIR` |
| `spotify_curation/client.py` | Spotify OAuth client factory | `get_spotify(show_dialog=False)` |
| `spotify_curation/covers.py` | Procedural cover art + upload | `SERIES1_GENERATORS`, `SERIES2_GENERATORS`, `upload_cover()`, `lerp_color()`, `gradient_bg()` |
| `scripts/export_library.py` | Full library export | `main()` → JSON files in `library/` |
| `scripts/create_curated_playlists.py` | Series 1 playlist creation | `main()` → genre playlists |
| `scripts/upload_covers.py` | Series 1 cover upload | `main()` → JPEG + image upload |
| `scripts/recommend_artists.py` | Series 2 artist discovery | `main()` → `recommendations.json` |
| `scripts/create_mood_playlists.py` | Series 2 mood playlists | `main()` → mood playlists |
| `scripts/upload_mood_covers.py` | Series 2 cover upload | `main()` → JPEG + image upload |

---

## 6. Runtime View

### 6.1. Series 1 — Genre Playlist Creation

```mermaid
sequenceDiagram
    participant User
    participant export as export_library.py
    participant curated as create_curated_playlists.py
    participant upload as upload_covers.py
    participant Spotify
    participant FS as Filesystem

    User->>export: python scripts/export_library.py
    export->>Spotify: current_user_saved_tracks (paginated)
    export->>Spotify: current_user_followed_artists (paginated)
    export->>Spotify: current_user_playlists + playlist_items (paginated)
    export->>FS: Write saved_tracks.json, followed_artists.json
    export->>FS: Write owned_playlists/*.json, playlists_summary.json
    export->>FS: Write do_not_include.json (union of all track IDs)
    export-->>User: Done / Exportação concluída.

    User->>curated: python scripts/create_curated_playlists.py
    curated->>FS: Read do_not_include.json
    loop For each PLAYLIST entry
        loop For each artist
            curated->>Spotify: search(q="artist:{name}", type="track")
            Spotify-->>curated: Top 10 tracks
            curated->>curated: Filter blocked IDs, pick top MAX_PER_ARTIST by popularity
        end
        curated->>Spotify: POST me/playlists (create playlist)
        curated->>Spotify: playlist_add_items (batch 100 URIs)
    end
    curated-->>User: Created: {url}

    User->>upload: python scripts/upload_covers.py
    upload->>upload: Generate procedural cover (Pillow + NumPy, seed=42)
    upload->>Spotify: PUT /playlists/{id}/images (base64 JPEG)
    Spotify-->>upload: 200/202/204
    upload->>FS: Save JPEG to output/covers/
    upload-->>User: Cover uploaded
```

### 6.2. Series 2 — Mood Playlist Discovery & Creation

```mermaid
sequenceDiagram
    participant User
    participant export as export_library.py
    participant rec as recommend_artists.py
    participant mood as create_mood_playlists.py
    participant upload as upload_mood_covers.py
    participant Spotify
    participant FS as Filesystem

    User->>export: python scripts/export_library.py
    export->>FS: Write library/*.json + do_not_include.json

    User->>rec: python scripts/recommend_artists.py
    rec->>FS: Read followed_artists.json, saved_tracks.json, do_not_include.json
    loop For each artist in DISCOVERY_ARTISTS
        alt Artist known (followed or 3+ liked tracks)
            rec->>rec: Skip — reason logged
        else New artist
            rec->>Spotify: search(q="artist:{name}", type="track")
            Spotify-->>rec: Top tracks (popularity-sorted)
            rec->>rec: Deduplicate, pick top 3
        end
        rec->>FS: Write checkpoint to recommendations.json (after each artist)
    end
    rec-->>User: Summary per category + mood counts

    User->>mood: python scripts/create_mood_playlists.py
    mood->>FS: Read recommendations.json, do_not_include.json
    loop For each mood (focus, energy, night, journey)
        mood->>mood: Filter artists by mood, pick MAX_PER_ARTIST tracks
        mood->>Spotify: POST me/playlists
        mood->>Spotify: playlist_add_items
    end
    mood-->>User: Created playlist URLs

    User->>upload: python scripts/upload_mood_covers.py
    upload->>upload: Generate procedural cover (Pillow + NumPy, seed=99)
    upload->>Spotify: PUT /playlists/{id}/images
    upload-->>User: Cover uploaded
```

### 6.3. Cover Upload — JPEG Size Adaptation

```mermaid
sequenceDiagram
    participant Script as upload_*.py
    participant Cover as covers.py
    participant Spotify_API as Spotify Web API

    Script->>Cover: generate_cover(rng)
    Cover-->>Script: PIL Image (640x640 RGB)
    Script->>Cover: upload_cover(sp, playlist_id, img)

    loop quality in [80, 65, 50, 35]
        Cover->>Cover: Save JPEG to BytesIO at quality
        Cover->>Cover: Base64-encode payload
        alt payload <= 256 KB
            Cover-->>Script: Break (quality used)
        else too large
            Cover->>Cover: Continue loop
        end
    end

    Cover->>Spotify_API: PUT /v1/playlists/{id}/images (base64 JPEG)
    Spotify_API-->>Cover: 200 / 202 / 204
    Cover-->>Script: HTTP status code
```

---

## 7. Deployment View

### 7.1. Local Workstation

The tool runs exclusively on the user's local machine. There is no server component.

```
┌─────────────────────────────────────────────────┐
│                  User Workstation                 │
│                                                   │
│  $ python scripts/export_library.py               │
│  $ python scripts/create_curated_playlists.py     │
│                                                   │
│  ┌─────────────────────────────────────────┐      │
│  │  spotify-curation/                       │      │
│  │  ├── scripts/          (6 CLIs)          │      │
│  │  ├── spotify_curation/ (shared lib)      │      │
│  │  ├── config.py                           │      │
│  │  ├── .env              (credentials)     │      │
│  │  ├── library/          (JSON state)      │      │
│  │  ├── output/covers/    (JPEG files)      │      │
│  │  └── requirements.txt                    │      │
│  └─────────────────────────────────────────┘      │
│                                                   │
│  Python 3.8+ with spotipy, Pillow, NumPy           │
└─────────────────────────────────────────────────┘
```

### 7.2. Required Runtime

| Component | Version |
|-----------|---------|
| Python | 3.8+ |
| spotipy | 2.23+ |
| Pillow | 10.0+ |
| NumPy | 1.24+ |
| requests | 2.31+ |
| python-dotenv | 1.0+ |

### 7.3. External Service

| Service | Authentication | Rate Limit Notes |
|---------|---------------|------------------|
| Spotify Web API | OAuth 2.0 (Authorization Code Flow) | ~10 req/s for search; scripts use 150-500ms delays |
| `PUT /playlists/{id}/images` | OAuth token (ugc-image-upload scope) | 256 KB payload limit per image |

---

## 8. Cross-cutting Concepts

### 8.1. Error Handling

- **Spotify API timeouts**: `recommend_artists.py` implements exponential backoff (2^attempt seconds) for timeout errors
- **Missing credentials**: `config.py` raises `KeyError` on missing `SPOTIFY_CLIENT_ID` / `SPOTIFY_CLIENT_SECRET`
- **Incomplete playlists**: Both `create_*_playlists.py` scripts skip creation if fewer than 5 tracks are selected (prints a WARNING)
- **Unconfigured playlists**: Cover upload scripts skip entries whose `id` starts with `<` (placeholder detection)

### 8.2. State Management

All state is stored as JSON files in `library/`:

| File | Produced By | Consumed By | Format |
|------|-------------|-------------|--------|
| `saved_tracks.json` | `export_library.py` | `recommend_artists.py` | Array of track objects |
| `followed_artists.json` | `export_library.py` | `recommend_artists.py` | Array of artist objects |
| `playlists_summary.json` | `export_library.py` | — | Array of playlist summaries |
| `owned_playlists/*.json` | `export_library.py` | — | Per-playlist track dumps |
| `do_not_include.json` | `export_library.py` | All curation scripts | Flat array of track ID strings |
| `recommendations.json` | `recommend_artists.py` | `create_mood_playlists.py` | Array of artist discovery records |

### 8.3. Reproducibility

- Cover generators use `numpy.random.default_rng(42)` (Series 1) and `numpy.random.default_rng(99)` (Series 2) — deterministic output across runs
- No external data sources beyond Spotify API responses; API changes may affect reproducibility

### 8.4. Security

- Credentials read from `.env` file (gitignored) or environment variables
- OAuth token cached in `library/.cache` (gitignored)
- All API communication over HTTPS
- No secrets in code — `config.py` reads from environment only

### 8.5. i18n

- README and CONTRIBUTING are bilingual (English primary, Portuguese supplementary)
- Inline code comments follow the same pattern (`# action / ação`)
- CLI output is English-only for consistency

---

## 9. Design Decisions

### 9.1. ADR-001: JSON files over a database

| Field | Value |
|-------|-------|
| **Context** | The tool needs to persist library state and checkpoint progress |
| **Decision** | Use flat JSON files in `library/` |
| **Rationale** | Zero additional dependencies; files are human-readable for debugging; checkpoint writes after every artist in `recommend_artists.py` enable safe interruption and resume |
| **Consequences** | No query capability; full-file writes are atomic (`open + write`) but not ACID; scales poorly beyond ~10K tracks |
| **Status** | Accepted |

### 9.2. ADR-002: Script-based CLI over packaged tool

| Field | Value |
|-------|-------|
| **Context** | Six entry points need to be run by the user from a terminal |
| **Decision** | Keep scripts as standalone `.py` files with `sys.path.insert(0, ...)` for imports |
| **Rationale** | Simplest possible setup — clone, `pip install -r requirements.txt`, `python scripts/foo.py`. No packaging, no build step, no `setup.py` |
| **Consequences** | Cannot install via `pip install -e .` or publish to PyPI without additional packaging work; `ruff.toml` suppresses `E402` for `scripts/` |
| **Status** | Accepted |

### 9.3. ADR-003: Procedural cover art over downloaded images

| Field | Value |
|-------|-------|
| **Context** | Playlist covers need to be unique and visually consistent per series/syle |
| **Decision** | Generate covers procedurally with Pillow + NumPy using fixed random seeds |
| **Rationale** | No copyright concerns; fully reproducible; no network calls; lightweight (no ML model); each generator encodes a visual metaphor for the genre/mood |
| **Consequences** | 9 unique generators to maintain; visual diversity depends on generator quality rather than asset curation |
| **Status** | Accepted |

### 9.4. ADR-004: `search(type=track)` over deprecated recommendation endpoints

| Field | Value |
|-------|-------|
| **Context** | Three Spotify API endpoints (`related-artists`, `top-tracks`, `recommendations`) were deprecated in November 2024 |
| **Decision** | Use `search(q="artist:{name}", type="track")` and sort by popularity |
| **Rationale** | Works on all API tiers without Extended Quota Mode; the search endpoint is mature and stable |
| **Consequences** | Cannot discover "related" artists automatically — the user must supply artist lists; search results may include remixes or live versions (mitigated by canonical name deduplication) |
| **Status** | Accepted |

---

## 10. Quality Scenarios

### 10.1. Primary Quality Attributes

| Attribute | Scenario | Current Status |
|-----------|----------|----------------|
| **Reproducibility** | Running `upload_covers.py` twice produces identical JPEG files | Guaranteed — fixed NumPy seed |
| **Determinism** | Same artist list + same library → same playlists | Dependent on Spotify API response order (search results may vary) |
| **Resilience** | Interrupt and restart `recommend_artists.py` mid-way | Supported — per-artist checkpoint writes to `recommendations.json` |
| **Correctness** | A track in `do_not_include.json` never appears in a curated playlist | Verified — blocklist is checked at search time and again at playlist creation |
| **Availability** | Spotify API is unavailable | Fail-fast with clear HTTP error — no queuing or retry beyond timeout backoff |

### 10.2. Test Coverage

| Area | Coverage | Notes |
|------|----------|-------|
| Cover generators core (`lerp_color`, `gradient_bg`) | `tests/test_covers.py` | Unit-tested in [`tests/test_covers.py`](tests/test_covers.py) |
| All 9 cover generators | `tests/test_covers.py` | Verify: 640x640 RGB output, no exceptions, reproducibility |
| Import resolution | CI (`ruff check` + import check) | `.github/workflows/ci.yml` |
| CLI entry points | Manual | Requires live Spotify OAuth session |

---

## 11. Risks and Technical Debt

### 11.1. Technical Debt

| Item | Severity | Description |
|------|----------|-------------|
| `sys.path.insert` pattern | Low | Scripts mutate `sys.path` before imports — fragile with conflicting package names |
| No `pyproject.toml` | Low | Cannot `pip install -e .` or declare optional dependency groups |
| No type hints | Medium | `covers.py` has no function signatures; all scripts lack annotations |
| Manual playlist ID copy | Medium | Users must paste playlist IDs from script output into upload scripts — no automated handoff |
| Hardcoded seeds (42, 99) | Low | Cover reproducibility is intentional; no mechanism for custom seeds |
| OAuth token stored in versioned directory | Low | `.cache` lives in `library/` (gitignored) but a misconfigured `.gitignore` could leak tokens |
| Deprecated endpoint reliance removed | Low | Already migrated to `search` — but upstream Spotify API changes are an ongoing risk |

### 11.2. Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Spotify deprecates `search(type=track)` by popularity | Low | High | Monitor Spotify changelog; fall back to `tracks` endpoint by album |
| Extended Quota Mode becomes mandatory for playlist creation | Low | Medium | Document workarounds; provide PR guidance |
| OAuth cache expires mid-run | Medium | Low | Scripts re-prompt browser on `show_dialog=True` |
| Large library exceeds memory | Low | Low | Tracks capped by Spotify pagination (50-100 per page); JSON files are streaming-friendly |

---

## 12. Glossary

| Term | Definition |
|------|-----------|
| **blocklist / do_not_include** | Set of all track IDs the user already owns — used as a hard filter against repeats |
| **Series 1** | Genre-based manual curation: user defines artist lists per playlist |
| **Series 2** | Mood-based automated discovery: user defines categories + mood tags; tool groups tracks by mood |
| **Spotipy** | Python library for the Spotify Web API (`spotipy` package) |
| **OAuth** | Spotify Authorization Code Flow — requires browser interaction on first run |
| **Procedural cover** | Playlist cover image generated algorithmically (Pillow + NumPy) rather than from a static asset |
| **Mood tag** | String label (`focus`, `energy`, `night`, `journey`) assigned to a discovery artist; determines which mood playlist the artist's tracks populate |
| **Checkpoint** | Periodic save of `recommendations.json` after each artist in `recommend_artists.py` — enables safe interruption and resume |
| **Extended Quota Mode** | Spotify's optional API tier that re-enables deprecated endpoints — not required by this project |
| **Canonical name** | Track name with parenthetical suffixes (live, remaster, etc.) stripped for deduplication |

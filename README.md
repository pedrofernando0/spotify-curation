# spotify-curation

**Build Spotify playlists from your own library data — not from recommendations you didn't ask for.**

[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Spotify Web API](https://img.shields.io/badge/Spotify-Web%20API-1DB954?logo=spotify&logoColor=white)](https://developer.spotify.com/documentation/web-api)

---

> **[English](#english)** · **[Português](#português)**

---

## English

### The idea

Spotify's algorithm optimizes for engagement, not discovery. This tool takes a different approach: it exports everything you already own, blocks those tracks permanently, then searches for music from a curated list of artists you define. Every result is something you don't have yet.

No magic, no ML, no black box — just your taste applied as a filter.

### How it works

```
export_library.py           →  library/saved_tracks.json
                               library/followed_artists.json
                               library/do_not_include.json   ← blocklist

create_curated_playlists.py →  searches Spotify for each artist in your list
                               filters against do_not_include.json
                               creates playlists via Web API

recommend_artists.py        →  filters out artists you already know
                               finds top tracks per discovery artist
                               library/recommendations.json  ← with mood tags

create_mood_playlists.py    →  groups recommendations.json by mood
                               creates one playlist per mood

upload_covers.py / upload_mood_covers.py  →  procedural JPEGs via Pillow
                                              uploaded via PUT /playlists/{id}/images
```

### Cover previews

Nine procedural styles, generated with Pillow + NumPy (fixed seed, fully reproducible):

| Style | Aesthetic |
|---|---|
| `rap` | Dark grid, neon geometry |
| `mpb` | Warm sepia, vinyl rings |
| `rock` | Purple haze, lightning |
| `jazz` | Deep blue, club spotlights |
| `folk` | Watercolor mist, tree silhouettes |
| `concentracao` | Teal circuit board |
| `energia` | Red diagonals, high contrast |
| `noite` | Deep purple, floating particles |
| `viagem` | Sunset landscape, open road |

### Quickstart

**1. Create a Spotify app**

Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard), create an app, and set `http://127.0.0.1:8888/callback` as the Redirect URI.

**2. Configure credentials**

```bash
cp .env.example .env
# Fill in SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Export your library**

```bash
python scripts/export_library.py
```

This creates `library/saved_tracks.json`, `library/followed_artists.json`, and `library/do_not_include.json`. The first run opens a browser for OAuth. The token is cached for subsequent runs.

**5. Create playlists**

```bash
# Series 1 — genre-based (customize artist lists first — see below)
python scripts/create_curated_playlists.py

# Series 2 — mood-based (customize artist lists first)
python scripts/recommend_artists.py
python scripts/create_mood_playlists.py
```

**6. Upload covers (optional)**

```bash
# Paste your playlist IDs into upload_covers.py / upload_mood_covers.py first
python scripts/upload_covers.py
python scripts/upload_mood_covers.py
```

### Customizing for your taste

The scripts ship with small example artist lists. Replace them with artists that are **adjacent to your own profile** — similar to what you love, but absent from your library.

#### Finding good candidates

1. Run `export_library.py` and look at your top artists in `saved_tracks.json`
2. Find artists stylistically close to those — label compilations, music press, Bandcamp tags, etc.
3. Add them to the lists below

#### Series 1 — `scripts/create_curated_playlists.py`

Edit the `PLAYLISTS` array. Each entry is one Spotify playlist:

```python
PLAYLISTS = [
    {
        "name": "Alternative Rock — Discoveries",
        "description": "Post-punk and indie I haven't explored yet.",
        "artists": [
            "Fontaines D.C.",
            "Shame",
            "Squid",
            "Yard Act",
            "DIIV",
        ],
    },
    # ... add more playlists
]
```

#### Series 2 — `scripts/recommend_artists.py`

Edit `DISCOVERY_ARTISTS`. Each artist gets one or more **mood tags** that determine which playlist it ends up in:

```python
DISCOVERY_ARTISTS = {
    "Contemporary Hip-Hop": [
        ("Saba",      ["focus", "night"]),
        ("JID",       ["energy", "night"]),
        ("Noname",    ["focus", "night"]),
    ],
    "Post-Rock": [
        ("Mogwai",    ["focus", "journey"]),
        ("Sigur Rós", ["focus", "journey"]),
    ],
}
```

Available moods (defined in `create_mood_playlists.py`): `focus` · `energy` · `night` · `journey`

### Spotify API notes

Three endpoints are **deprecated since November 2024** and return `403` for apps without Extended Quota Mode:

| Endpoint | Status |
|---|---|
| `GET /artists/{id}/related-artists` | Deprecated |
| `GET /artists/{id}/top-tracks` | Deprecated |
| `GET /recommendations` | Deprecated |

This project uses `search(type=track, q="artist:{name}")` instead — available to all apps, returns popularity scores.

### Project structure

```
spotify-curation/
├── scripts/
│   ├── export_library.py            # Step 1: export your full library
│   ├── create_curated_playlists.py  # Series 1: genre playlists
│   ├── upload_covers.py             # Series 1: procedural covers
│   ├── recommend_artists.py         # Series 2: discover artists by mood
│   ├── create_mood_playlists.py     # Series 2: mood playlists
│   └── upload_mood_covers.py        # Series 2: procedural covers
├── spotify_curation/
│   ├── client.py                    # shared Spotify client factory
│   └── covers.py                    # cover generators + upload utility
├── library/                         # gitignored — generated by export_library.py
├── output/covers/                   # gitignored — generated by upload scripts
├── config.py                        # reads credentials from environment
├── requirements.txt
└── .env.example
```

### Required scopes

The OAuth flow requests these scopes automatically:

| Scope | Used for |
|---|---|
| `user-library-read` | Export liked songs |
| `user-follow-read` | Export followed artists |
| `playlist-read-private` | Export owned playlists |
| `playlist-modify-public` | Create and populate playlists |
| `playlist-modify-private` | Create private playlists |
| `ugc-image-upload` | Upload playlist covers |

### License

MIT — see [LICENSE](LICENSE).

---

## Português

### A ideia

O algoritmo do Spotify otimiza engajamento, não descoberta. Esta ferramenta tem uma abordagem diferente: exporta tudo que você já possui, bloqueia permanentemente essas faixas e busca música de uma lista de artistas que você define. Cada resultado é algo que você ainda não tem.

Sem ML, sem caixa-preta — só o seu gosto aplicado como filtro.

### Como funciona

```
export_library.py           →  library/saved_tracks.json
                               library/followed_artists.json
                               library/do_not_include.json   ← blocklist

create_curated_playlists.py →  busca no Spotify cada artista da sua lista
                               filtra contra do_not_include.json
                               cria playlists via Web API

recommend_artists.py        →  filtra artistas que você já conhece
                               encontra top tracks por artista de descoberta
                               library/recommendations.json  ← com tags de mood

create_mood_playlists.py    →  agrupa recommendations.json por mood
                               cria uma playlist por mood

upload_covers.py / upload_mood_covers.py  →  JPEGs procedurais via Pillow
                                              enviados via PUT /playlists/{id}/images
```

### Início rápido

**1. Criar um app no Spotify**

Acesse o [Spotify Developer Dashboard](https://developer.spotify.com/dashboard), crie um app e adicione `http://127.0.0.1:8888/callback` como Redirect URI.

**2. Configurar credenciais**

```bash
cp .env.example .env
# Preencha SPOTIFY_CLIENT_ID e SPOTIFY_CLIENT_SECRET
```

**3. Instalar dependências**

```bash
pip install -r requirements.txt
```

**4. Exportar sua biblioteca**

```bash
python scripts/export_library.py
```

Cria `library/saved_tracks.json`, `library/followed_artists.json` e `library/do_not_include.json`. Na primeira execução, abre o navegador para OAuth. O token é cacheado para execuções seguintes.

**5. Criar playlists**

```bash
# Série 1 — por gênero (personalize as listas de artistas primeiro)
python scripts/create_curated_playlists.py

# Série 2 — por mood (personalize as listas de artistas primeiro)
python scripts/recommend_artists.py
python scripts/create_mood_playlists.py
```

**6. Subir capas (opcional)**

```bash
# Cole os IDs das suas playlists em upload_covers.py / upload_mood_covers.py antes
python scripts/upload_covers.py
python scripts/upload_mood_covers.py
```

### Personalizando para o seu gosto

Os scripts incluem listas de artistas de exemplo. Substitua-os por artistas **adjacentes ao seu perfil** — similares ao que você ama, mas ausentes da sua biblioteca.

#### Encontrando bons candidatos

1. Rode `export_library.py` e veja seus artistas mais frequentes em `saved_tracks.json`
2. Encontre artistas estilisticamente próximos — compilações de selos, imprensa musical, tags do Bandcamp, etc.
3. Adicione-os nas listas abaixo

#### Série 1 — `scripts/create_curated_playlists.py`

Edite o array `PLAYLISTS`. Cada entrada é uma playlist no Spotify:

```python
PLAYLISTS = [
    {
        "name": "Rock Alternativo — Descobertas",
        "description": "Pós-punk e indie que ainda não explorei.",
        "artists": [
            "Fontaines D.C.",
            "Shame",
            "Squid",
        ],
    },
]
```

#### Série 2 — `scripts/recommend_artists.py`

Edite `DISCOVERY_ARTISTS`. Cada artista recebe uma ou mais **tags de mood** que determinam em qual playlist ele aparece:

```python
DISCOVERY_ARTISTS = {
    "Hip-Hop Contemporâneo": [
        ("Saba",   ["focus", "night"]),
        ("JID",    ["energy", "night"]),
    ],
    "Pós-Rock": [
        ("Mogwai", ["focus", "journey"]),
    ],
}
```

Moods disponíveis (definidos em `create_mood_playlists.py`): `focus` · `energy` · `night` · `journey`

### Notas sobre a API Spotify

Três endpoints estão **depreciados desde novembro de 2024** e retornam `403` para apps sem Extended Quota Mode:

| Endpoint | Status |
|---|---|
| `GET /artists/{id}/related-artists` | Depreciado |
| `GET /artists/{id}/top-tracks` | Depreciado |
| `GET /recommendations` | Depreciado |

Este projeto usa `search(type=track, q="artist:{nome}")` — disponível para todos os apps, retorna scores de popularidade.

### Estrutura do projeto

```
spotify-curation/
├── scripts/
│   ├── export_library.py            # Passo 1: exportar biblioteca completa
│   ├── create_curated_playlists.py  # Série 1: playlists por gênero
│   ├── upload_covers.py             # Série 1: capas procedurais
│   ├── recommend_artists.py         # Série 2: descobrir artistas por mood
│   ├── create_mood_playlists.py     # Série 2: playlists por mood
│   └── upload_mood_covers.py        # Série 2: capas procedurais
├── spotify_curation/
│   ├── client.py                    # factory do cliente Spotify
│   └── covers.py                    # geradores de capa + utilitário de upload
├── library/                         # gitignored — gerado por export_library.py
├── output/covers/                   # gitignored — gerado pelos scripts de capas
├── config.py                        # lê credenciais das variáveis de ambiente
├── requirements.txt
└── .env.example
```

### Licença

MIT — veja [LICENSE](LICENSE).

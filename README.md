# spotify-curation

> Personalized Spotify playlist curation powered by your own library — no algorithm, no black box.

**[English](#english) · [Português](#português)**

---

## English

### What is this?

`spotify-curation` exports your Spotify library and builds curated playlists using **your real listening data as a filter** — every track you've already liked or added is excluded from results, so every playlist is a genuine discovery.

It works entirely through the [Spotify Web API](https://developer.spotify.com/documentation/web-api), bypassing the Spotify MCP tool (which doesn't accept specific track URIs) and the deprecated recommendation endpoints (which require Extended Quota Mode).

### Features

- **Export** your full library: liked songs, followed artists, owned playlists
- **Curate** genre-based playlists (Series 1) with editorial artist lists
- **Discover** mood-based playlists (Series 2) with unknown artists filtered by familiarity
- **Generate** procedural playlist covers via Pillow + NumPy (no design tools needed)
- **Zero repeats** — `do_not_include.json` blocks every track you already own

### Playlists generated

#### Series 1 — Genre-based

| Playlist | Genre |
|---|---|
| Rap Brasileiro — O Que o Algoritmo Escondeu | Brazilian Rap (underground) |
| MPB Fundo do Baú | MPB / Samba (rarities) |
| Rock Alternativo — Além do Que Você Segue | Alternative / Post-punk |
| Jazz & Fusão Contemporânea | Jazz / Contemporary Fusion |
| Voz & Silêncio — Folk e Canção Nua | Folk / Acoustic |

#### Series 2 — Mood-based (discovery only)

| Playlist | Mood |
|---|---|
| Foco Profundo — Instrumental e Flow | Focus / Concentration |
| Ignição — Rock e Rap de Alta Tensão | Energy / High intensity |
| Madrugada — Peso e Densidade | Night / Dense atmosphere |
| Janela Aberta — Pra Rodar | Journey / Open road |

### Setup

**1. Create a Spotify app**

Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard), create an app, and add `http://127.0.0.1:8888/callback` as a Redirect URI.

**2. Clone and configure**

```bash
git clone https://github.com/your-username/spotify-curation.git
cd spotify-curation

cp .env.example .env
# Edit .env with your credentials
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Authenticate**

The first script run opens a browser for OAuth. The token is cached in `library/.cache` for subsequent runs.

### Usage

```bash
# Step 1 — Export your library (run once, then periodically to keep it fresh)
python scripts/export_library.py

# Series 1 — Genre-based playlists
python scripts/create_curated_playlists.py
python scripts/upload_covers.py          # optional: upload procedural covers

# Series 2 — Mood-based playlists (discovery)
python scripts/recommend_artists.py      # generates library/recommendations.json
python scripts/create_mood_playlists.py
python scripts/upload_mood_covers.py     # optional: upload procedural covers
```

> **Tip:** `recommend_artists.py` checkpoints automatically. If it's interrupted, re-running it resumes from where it left off.

### Project structure

```
spotify-curation/
  scripts/
    export_library.py            # export full library → library/*.json
    create_curated_playlists.py  # Series 1: genre playlists
    upload_covers.py             # Series 1: generate + upload covers
    recommend_artists.py         # discover artists → library/recommendations.json
    create_mood_playlists.py     # Series 2: mood playlists
    upload_mood_covers.py        # Series 2: generate + upload covers
  spotify_curation/
    client.py                    # shared Spotify client factory
    covers.py                    # procedural cover generators + upload utility
  library/                       # gitignored — populated by export_library.py
  output/covers/                 # gitignored — populated by upload scripts
  config.py                      # reads credentials from environment
  requirements.txt
  .env.example
```

### API notes

These Spotify endpoints require **Extended Quota Mode** (only granted to approved apps) and return `403` for standard apps:

- `GET /artists/{id}/related-artists` — deprecated Nov 2024
- `GET /artists/{id}/top-tracks` — deprecated Nov 2024
- `GET /recommendations` — deprecated Nov 2024

**Workaround used here:** `search(type=track, q="artist:{name}")` — available to all apps, returns `popularity` in results.

### Customizing for your library

The artist lists in `create_curated_playlists.py` and `recommend_artists.py` are **editorial choices** made for one specific listener profile. To adapt them to your own library:

1. Run `export_library.py` to populate `library/saved_tracks.json` and `library/followed_artists.json`
2. Edit the `PLAYLISTS` and `DISCOVERY_ARTISTS` dictionaries with artists relevant to your profile
3. The filtering logic (`do_not_include.json`, followed-artist exclusion, 3+ liked tracks threshold) works automatically for any artist list

### License

MIT — see [LICENSE](LICENSE).

---

## Português

### O que é isso?

`spotify-curation` exporta sua biblioteca do Spotify e cria playlists curadas usando **seus dados reais de escuta como filtro** — toda música que você já curtiu ou adicionou é excluída dos resultados, então cada playlist é uma descoberta genuína.

Funciona inteiramente pela [Spotify Web API](https://developer.spotify.com/documentation/web-api), contornando o MCP do Spotify (que não aceita URIs de tracks específicos) e os endpoints de recomendação depreciados (que exigem Extended Quota Mode).

### Funcionalidades

- **Exporta** sua biblioteca completa: músicas curtidas, artistas seguidos, playlists próprias
- **Cria** playlists por gênero (Série 1) com listas editoriais de artistas
- **Descobre** playlists por mood (Série 2) com artistas desconhecidos filtrados por familiaridade
- **Gera** capas procedurais via Pillow + NumPy (sem ferramentas de design)
- **Zero repetições** — `do_not_include.json` bloqueia toda track que você já tem

### Playlists geradas

#### Série 1 — Por gênero

| Playlist | Gênero |
|---|---|
| Rap Brasileiro — O Que o Algoritmo Escondeu | Rap BR (underground) |
| MPB Fundo do Baú | MPB / Samba (raridades) |
| Rock Alternativo — Além do Que Você Segue | Alternativo / Pós-punk |
| Jazz & Fusão Contemporânea | Jazz / Fusão contemporânea |
| Voz & Silêncio — Folk e Canção Nua | Folk / Acústico |

#### Série 2 — Por mood (descoberta pura)

| Playlist | Mood |
|---|---|
| Foco Profundo — Instrumental e Flow | Foco / Concentração |
| Ignição — Rock e Rap de Alta Tensão | Energia / Alta intensidade |
| Madrugada — Peso e Densidade | Noite / Atmosfera densa |
| Janela Aberta — Pra Rodar | Viagem / Estrada aberta |

### Setup

**1. Criar um app no Spotify**

Acesse o [Spotify Developer Dashboard](https://developer.spotify.com/dashboard), crie um app e adicione `http://127.0.0.1:8888/callback` como Redirect URI.

**2. Clonar e configurar**

```bash
git clone https://github.com/seu-usuario/spotify-curation.git
cd spotify-curation

cp .env.example .env
# Edite .env com suas credenciais
```

**3. Instalar dependências**

```bash
pip install -r requirements.txt
```

**4. Autenticar**

Na primeira execução, um navegador abrirá para o fluxo OAuth. O token é cacheado em `library/.cache` para execuções subsequentes.

### Como usar

```bash
# Passo 1 — Exportar sua biblioteca (rodar uma vez, depois periodicamente)
python scripts/export_library.py

# Série 1 — Playlists por gênero
python scripts/create_curated_playlists.py
python scripts/upload_covers.py          # opcional: sobe capas procedurais

# Série 2 — Playlists por mood (descoberta)
python scripts/recommend_artists.py      # gera library/recommendations.json
python scripts/create_mood_playlists.py
python scripts/upload_mood_covers.py     # opcional: sobe capas procedurais
```

> **Dica:** `recommend_artists.py` faz checkpoint automático. Se for interrompido, basta re-executar que ele retoma de onde parou.

### Estrutura do projeto

```
spotify-curation/
  scripts/
    export_library.py            # exporta biblioteca → library/*.json
    create_curated_playlists.py  # Série 1: playlists por gênero
    upload_covers.py             # Série 1: gera + sobe capas
    recommend_artists.py         # descobre artistas → library/recommendations.json
    create_mood_playlists.py     # Série 2: playlists por mood
    upload_mood_covers.py        # Série 2: gera + sobe capas
  spotify_curation/
    client.py                    # factory do cliente Spotify compartilhado
    covers.py                    # geradores de capa procedural + utilitário de upload
  library/                       # gitignored — populado por export_library.py
  output/covers/                 # gitignored — populado pelos scripts de capas
  config.py                      # lê credenciais das variáveis de ambiente
  requirements.txt
  .env.example
```

### Notas sobre a API

Estes endpoints do Spotify exigem **Extended Quota Mode** (concedido só a apps aprovados) e retornam `403` para apps padrão:

- `GET /artists/{id}/related-artists` — depreciado Nov 2024
- `GET /artists/{id}/top-tracks` — depreciado Nov 2024
- `GET /recommendations` — depreciado Nov 2024

**Workaround usado aqui:** `search(type=track, q="artist:{nome}")` — disponível para todos os apps, retorna `popularity` nos resultados.

### Adaptando para sua biblioteca

As listas de artistas em `create_curated_playlists.py` e `recommend_artists.py` são **escolhas editoriais** feitas para um perfil específico de ouvinte. Para adaptar ao seu:

1. Rode `export_library.py` para popular `library/saved_tracks.json` e `library/followed_artists.json`
2. Edite os dicionários `PLAYLISTS` e `DISCOVERY_ARTISTS` com artistas relevantes ao seu perfil
3. A lógica de filtro (`do_not_include.json`, exclusão de artistas seguidos, limiar de 3+ tracks curtidas) funciona automaticamente para qualquer lista

### Licença

MIT — veja [LICENSE](LICENSE).

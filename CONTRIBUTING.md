# Contributing

Contributions are welcome. This is a small focused tool — keep additions scoped to the core use case.

## Ways to contribute

- **New cover styles** — add a generator function to `spotify_curation/covers.py` and expose it in `SERIES1_GENERATORS` or `SERIES2_GENERATORS`
- **Bug fixes** — open an issue first if the fix is non-trivial
- **Spotify API workarounds** — the deprecated endpoint situation evolves; PRs that update the approach are especially useful
- **Documentation** — improvements to the README, inline comments, or examples

## Setup

```bash
git clone https://github.com/pedrofernando0/spotify-curation.git
cd spotify-curation
pip install -r requirements.txt ruff
cp .env.example .env
# fill in your Spotify credentials
```

## Before opening a PR

```bash
ruff check .
```

No test suite yet — manual verification against a real Spotify account is the current standard.

## Scope

This project intentionally has **no runtime dependencies beyond spotipy, Pillow, NumPy, and requests**. Please don't add heavyweight frameworks or new mandatory dependencies.

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from config import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, SCOPES, LIBRARY_DIR


def get_spotify(show_dialog: bool = False) -> spotipy.Spotify:
    return spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
            scope=SCOPES,
            cache_path=os.path.join(LIBRARY_DIR, ".cache"),
            show_dialog=show_dialog,
        ),
        requests_timeout=15,
    )

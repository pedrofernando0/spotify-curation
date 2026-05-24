import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
LIBRARY_DIR = os.path.join(BASE_DIR, "library")
COVERS_DIR  = os.path.join(BASE_DIR, "output", "covers")

CLIENT_ID     = os.environ["SPOTIFY_CLIENT_ID"]
CLIENT_SECRET = os.environ["SPOTIFY_CLIENT_SECRET"]
REDIRECT_URI  = os.environ.get("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback")

SCOPES = " ".join([
    "user-library-read",
    "user-follow-read",
    "playlist-read-private",
    "playlist-read-collaborative",
    "playlist-modify-public",
    "playlist-modify-private",
    "ugc-image-upload",
])

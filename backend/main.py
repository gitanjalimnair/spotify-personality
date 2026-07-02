import os
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = "https://spotify-personality.onrender.com/callback"

app = FastAPI()

# Enable CORS so your Next.js frontend can communicate with this backend cleanly
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://spotify-personality-chi.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/login")
def login():
    """Redirects the user to Spotify's official authorization page."""
    scope = "user-top-read user-read-private user-read-email"
    spotify_auth_url = (
        f"https://accounts.spotify.com/authorize?"
        f"client_id={CLIENT_ID}&"
        f"response_type=code&"
        f"redirect_uri={REDIRECT_URI}&"
        f"scope={scope}"
    )
    return RedirectResponse(url=spotify_auth_url)

@app.get("/callback")
def callback(code: str = None, error: str = None):
    """Catches the code from Spotify, exchanges it for a token, and forwards it to frontend."""
    if error:
        return RedirectResponse(url=f"https://spotify-personality-chi.vercel.app/?error={error}")
    
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code missing")

    # Exchange the authorization code for an Access Token
    token_url = "https://accounts.spotify.com/api/token"
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    
    response = requests.post(token_url, data=payload, headers=headers)
    
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Failed to retrieve token from Spotify")
        
    token_data = response.json()
    access_token = token_data.get("access_token")

    # FIX: Bounces the browser back to your live Vercel app instead of localhost!
    return RedirectResponse(url=f"https://spotify-personality-chi.vercel.app/?token={access_token}")

@app.get("/api/profile")
def get_profile(token: str):
    """Fetches user data and generates a mock archetype profile based on music metrics."""
    if not token:
        raise HTTPException(status_code=400, detail="Token parameter is required")

    headers = {"Authorization": f"Bearer {token}"}
    
    # Try fetching real data from Spotify
    try:
        top_tracks_response = requests.get(
            "https://api.spotify.com/v1/me/top/tracks?limit=5&time_range=medium_term", 
            headers=headers
        )
        
        tracks = []
        if top_tracks_response.status_code == 200:
            for item in top_tracks_response.json().get("items", []):
                tracks.append({
                    "name": item.get("name"),
                    "artist": item.get("artists")[0].get("name") if item.get("artists") else "Unknown Artist"
                })
        
        # Fallback items if their new Spotify profile has no listening history yet
        if not tracks:
            tracks = [
                {"name": "Blinding Lights", "artist": "The Weeknd"},
                {"name": "Stay", "artist": "The Kid LAROI & Justin Bieber"},
                {"name": "Good 4 U", "artist": "Olivia Rodrigo"}
            ]

        # Generate a creative archetype structure to return to the dashboard interface
        return {
            "personality": "The Nocturnal Sonic Alchemist",
            "description": "Your rotation reveals a deep affinity for atmospheric soundscapes paired with high-energy rhythms. You use music as an emotional conduit, blending nighttime reflective vibes with heavy synth basslines.",
            "stats": {
                "danceability": 74,
                "energy": 82
            },
            "top_tracks": tracks
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
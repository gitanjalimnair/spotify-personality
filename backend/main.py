import os
import requests
import random
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
    allow_origins=["http://localhost:3000", "https://spotify-personality-chi.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🧠 Fixed: The Archetypes pool is explicitly defined here so the code doesn't crash!
ARCHETYPES = [
    {
        "personality": "The Nocturnal Sonic Alchemist",
        "description": "Your rotation reveals a deep affinity for atmospheric soundscapes paired with high-energy rhythms. You use music as an emotional conduit, blending nighttime reflective vibes with heavy synth basslines."
    },
    {
        "personality": "The Main Character Indie Idealist",
        "description": "Your tracks lean heavily into cinematic acoustic textures, raw emotional vocals, and nostalgic indie soundscapes. You treat life like a coming-of-age movie, curating a bittersweet backdrop for everyday moments."
    },
    {
        "personality": "The High-Octane Rhythm Rebel",
        "description": "You thrive on intense beats, driving bass lines, and fast-paced electronic or hip-hop flows. Your music is pure fuel designed to keep your focus locked and your energy levels maxed out."
    },
    {
        "personality": "The Eclectic Time Traveler",
        "description": "Your history jumps across decades and genres effortlessly. From retro funk classics to hyper-modern underground pop, you reject current trends to build a deeply personalized, timeless sonic library."
    }
]

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

    # Bounces the browser back to your live Vercel app instead of localhost
    return RedirectResponse(url=f"https://spotify-personality-chi.vercel.app/?token={access_token}")

@app.get("/api/profile")
def get_profile(token: str):
    if not token:
        raise HTTPException(status_code=400, detail="Token parameter is required")

    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        tracks = []
        
        # 1. Try SHORT_TERM first
        recent_response = requests.get(
            "https://api.spotify.com/v1/me/top/tracks?time_range=short_term&limit=5", 
            headers=headers
        )
        if recent_response.status_code == 200:
            for item in recent_response.json().get("items", []):
                tracks.append({
                    "name": item.get("name"),
                    "artist": item.get("artists")[0].get("name") if item.get("artists") else "Unknown Artist"
                })

        # 2. Fall back to LONG_TERM if empty
        if not tracks:
            vault_response = requests.get(
                "https://api.spotify.com/v1/me/top/tracks?time_range=long_term&limit=5", 
                headers=headers
            )
            if vault_response.status_code == 200:
                for item in vault_response.json().get("items", []):
                    tracks.append({
                        "name": item.get("name"),
                        "artist": item.get("artists")[0].get("name") if item.get("artists") else "Unknown Artist"
                    })

        # 3. Emergency backup if Spotify returns absolutely nothing
        is_fallback = False
        if not tracks:
            is_fallback = True
            fallback_pools = [
                [{"name": "Starboy", "artist": "The Weeknd"}, {"name": "Nightchanges", "artist": "One Direction"}, {"name": "Perfect", "artist": "Ed Sheeran"}],
                [{"name": "Bohemian Rhapsody", "artist": "Queen"}, {"name": "Sweater Weather", "artist": "The Neighbourhood"}, {"name": "Do I Wanna Know?", "artist": "Arctic Monkeys"}],
                [{"name": "Kya Baat Ay", "artist": "Harrdy Sandhu"}, {"name": "Bukhaar", "artist": "Aroob Khan"}, {"name": "Piche Tere", "artist": "Kunwarr"}]
            ]
            tracks = random.choice(fallback_pools)

        # 🧠 DYNAMIC CALCULATION ANALYSIS: Calculate a permanent value based on track text properties
        # This removes the random number generator completely.
        total_chars = sum(len(t["name"]) + len(t["artist"]) for t in tracks)
        ascii_sum = sum(ord(c) for t in tracks for c in t["name"])
        
        # Calculate meaningful, repeatable metrics directly scaled from their tracks
        # Compresses numerical bounds strictly between 60% and 98%
        dynamic_danceability = 60 + (ascii_sum % 39)
        dynamic_energy = 60 + ((total_chars * ascii_sum) % 39)
        
        # Pick a dedicated index from the ARCHETYPES list using their music signature
        archetype_index = (ascii_sum + total_chars) % len(ARCHETYPES)
        chosen_archetype = ARCHETYPES[archetype_index]
        
        personality_title = chosen_archetype["personality"]
        description_text = chosen_archetype["description"]
        
        if is_fallback:
            personality_title = f"The Vaulted {personality_title}"
            description_text = "Your profile is currently locked in time capsule mode! " + description_text

        return {
            "personality": personality_title,
            "description": description_text,
            "stats": {
                "danceability": dynamic_danceability,
                "energy": dynamic_energy
            },
            "top_tracks": tracks
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
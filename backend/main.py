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
    if not token:
        raise HTTPException(status_code=400, detail="Token parameter is required")

    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        tracks = []
        
        # Step 1: Try SHORT_TERM first (Last 4 weeks) for active, recent data
        recent_response = requests.get(
            "https://api.spotify.com/v1/me/top/tracks?limit=5&time_range=short_term", 
            headers=headers
        )
        if recent_response.status_code == 200:
            for item in recent_response.json().get("items", []):
                tracks.append({
                    "name": item.get("name"),
                    "artist": item.get("artists")[0].get("name") if item.get("artists") else "Unknown Artist"
                })

        # Step 2: Fall back to LONG_TERM if they haven't used Spotify recently
        if not tracks:
            vault_response = requests.get(
                "https://api.spotify.com/v1/me/top/tracks?limit=5&time_range=long_term", 
                headers=headers
            )
            if vault_response.status_code == 200:
                for item in vault_response.json().get("items", []):
                    tracks.append({
                        "name": item.get("name"),
                        "artist": item.get("artists")[0].get("name") if item.get("artists") else "Unknown Artist"
                    })

        # Step 3: Emergency randomized pool if their account is completely blank
        is_fallback = False
        if not tracks:
            is_fallback = True
            fallback_pools = [
                [{"name": "Starboy", "artist": "The Weeknd"}, {"name": "Nightchanges", "artist": "One Direction"}, {"name": "Perfect", "artist": "Ed Sheeran"}],
                [{"name": "Bohemian Rhapsody", "artist": "Queen"}, {"name": "Sweater Weather", "artist": "The Neighbourhood"}, {"name": "Do I Wanna Know?", "artist": "Arctic Monkeys"}],
                [{"name": "Kya Baat Ay", "artist": "Harrdy Sandhu"}, {"name": "Bukhaar", "artist": "Aroob Khan"}, {"name": "Piche Tere", "artist": "Kunwarr"}]
            ]
            tracks = random.choice(fallback_pools)

        # 🧠 THE FIX: Generate a unique seed based on the letters of their specific tracks!
        # This guarantees that their track list mathematically locks in their unique score.
        track_seed = sum(ord(char) for track in tracks for char in track["name"])
        random.seed(track_seed) 
        
        chosen_archetype = random.choice(ARCHETYPES)
        personality_title = chosen_archetype["personality"]
        description_text = chosen_archetype["description"]
        
        if is_fallback:
            personality_title = f"The Vaulted {personality_title}"
            description_text = "Your profile is currently locked in time capsule mode! " + description_text

        # Generate unique metrics anchored to their personal track seed
        dynamic_danceability = random.randint(65, 95)
        dynamic_energy = random.randint(60, 95)
        
        # Reset seed so subsequent requests from other users stay random
        random.seed() 

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
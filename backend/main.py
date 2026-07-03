import os
import json
import requests
import random
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables from .env file
load_dotenv()

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = "https://spotify-personality.onrender.com/callback"

# Initialize the Gemini Client using the official SDK
genai_client = genai.Client()

app = FastAPI()

# Enable CORS so your Next.js frontend can communicate with this backend cleanly
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://spotify-personality-chi.vercel.app"],
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

    # Bounces the browser back to your live Vercel app
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

        # 🧠 DYNAMIC AI ANALYSIS ENGINE
        # Format track names and artists safely into a summary string for Gemini
        tracks_summary = ", ".join([f"'{t['name']}' by {t['artist']}" for t in tracks])
        
        prompt = f"""
        Analyze this user's top Spotify tracks: {tracks_summary}.
        Based on the genre, cultural context, language, tempo, and vibe of these specific songs, generate a deeply personalized musical profile.
        
        Return your response strictly as a JSON object matching this schema:
        {{
            "personality": "A creative, highly specific 3-5 word title for their musical archetype (e.g., 'The Late-Night Desi Dreamer' or 'The High-Octane Bass Rebel')",
            "description": "A meaningful, beautifully written 2-3 sentence paragraph describing their unique personality and listening traits based on these exact songs.",
            "stats": {{
                "danceability": <a logically calculated integer between 40 and 99 representing the rhythm/movement factor of this mix>,
                "energy": <a logically calculated integer between 40 and 99 representing the sound intensity/pace factor>
            }}
        }}
        """

        # Call the Gemini model using structured JSON output configurations
        # Make the structured AI call
        ai_response = genai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )

        # Clean any potential markdown wrappers from the text before parsing
        clean_text = ai_response.text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        clean_text = clean_text.strip()

        # Convert the text block into standard Python formats safely
        profile_data = json.loads(clean_text)

        personality_title = profile_data.get("personality", "The Sonic Explorer")
        description_text = profile_data.get("description", "Your musical taste spans diverse emotional spaces.")
        stats = profile_data.get("stats", {"danceability": 75, "energy": 75})

        if is_fallback:
            personality_title = f"The Vaulted {personality_title}"
            description_text = "Your profile is currently locked in time capsule mode! " + description_text

        return {
            "personality": personality_title,
            "description": description_text,
            "stats": stats,
            "top_tracks": tracks
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
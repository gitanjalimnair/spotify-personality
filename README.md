# 🎵 VibeCheck

Live Demo: [spotify-personality-chi.vercel.app](https://spotify-personality-chi.vercel.app/)

An AI-driven, full-stack web application that securely analyzes your real Spotify rotation statistics to generate a personalized musical soul archetype dashboard.

---

## 🚀 Features

- Connect your real Spotify account securely
- AI analyzes audio features and listening habits
- Generates structured personality layouts:
  - 🔍 Musical Archetype
  - 💭 Behavioral Summary
  - 📊 Sonic Attributes (Danceability & Energy)
  - 🎧 Current Heavy Rotation List

---

## 🧠 How It Works

1. User authenticates via Spotify OAuth 2.0
2. Authorization code is processed by the FastAPI backend
3. Secure token is returned to the Next.js frontend to render your music archetype

---

## 🖼 Example

Input: Spotify User Listening History

Output:
- **Archetype:** The Nocturnal Sonic Alchemist
- **Metrics:** 74% Danceability | 82% Energy Factor
- **Summary:** Deep affinity for atmospheric soundscapes and high-energy synth basslines.

### Live Application Render
<img width="1600" height="838" alt="image" src="https://github.com/user-attachments/assets/0df2393f-df11-43ad-ab20-73a0cf430de6" />
<img width="1918" height="1006" alt="image" src="https://github.com/user-attachments/assets/a8ab0d2d-b03e-4902-a78a-72b0784b018b" />


---

## 🛠 Tech Stack

- Next.js
- FastAPI (Python)
- Spotify API
- Tailwind CSS
- Vercel & Render


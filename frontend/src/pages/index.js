import { useState, useEffect } from 'react';
import axios from 'axios';

export default function Home() {
  const [token, setToken] = useState(null);
  const [profileData, setProfileData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const tokenParam = urlParams.get('token');
    if (tokenParam) {
      setToken(tokenParam);
      fetchMusicProfile(tokenParam);
    }
  }, []);

  const handleLogin = () => {
    window.location.href = 'http://127.0.0.1:8000/login';
  };

  const fetchMusicProfile = async (accessToken) => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`http://127.0.0.1:8000/api/profile?token=${accessToken}`);
      setProfileData(response.data);
    } catch (err) {
      setError('Failed to fetch your music soul archetype.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center justify-center p-6 font-sans">
      <main className="max-w-md w-full text-center">
        
        {!token && (
          <div className="space-y-6 bg-slate-900 border border-slate-800 p-8 rounded-2xl shadow-xl">
            <h1 className="text-4xl font-extrabold tracking-tight bg-gradient-to-r from-emerald-400 to-teal-500 bg-clip-text text-transparent">
              VibeCheck
            </h1>
            <p className="text-slate-400 text-sm">
              Discover your true musical personality archetype pulled directly from your real Spotify rotation data.
            </p>
            <button
              onClick={handleLogin}
              className="w-full py-3.5 px-4 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold rounded-xl transition duration-200 cursor-pointer shadow-lg shadow-emerald-500/20"
            >
              Connect Spotify Account
            </button>
          </div>
        )}

        {loading && (
          <div className="animate-pulse space-y-4">
            <div className="h-8 bg-slate-800 rounded w-3/4 mx-auto"></div>
            <div className="h-24 bg-slate-800 rounded-2xl"></div>
          </div>
        )}

        {error && (
          <div className="bg-red-900/20 border border-red-500/30 text-red-400 p-4 rounded-xl text-sm">
            {error}
          </div>
        )}

        {profileData && !loading && (
          <div className="space-y-6 bg-gradient-to-b from-slate-900 to-slate-950 border border-slate-800 p-8 rounded-2xl shadow-2xl text-left">
            <div>
              <span className="text-xs font-semibold tracking-widest text-emerald-400 uppercase">Your Archetype</span>
              <h2 className="text-3xl font-black text-white mt-1">{profileData.personality}</h2>
            </div>
            
            <p className="text-slate-400 text-sm leading-relaxed border-l-2 border-emerald-500 pl-4 py-1">
              {profileData.description}
            </p>

            <div className="space-y-4 pt-2">
              <div>
                <div className="flex justify-between text-xs text-slate-400 font-medium mb-1">
                  <span>Danceability</span>
                  <span className="text-emerald-400 font-bold">{profileData.stats.danceability}%</span>
                </div>
                <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div className="bg-emerald-400 h-full rounded-full" style={{ width: `${profileData.stats.danceability}%` }}></div>
                </div>
              </div>

              <div>
                <div className="flex justify-between text-xs text-slate-400 font-medium mb-1">
                  <span>Energy Factor</span>
                  <span className="text-teal-400 font-bold">{profileData.stats.energy}%</span>
                </div>
                <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div className="bg-teal-400 h-full rounded-full" style={{ width: `${profileData.stats.energy}%` }}></div>
                </div>
              </div>
            </div>

            <div className="pt-4 border-t border-slate-800/60">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">Current Heavy Rotation</h3>
              <ul className="space-y-2.5">
                {profileData.top_tracks.map((track, i) => (
                  <li key={i} className="flex items-center space-x-3 text-sm bg-slate-900/50 p-2.5 rounded-lg border border-slate-800/40">
                    <span className="text-xs font-bold text-slate-600 w-4">{i + 1}</span>
                    <div className="truncate">
                      <p className="font-semibold text-slate-200 truncate">{track.name}</p>
                      <p className="text-xs text-slate-400 truncate">{track.artist}</p>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
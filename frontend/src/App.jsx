import { useState } from "react";
import Uploader from "./components/Uploader";
import MoodSelector from "./components/MoodSelector";
import Results from "./components/Results";
import SessionRoom from "./components/SessionRoom";
import "./index.css";

const API = "http://localhost:8000/api";
const MY_USER_ID = Math.random().toString(36).slice(2, 10);

function getJoinCodeFromUrl() {
  return new URLSearchParams(window.location.search).get("join") || "";
}

export default function App() {
  const initialCode = getJoinCodeFromUrl();
  const [screen, setScreen] = useState(initialCode ? "session" : "home");
  const [sessionCode, setSessionCode] = useState(initialCode);
  const [joinInput, setJoinInput] = useState("");
  const [files, setFiles] = useState([]);
  const [mood, setMood] = useState("");
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  function reset() {
    setFiles([]);
    setMood("");
    setResults(null);
    setError(null);
    setSessionCode("");
    setJoinInput("");
    setScreen("home");
    window.history.replaceState({}, "", "/");
  }

  async function handleCreateSession() {
    setError(null);
    try {
      const res = await fetch(API + "/session/create", { method: "POST" });
      const data = await res.json();
      setSessionCode(data.code);
      setScreen("session");
    } catch (e) {
      setError("Impossible de creer la session, verifie que le backend tourne.");
    }
  }

  function handleJoinSession() {
    if (joinInput.length !== 6) return;
    setSessionCode(joinInput.toUpperCase());
    setScreen("session");
  }

  async function handleSoloSubmit() {
    if (files.length === 0 || !mood.trim()) return;
    setLoading(true);
    setError(null);
    const form = new FormData();
    files.forEach(function(f) { form.append("files", f); });
    form.append("mood", mood);
    form.append("top_n", "5");
    try {
      const res = await fetch(API + "/recommend", { method: "POST", body: form });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Erreur serveur");
      setResults(data);
      setScreen("results");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  if (screen === "results" && results) {
    return (
      <div className="app">
        <header className="hero"><h1>Filmatch</h1></header>
        <main className="main">
          <Results data={results} />
          <button className="btn-secondary" onClick={reset}>Nouvelle recherche</button>
        </main>
      </div>
    );
  }

  if (screen === "session") {
    return (
      <div className="app">
        <header className="hero"><h1>Filmatch</h1><p>Session groupe</p></header>
        <main className="main">
          <SessionRoom
            code={sessionCode}
            myUserId={MY_USER_ID}
            onResults={function(data) { setResults(data); setScreen("results"); }}
            onBack={reset}
          />
        </main>
      </div>
    );
  }

  if (screen === "solo") {
    return (
      <div className="app">
        <header className="hero">
          <h1>Filmatch</h1>
          <p>Mode solo</p>
        </header>
        <main className="main">
          <div className="card">
            <Uploader files={files} setFiles={setFiles} />
            <MoodSelector mood={mood} setMood={setMood} />
            <button
              className="btn-primary"
              onClick={handleSoloSubmit}
              disabled={files.length === 0 || !mood.trim() || loading}
            >
              {loading ? "Analyse en cours..." : "Trouver mes films"}
            </button>
            {loading && <p className="hint">Analyse en cours (30-60s)...</p>}
            {error && <p className="error">{error}</p>}
            <button className="back-btn-bottom" onClick={reset}>Retour</button>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="hero">
        <h1>Filmatch</h1>
        <p>Trouve le film parfait pour toi ou ton groupe</p>
      </header>
      <main className="main">
        <div className="mode-grid">
          <button className="mode-card" onClick={function() { setScreen("solo"); }}>
            <span className="mode-icon">Solo</span>
            <h2>Regarder seul</h2>
            <p>Recommandations personnalisees pour toi</p>
          </button>
          <button className="mode-card" onClick={handleCreateSession}>
            <span className="mode-icon">Groupe</span>
            <h2>Regarder en groupe</h2>
            <p>Invite tes amis et trouvez un film ensemble</p>
          </button>
        </div>
        <div className="join-section">
          <p className="label">Tu as un code d invitation ?</p>
          <div className="join-row">
            <input
              className="input join-input"
              placeholder="Ex: ABC123"
              value={joinInput}
              onChange={function(e) { setJoinInput(e.target.value.toUpperCase()); }}
              maxLength={6}
            />
            <button
              className="btn-primary"
              disabled={joinInput.length !== 6}
              onClick={handleJoinSession}
            >
              Rejoindre
            </button>
          </div>
        </div>
        {error && <p className="error">{error}</p>}
      </main>
    </div>
  );
}

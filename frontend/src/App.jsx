import { useState } from "react";
import Uploader from "./components/Uploader";
import MoodSelector from "./components/MoodSelector";
import Results from "./components/Results";
import "./index.css";

const API = "http://localhost:8000/api";

export default function App() {
  const [files, setFiles] = useState([]);
  const [mood, setMood] = useState("");
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  async function handleSubmit() {
    if (files.length === 0 || !mood.trim()) return;
    setLoading(true);
    setError(null);
    setResults(null);

    const form = new FormData();
    files.forEach(function(f) { form.append("files", f); });
    form.append("mood", mood);
    form.append("top_n", "5");

    try {
      const res = await fetch(API + "/recommend", { method: "POST", body: form });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Erreur serveur");
      setResults(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app">
      <header className="hero">
        <h1>Filmatch</h1>
        <p>Importe vos historiques Letterboxd et dites-nous votre mood.</p>
      </header>
      <main className="main">
        <div className="card">
          <Uploader files={files} setFiles={setFiles} />
          <MoodSelector mood={mood} setMood={setMood} />
          <button
            className="btn-primary"
            onClick={handleSubmit}
            disabled={files.length === 0 || !mood.trim() || loading}
          >
            {loading ? "Analyse en cours..." : "Trouver nos films"}
          </button>
          {loading && (
            <p className="hint">Le moteur analyse les historiques et cherche les meilleurs films...</p>
          )}
          {error && <p className="error">{error}</p>}
        </div>
        {results && <Results data={results} />}
      </main>
    </div>
  );
}

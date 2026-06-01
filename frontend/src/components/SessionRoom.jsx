import { useState, useEffect } from "react";
import { useDropzone } from "react-dropzone";
import JSZip from "jszip";
import MoodSelector from "./MoodSelector";

const API = "http://localhost:8000/api";

async function extractFromZip(zipFile) {
  const zip = await JSZip.loadAsync(zipFile);
  const f = zip.file("ratings.csv");
  if (!f) throw new Error("ratings.csv introuvable dans le zip");
  const blob = await f.async("blob");
  return new File([blob], "ratings.csv", { type: "text/csv" });
}

export default function SessionRoom({ code, myUserId, onResults, onBack }) {
  const [status, setStatus] = useState(null);
  const [uploaded, setUploaded] = useState(false);
  const [movieCount, setMovieCount] = useState(0);
  const [file, setFile] = useState(null);
  const [mood, setMood] = useState("");
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);

  const shareLink = window.location.origin + "?join=" + code;
  const qrUrl = "https://api.qrserver.com/v1/create-qr-code/?size=120x120&data=" + encodeURIComponent(shareLink);

  useEffect(function() {
    async function poll() {
      try {
        const res = await fetch(API + "/session/" + code + "/status");
        if (!res.ok) return;
        const data = await res.json();
        setStatus(data);
        if (data.status === "done") {
          const rRes = await fetch(API + "/session/" + code + "/results");
          const rData = await rRes.json();
          if (rData.recommendations) onResults(rData);
        }
      } catch (e) {}
    }
    poll();
    const iv = setInterval(poll, 3000);
    return function() { clearInterval(iv); };
  }, [code]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: async function(accepted) {
      if (!accepted.length) return;
      let f = accepted[0];
      if (f.name.toLowerCase().endsWith(".zip")) {
        try { f = await extractFromZip(f); } catch (e) { setError(e.message); return; }
      }
      setFile(f);
      setError(null);
    },
    accept: { "text/csv": [".csv"], "application/zip": [".zip"], "application/x-zip-compressed": [".zip"] },
    maxFiles: 1,
  });

  async function handleUpload() {
    if (!file) return;
    setUploading(true);
    setError(null);
    const form = new FormData();
    form.append("file", file);
    form.append("user_id", myUserId);
    try {
      const res = await fetch(API + "/session/" + code + "/upload", { method: "POST", body: form });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Erreur upload");
      setUploaded(true);
      setMovieCount(data.movies_parsed);
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  }

  async function handleStart() {
    if (!mood.trim()) return;
    setLoading(true);
    setError(null);
    const form = new FormData();
    form.append("mood", mood);
    try {
      const res = await fetch(API + "/session/" + code + "/start", { method: "POST", body: form });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Erreur lancement");
      onResults(data);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  }

  function copyLink() {
    navigator.clipboard.writeText(shareLink).then(function() {
      setCopied(true);
      setTimeout(function() { setCopied(false); }, 2000);
    });
  }

  const userCount = status ? status.user_count : 0;
  const isComputing = status && status.status === "computing";

  return (
    <div className="card">
      <div className="session-header">
        <div className="session-code-block">
          <span className="label">Code de session</span>
          <span className="session-code">{code}</span>
          <span className="user-count">{userCount} utilisateur{userCount > 1 ? "s" : ""} connecte{userCount > 1 ? "s" : ""}</span>
        </div>
        <img src={qrUrl} alt="QR code" className="qr-code" />
      </div>

      <button className="btn-copy" onClick={copyLink}>
        {copied ? "Lien copie !" : "Copier le lien d invitation"}
      </button>

      <div className="section">
        <label className="label">Ton historique Letterboxd</label>
        {!uploaded ? (
          <>
            <button
              className="btn-letterboxd"
              onClick={function() { window.open("https://letterboxd.com/data/export/", "_blank"); }}
              type="button"
            >
              Ouvrir mon Letterboxd Export
            </button>
            <div {...getRootProps()} className={"dropzone" + (isDragActive ? " active" : "") + (file ? " done" : "")}>
              <input {...getInputProps()} />
              {file ? (
                <p>OK : {file.name}</p>
              ) : (
                <p>Glisse ton .zip ou ratings.csv ici</p>
              )}
            </div>
            {file && (
              <button className="btn-primary" onClick={handleUpload} disabled={uploading}>
                {uploading ? "Envoi en cours..." : "Valider mon historique"}
              </button>
            )}
          </>
        ) : (
          <div className="upload-success">
            OK {movieCount} films charges
          </div>
        )}
      </div>

      {uploaded && !isComputing && (
        <>
          <MoodSelector mood={mood} setMood={setMood} />
          <button
            className="btn-primary"
            onClick={handleStart}
            disabled={!mood.trim() || loading}
          >
            {loading ? "Calcul en cours..." : "Lancer les recommandations"}
          </button>
        </>
      )}

      {isComputing && (
        <p className="hint">Calcul en cours, les resultats vont apparaitre...</p>
      )}

      {error && <p className="error">{error}</p>}
      <button className="back-btn-bottom" onClick={onBack}>Retour</button>
    </div>
  );
}

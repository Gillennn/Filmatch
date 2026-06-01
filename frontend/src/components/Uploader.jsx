import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import JSZip from "jszip";

const USER_COLORS = ["#7c6af7", "#4caf83", "#f7a76a", "#f76a6a", "#6ab4f7", "#c96af7"];

async function extractFromZip(zipFile) {
  const zip = await JSZip.loadAsync(zipFile);
  const ratingsFile = zip.file("ratings.csv");
  if (!ratingsFile) {
    throw new Error("ratings.csv introuvable dans le zip Letterboxd");
  }
  const blob = await ratingsFile.async("blob");
  return new File([blob], "ratings.csv", { type: "text/csv" });
}

export default function Uploader({ files, setFiles }) {
  const [extracting, setExtracting] = useState(false);
  const [extractError, setExtractError] = useState(null);

  const onDrop = useCallback(async function(accepted) {
    setExtractError(null);
    setExtracting(true);
    const processed = [];
    for (const f of accepted) {
      if (f.name.toLowerCase().endsWith(".zip")) {
        try {
          const csv = await extractFromZip(f);
          processed.push(csv);
        } catch (e) {
          setExtractError(e.message);
        }
      } else {
        processed.push(f);
      }
    }
    setExtracting(false);
    if (processed.length > 0) {
      setFiles(function(prev) { return prev.concat(processed).slice(0, 6); });
    }
  }, [setFiles]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "text/csv": [".csv"],
      "application/zip": [".zip"],
      "application/x-zip-compressed": [".zip"]
    },
    multiple: true,
  });

  function removeFile(index) {
    setFiles(function(prev) { return prev.filter(function(_, i) { return i !== index; }); });
  }

  return (
    <div className="section">
      <label className="label">
        1. Historiques Letterboxd
        <span className="label-hint"> — jusqu a 6 utilisateurs</span>
      </label>

      <button
        className="btn-letterboxd"
        onClick={function() { window.open("https://letterboxd.com/data/export/", "_blank"); }}
        type="button"
      >
        Ouvrir mon Letterboxd Export
      </button>
      <p className="hint-small">
        Clique sur Export Data sur Letterboxd, puis depose le .zip directement ici
      </p>

      {files.length > 0 && (
        <div className="user-list">
          {files.map(function(f, i) {
            return (
              <div key={i} className="user-item">
                <span className="user-badge" style={{ background: USER_COLORS[i] }}>
                  U{i + 1}
                </span>
                <span className="user-filename">{f.name}</span>
                <button className="remove-btn" onClick={function() { removeFile(i); }}>
                  Retirer
                </button>
              </div>
            );
          })}
        </div>
      )}

      {files.length < 6 && (
        <div
          {...getRootProps()}
          className={"dropzone" + (isDragActive ? " active" : "")}
        >
          <input {...getInputProps()} />
          {extracting ? (
            <p>Extraction du zip en cours...</p>
          ) : isDragActive ? (
            <p>Depose ici...</p>
          ) : files.length === 0 ? (
            <p>Glisse ton .zip Letterboxd ou ratings.csv ici</p>
          ) : (
            <p>+ Ajouter un autre utilisateur (.zip ou .csv)</p>
          )}
        </div>
      )}

      {extractError && <p className="error">{extractError}</p>}
    </div>
  );
}


import { useCallback } from "react";
import { useDropzone } from "react-dropzone";

const USER_COLORS = ["#7c6af7", "#4caf83", "#f7a76a", "#f76a6a", "#6ab4f7", "#c96af7"];

export default function Uploader({ files, setFiles }) {
  const onDrop = useCallback(function(accepted) {
    if (accepted.length > 0) {
      setFiles(function(prev) { return prev.concat(accepted).slice(0, 6); });
    }
  }, [setFiles]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "text/csv": [".csv"] },
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
          {isDragActive ? (
            <p>Depose ici...</p>
          ) : files.length === 0 ? (
            <p>Glisse ton ratings.csv ici ou <span className="link">clique pour choisir</span></p>
          ) : (
            <p>+ Ajouter un autre utilisateur</p>
          )}
        </div>
      )}
    </div>
  );
}

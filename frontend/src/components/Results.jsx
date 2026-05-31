export default function Results({ data }) {
  const groupLabel = data.group_size > 1
    ? " - Groupe de " + data.group_size + " personnes"
    : "";

  return (
    <div className="results">
      <h2>
        {data.recommendations.length} films pour "{data.mood}"{groupLabel}
      </h2>
      <div className="grid">
        {data.recommendations.map(function(film) {
          return (
            <div key={film.key} className="movie-card">
              {film.poster_path ? (
                <img src={film.poster_path} alt={film.title} className="poster" />
              ) : (
                <div className="poster-placeholder">Pas d affiche</div>
              )}
              <div className="movie-info">
                <h3>{film.title}</h3>
                <span className="year">{film.year}</span>
                <div className="genres">
                  {film.genres.map(function(g) {
                    return <span key={g} className="genre-tag">{g}</span>;
                  })}
                </div>
                <p className="overview">
                  {film.overview ? film.overview.slice(0, 120) + "..." : ""}
                </p>
                <div className="score-bar">
                  <div
                    className="score-fill"
                    style={{ width: Math.round(film.score * 100) + "%" }}
                  />
                  <span className="score-label">{Math.round(film.score * 100)}%</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

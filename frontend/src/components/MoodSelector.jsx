const SUGGESTIONS = [
  "Comedie legere",
  "Romance feel-good",
  "Thriller haletant",
  "Film d action intense",
  "Drame emouvant",
  "Horreur angoissante",
  "Science-fiction epique",
  "Animation familiale",
  "Documentaire inspirant",
  "Soiree nostalgique",
];

export default function MoodSelector({ mood, setMood }) {
  return (
    <div className="section">
      <label className="label">2. Ton mood du moment</label>
      <input
        className="input"
        type="text"
        placeholder="Ex : comedie romantique un peu melancolique..."
        value={mood}
        onChange={(e) => setMood(e.target.value)}
      />
      <div className="pills">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            className={"pill" + (mood === s ? " pill-active" : "")}
            onClick={() => setMood(s)}
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}

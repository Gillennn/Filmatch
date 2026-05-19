import asyncio
import numpy as np
from typing import List, Dict, Optional

from services.tmdb import get_genre_map, fetch_candidates, search_movie
from services.embedding import encode_movie, encode_mood
from services.engine import EngineRecommandationGroupe

MOOD_KEYWORDS: Dict[str, List[str]] = {
    "action": ["Action", "Thriller"],
    "comedie": ["Comedy"], "comédie": ["Comedy"],
    "drole": ["Comedy"], "drôle": ["Comedy"], "rire": ["Comedy"],
    "horreur": ["Horror"], "peur": ["Horror"],
    "triste": ["Drama"], "melancolique": ["Drama"], "mélancolique": ["Drama"],
    "romantique": ["Romance"], "romance": ["Romance"], "amour": ["Romance"],
    "aventure": ["Adventure"],
    "science-fiction": ["Science Fiction"], "sf": ["Science Fiction"],
    "fantaisie": ["Fantasy"], "fantasy": ["Fantasy"],
    "animation": ["Animation"],
    "famille": ["Family"], "enfants": ["Family", "Animation"],
    "documentaire": ["Documentary"],
    "policier": ["Crime", "Mystery"], "crime": ["Crime"],
    "mystere": ["Mystery"], "mystère": ["Mystery"],
    "guerre": ["War"], "histoire": ["History"],
    "musical": ["Music"], "western": ["Western"],
    "thriller": ["Thriller"], "suspense": ["Thriller", "Mystery"],
}


def extract_genres_from_mood(mood_text: str) -> List[str]:
    mood_lower = mood_text.lower()
    genres: set = set()
    for keyword, genre_list in MOOD_KEYWORDS.items():
        if keyword in mood_lower:
            genres.update(genre_list)
    return list(genres)


async def _fetch_and_embed(film: Dict, genre_map: Dict) -> Optional[tuple]:
    try:
        result = await search_movie(film["name"], film["year"])
        if result and result.get("overview"):
            genres = [genre_map.get(gid, "") for gid in result.get("genre_ids", [])]
            genres = [g for g in genres if g]
            emb = encode_movie(result["overview"], genres)
            return film["key"], emb
    except Exception:
        pass
    return None


async def build_profile_embeddings(
    history: List[Dict], genre_map: Dict, top_k: int = 25
) -> Dict[str, np.ndarray]:
    top_films = sorted(history, key=lambda x: x["rating"], reverse=True)[:top_k]
    results = await asyncio.gather(
        *[_fetch_and_embed(f, genre_map) for f in top_films],
        return_exceptions=True,
    )
    out = {}
    for r in results:
        if r and not isinstance(r, Exception):
            key, emb = r
            out[key] = emb
    return out


async def run_pipeline(
    histories: List[List[Dict]],
    mood_text: str,
    top_n: int = 20,
) -> List[Dict]:
    seen_keys = {film["key"] for history in histories for film in history}

    genre_map = await get_genre_map()
    candidates = await fetch_candidates(seen_keys, genre_map)
    if not candidates:
        return []

    candidate_embeddings: Dict[str, np.ndarray] = {
        c["key"]: encode_movie(c["overview"], c["genres"]) for c in candidates
    }

    profile_embs_list = await asyncio.gather(
        *[build_profile_embeddings(h, genre_map) for h in histories]
    )

    engine = EngineRecommandationGroupe()
    profils_groupe = []
    for history, emb_catalogue in zip(histories, profile_embs_list):
        if emb_catalogue:
            profil = engine.calcul_profil_utilisateur(history, emb_catalogue)
            profils_groupe.append(profil)

    if not profils_groupe:
        return []

    v_mood = encode_mood(mood_text)
    genres_mood = extract_genres_from_mood(mood_text)

    scored = []
    for c in candidates:
        if c["key"] not in candidate_embeddings:
            continue
        score = engine.scoring_film_candidat(
            v_m=candidate_embeddings[c["key"]],
            genres_m=c["genres"],
            pop_m=c["popularity"],
            profils_groupe=profils_groupe,
            v_mood=v_mood,
            genres_mood=genres_mood,
        )
        scored.append({**c, "score": round(score, 4)})

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_n]

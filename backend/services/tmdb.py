import httpx
import os
from typing import Dict, List, Optional, Set
from dotenv import load_dotenv

load_dotenv()

TMDB_BASE = "https://api.themoviedb.org/3"
TMDB_IMG  = "https://image.tmdb.org/t/p/w500"


def _key() -> str:
    k = os.getenv("TMDB_API_KEY", "")
    if not k:
        raise RuntimeError("TMDB_API_KEY manquante dans le fichier .env")
    return k


async def get_genre_map() -> Dict[int, str]:
    """Récupère le mapping id → nom de genre depuis TMDB."""
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{TMDB_BASE}/genre/movie/list",
            params={"api_key": _key(), "language": "fr-FR"},
        )
        r.raise_for_status()
        return {g["id"]: g["name"] for g in r.json().get("genres", [])}


async def search_movie(name: str, year: Optional[int]) -> Optional[Dict]:
    """Cherche un film sur TMDB par titre + année."""
    params = {"api_key": _key(), "query": name, "language": "fr-FR"}
    if year:
        params["year"] = year

    async with httpx.AsyncClient() as client:
        r = await client.get(f"{TMDB_BASE}/search/movie", params=params)
        r.raise_for_status()
        results = r.json().get("results", [])
        return results[0] if results else None


async def fetch_candidates(
    seen_keys: Set[str],
    genre_map: Dict[int, str],
    max_pages: int = 5,
) -> List[Dict]:
    """
    Agrège popular + top_rated depuis TMDB.
    Filtre les films déjà vus par le groupe.
    """
    candidates: Dict[str, Dict] = {}

    async with httpx.AsyncClient(timeout=15.0) as client:
        for endpoint in ["popular", "top_rated"]:
            for page in range(1, max_pages + 1):
                r = await client.get(
                    f"{TMDB_BASE}/movie/{endpoint}",
                    params={"api_key": _key(), "language": "fr-FR", "page": page},
                )
                if r.status_code != 200:
                    continue

                for m in r.json().get("results", []):
                    title = m.get("title", "").strip()
                    raw_year = m.get("release_date", "")[:4]
                    year = int(raw_year) if raw_year.isdigit() else None
                    key = f"{title}_{year}" if year else title

                    if key in seen_keys or not m.get("overview"):
                        continue

                    genres = [
                        genre_map.get(gid, "")
                        for gid in m.get("genre_ids", [])
                    ]
                    candidates[key] = {
                        "key": key,
                        "tmdb_id": m["id"],
                        "title": title,
                        "year": year,
                        "overview": m.get("overview", ""),
                        "genres": [g for g in genres if g],
                        "popularity": m.get("popularity", 0.0),
                        "poster_path": (
                            TMDB_IMG + m["poster_path"]
                            if m.get("poster_path") else None
                        ),
                    }

    return list(candidates.values())
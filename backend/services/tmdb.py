import httpx
import unicodedata
import re
import os
from typing import Dict, List, Optional, Set
from dotenv import load_dotenv

load_dotenv()

TMDB_BASE = "https://api.themoviedb.org/3"
TMDB_IMG  = "https://image.tmdb.org/t/p/w500"

GENRE_IDS = {
    "Action": 28, "Adventure": 12, "Animation": 16, "Comedy": 35,
    "Crime": 80, "Documentary": 99, "Drama": 18, "Family": 10751,
    "Fantasy": 14, "History": 36, "Horror": 27, "Music": 10402,
    "Mystery": 9648, "Romance": 10749, "Science Fiction": 878,
    "Thriller": 53, "War": 10752, "Western": 37,
}


def _api_key() -> str:
    k = os.getenv("TMDB_API_KEY", "")
    if not k:
        raise RuntimeError("TMDB_API_KEY manquante dans le fichier .env")
    return k


def _norm(text: str) -> str:
    text = text.lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = re.sub(r"[^\w\s_]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _build(m: dict, genre_map: Dict[int, str]) -> dict:
    title = m.get("title", "").strip()
    raw_year = m.get("release_date", "")[:4]
    year = int(raw_year) if raw_year.isdigit() else None
    key = (title + "_" + str(year)) if year else title
    genres = [genre_map.get(gid, "") for gid in m.get("genre_ids", [])]
    return {
        "key": key,
        "tmdb_id": m["id"],
        "title": title,
        "year": year,
        "overview": m.get("overview", ""),
        "genres": [g for g in genres if g],
        "popularity": m.get("popularity", 0.0),
        "poster_path": TMDB_IMG + m["poster_path"] if m.get("poster_path") else None,
    }


async def get_genre_map() -> Dict[int, str]:
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{TMDB_BASE}/genre/movie/list",
            params={"api_key": _api_key(), "language": "en-US"},
        )
        r.raise_for_status()
        return {g["id"]: g["name"] for g in r.json().get("genres", [])}


async def search_movie(name: str, year: Optional[int]) -> Optional[Dict]:
    params = {"api_key": _api_key(), "query": name, "language": "en-US"}
    if year:
        params["year"] = year
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{TMDB_BASE}/search/movie", params=params)
        r.raise_for_status()
        results = r.json().get("results", [])
        return results[0] if results else None


async def fetch_by_genres(
    seen_norm: Set[str],
    genre_map: Dict[int, str],
    genre_names: List[str],
    max_pages: int = 10,
) -> Dict[str, dict]:
    ids = [str(GENRE_IDS[g]) for g in genre_names if g in GENRE_IDS]
    if not ids:
        return {}
    out = {}
    async with httpx.AsyncClient(timeout=20.0) as client:
        for page in range(1, max_pages + 1):
            r = await client.get(
                f"{TMDB_BASE}/discover/movie",
                params={
                    "api_key": _api_key(),
                    "language": "en-US",
                    "with_genres": ",".join(ids),
                    "sort_by": "popularity.desc",
                    "vote_count.gte": 800,
                    "vote_average.gte": 6.0,
                    "popularity.gte": 10,
                    "page": page,
                },
            )
            if r.status_code != 200:
                continue
            for m in r.json().get("results", []):
                if not m.get("overview"):
                    continue
                c = _build(m, genre_map)
                if _norm(c["key"]) not in seen_norm:
                    out[c["key"]] = c
    return out


async def fetch_popular(
    seen_norm: Set[str],
    genre_map: Dict[int, str],
    max_pages: int = 4,
) -> Dict[str, dict]:
    out = {}
    async with httpx.AsyncClient(timeout=20.0) as client:
        for endpoint in ["popular", "top_rated"]:
            for page in range(1, max_pages + 1):
                r = await client.get(
                    f"{TMDB_BASE}/movie/{endpoint}",
                    params={"api_key": _api_key(), "language": "en-US", "page": page},
                )
                if r.status_code != 200:
                    continue
                for m in r.json().get("results", []):
                    if not m.get("overview"):
                        continue
                    c = _build(m, genre_map)
                    if _norm(c["key"]) not in seen_norm:
                        out[c["key"]] = c
    return out


async def fetch_candidates(
    seen_norm: Set[str],
    genre_map: Dict[int, str],
    max_pages: int = 4,
) -> List[Dict]:
    result = await fetch_popular(seen_norm, genre_map, max_pages)
    return list(result.values())

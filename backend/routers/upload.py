import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException
from services.csv_parser import parse_letterboxd_csv
from services.tmdb import search_movie

router = APIRouter(prefix="/api", tags=["upload"])


@router.post("/upload-csv")
async def upload_csv(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Le fichier doit être un .csv")

    content = await file.read()

    try:
        movies = parse_letterboxd_csv(content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not movies:
        raise HTTPException(
            status_code=400,
            detail="Aucun film noté trouvé. Vérifie que tu utilises bien ratings.csv."
        )

    return {
        "user_id": str(uuid.uuid4()),
        "filename": file.filename,
        "movies_parsed": len(movies),
        "movies": [
            {"key": m["key"], "name": m["name"], "year": m["year"], "rating": m["rating"]}
            for m in movies
        ],
    }


@router.get("/test-tmdb")
async def test_tmdb(title: str, year: int = None):
    result = await search_movie(title, year)
    if not result:
        raise HTTPException(status_code=404, detail="Film non trouvé sur TMDB.")
    return {
        "tmdb_id": result["id"],
        "title": result["title"],
        "year": result.get("release_date", "")[:4],
        "overview": result.get("overview", "")[:200] + "...",
        "poster": f"https://image.tmdb.org/t/p/w500{result['poster_path']}"
                  if result.get("poster_path") else None,
    }
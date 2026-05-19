from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from services.csv_parser import parse_letterboxd_csv
from services.recommend import run_pipeline

router = APIRouter(prefix="/api", tags=["recommend"])


@router.post("/recommend")
async def recommend(
    file: UploadFile = File(...),
    mood: str = Form(...),
    top_n: int = Form(default=20),
):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, "Le fichier doit etre un .csv")
    if not mood.strip():
        raise HTTPException(400, "Le mood ne peut pas etre vide.")
    if not (1 <= top_n <= 50):
        raise HTTPException(400, "top_n doit etre entre 1 et 50.")

    content = await file.read()
    try:
        history = parse_letterboxd_csv(content)
    except ValueError as e:
        raise HTTPException(400, str(e))

    if not history:
        raise HTTPException(400, "Aucun film note trouve dans ce fichier.")

    try:
        results = await run_pipeline([history], mood, top_n)
    except Exception as e:
        raise HTTPException(500, f"Erreur pipeline : {str(e)}")

    return {
        "mood": mood,
        "group_size": 1,
        "recommendations": results,
    }

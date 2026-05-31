from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List
from services.csv_parser import parse_letterboxd_csv
from services.recommend import run_pipeline

router = APIRouter(prefix="/api", tags=["recommend"])


@router.post("/recommend")
async def recommend(
    files: List[UploadFile] = File(...),
    mood: str = Form(...),
    top_n: int = Form(default=5),
):
    if not files:
        raise HTTPException(400, "Au moins un fichier CSV requis.")
    if not mood.strip():
        raise HTTPException(400, "Le mood ne peut pas etre vide.")
    if len(files) > 6:
        raise HTTPException(400, "Maximum 6 utilisateurs par groupe.")

    histories = []
    for f in files:
        if not f.filename.lower().endswith(".csv"):
            raise HTTPException(400, f.filename + " n est pas un .csv")
        content = await f.read()
        try:
            history = parse_letterboxd_csv(content)
        except ValueError as e:
            raise HTTPException(400, str(e))
        if history:
            histories.append(history)

    if not histories:
        raise HTTPException(400, "Aucun historique valide trouve.")

    try:
        results = await run_pipeline(histories, mood, top_n)
    except Exception as e:
        raise HTTPException(500, "Erreur pipeline : " + str(e))

    return {
        "mood": mood,
        "group_size": len(histories),
        "recommendations": results,
    }

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from services.session import create_session, get_session
from services.csv_parser import parse_letterboxd_csv
from services.recommend import run_pipeline

router = APIRouter(prefix="/api/session", tags=["session"])


@router.post("/create")
async def create():
    s = create_session()
    return {"code": s["code"]}


@router.get("/{code}/status")
async def get_status(code: str):
    s = get_session(code)
    if not s:
        raise HTTPException(404, "Session introuvable ou expiree")
    return {
        "code": s["code"],
        "status": s["status"],
        "user_count": len(s["users"]),
        "users": [
            {"user_id": uid, "uploaded": u["uploaded"]}
            for uid, u in s["users"].items()
        ],
    }


@router.post("/{code}/upload")
async def upload(
    code: str,
    file: UploadFile = File(...),
    user_id: str = Form(...),
):
    s = get_session(code)
    if not s:
        raise HTTPException(404, "Session introuvable")
    if s["status"] == "done":
        raise HTTPException(400, "La session est terminee")

    content = await file.read()
    try:
        history = parse_letterboxd_csv(content)
    except ValueError as e:
        raise HTTPException(400, str(e))

    s["users"][user_id] = {"uploaded": True, "history": history}
    return {
        "user_id": user_id,
        "movies_parsed": len(history),
        "user_count": len(s["users"]),
    }


@router.post("/{code}/start")
async def start(code: str, mood: str = Form(...)):
    s = get_session(code)
    if not s:
        raise HTTPException(404, "Session introuvable")
    if not s["users"]:
        raise HTTPException(400, "Aucun historique uploade")
    if s["status"] == "computing":
        raise HTTPException(400, "Calcul deja en cours")

    s["status"] = "computing"
    s["mood"] = mood

    try:
        histories = [u["history"] for u in s["users"].values()]
        results = await run_pipeline(histories, mood, top_n=5)
        s["results"] = results
        s["status"] = "done"
    except Exception as e:
        s["status"] = "error"
        raise HTTPException(500, "Erreur : " + str(e))

    return {"mood": mood, "group_size": len(histories), "recommendations": results}


@router.get("/{code}/results")
async def get_results(code: str):
    s = get_session(code)
    if not s:
        raise HTTPException(404, "Session introuvable")
    if s["status"] != "done":
        return {"status": s["status"], "results": None}
    return {
        "status": "done",
        "mood": s["mood"],
        "group_size": len(s["users"]),
        "recommendations": s["results"],
    }

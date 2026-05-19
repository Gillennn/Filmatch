from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.upload import router as upload_router

app = FastAPI(title="Filmatch API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router)

@app.get("/health")
def health():
    return {"status": "ok", "version": "0.2.0"}
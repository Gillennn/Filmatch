from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.upload import router as upload_router
import services.embedding as emb


@asynccontextmanager
async def lifespan(app: FastAPI):
    emb.load_model()
    yield


app = FastAPI(title="CineGroup API", version="0.3.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "version": "0.3.0",
        "model_loaded": emb._model is not None,
    }

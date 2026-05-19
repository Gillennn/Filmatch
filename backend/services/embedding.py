from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Optional

_model: Optional[SentenceTransformer] = None


def load_model() -> None:
    global _model
    print("Chargement du modele d embeddings...")
    _model = SentenceTransformer("all-MiniLM-L6-v2")
    print(f"Modele charge. Dimension : {_model.get_embedding_dimension()}")


def get_model() -> SentenceTransformer:
    if _model is None:
        raise RuntimeError("Modele non charge.")
    return _model


def encode_movie(overview: str, genres: List[str]) -> np.ndarray:
    text = f"{overview} {' '.join(genres)}".strip()
    return get_model().encode(text, normalize_embeddings=True)


def encode_mood(mood_text: str) -> np.ndarray:
    return get_model().encode(mood_text, normalize_embeddings=True)

import numpy as np
from datetime import datetime
from typing import List, Dict, Optional


class EngineRecommandationGroupe:
    def __init__(
        self,
        t_half: float = 365.0,
        lambda_r: float = 1.0,
        alpha: float = 0.65,
        omega_hist: float = 0.4,
        omega_mood: float = 0.6,
        omega_pen: float = 0.3,
        delta: float = 0.7,
        gamma_pop: float = 0.15,
    ):
        self.t_half = t_half
        self.lambda_r = lambda_r
        self.alpha = alpha
        self.omega_hist = omega_hist
        self.omega_mood = omega_mood
        self.omega_pen = omega_pen
        self.delta = delta
        self.gamma_pop = gamma_pop

    def calcul_profil_utilisateur(
        self,
        history: List[Dict],
        embeddings_catalogue: Dict[str, np.ndarray],
        date_reference: Optional[datetime] = None,
    ) -> np.ndarray:
        if not date_reference:
            date_reference = datetime.now()

        valid_records = [r for r in history if r["key"] in embeddings_catalogue]
        if not valid_records:
            dim = next(iter(embeddings_catalogue.values())).shape
            return np.zeros(dim, dtype=np.float64)

        ratings = [r["rating"] for r in valid_records]
        user_mean = np.mean(ratings) if len(ratings) >= 5 else 3.0

        sample = next(iter(embeddings_catalogue.values()))
        p_u = np.zeros(sample.shape, dtype=np.float64)

        for record in valid_records:
            v_m = embeddings_catalogue[record["key"]]
            w_r = np.exp((record["rating"] - user_mean) / self.lambda_r) - 1.0
            delta_t = (date_reference - record["date_viewed"]).days
            decay = 2.0 ** (-max(0.0, delta_t) / self.t_half)
            p_u += (w_r * decay) * v_m

        norm = np.linalg.norm(p_u)
        if norm > 1e-9:
            p_u = p_u / norm
        return p_u

    def _cosinus_normalise(self, vec_a: np.ndarray, vec_b: np.ndarray) -> float:
        na, nb = np.linalg.norm(vec_a), np.linalg.norm(vec_b)
        if na < 1e-9 or nb < 1e-9:
            return 0.5
        return float(0.5 * (np.dot(vec_a, vec_b) / (na * nb) + 1.0))

    def scoring_film_candidat(
        self,
        v_m: np.ndarray,
        genres_m: List[str],
        pop_m: float,
        profils_groupe: List[np.ndarray],
        v_mood: np.ndarray,
        genres_mood: List[str],
    ) -> float:
        N = len(profils_groupe)
        if N == 0:
            raise ValueError("Groupe vide.")

        prefs = np.array([self._cosinus_normalise(p, v_m) for p in profils_groupe])

        if N == 1:
            r_hybrid = float(prefs[0])
            sigma_p = 0.0
        else:
            r_hybrid = self.alpha * np.mean(prefs) + (1.0 - self.alpha) * np.min(prefs)
            sigma_p = float(np.std(prefs))

        sim_sem = self._cosinus_normalise(v_m, v_mood)
        if genres_mood:
            sim_genre = len(set(genres_m) & set(genres_mood)) / len(genres_mood)
        else:
            sim_genre = 1.0

        sim_mood = self.delta * sim_sem + (1.0 - self.delta) * sim_genre
        score = self.omega_hist * r_hybrid + self.omega_mood * sim_mood - self.omega_pen * sigma_p
        facteur_pop = 1.0 / (np.log(10 + pop_m) ** self.gamma_pop)
        return float(score * facteur_pop)

import pandas as pd
from io import BytesIO
from datetime import datetime
from typing import List, Dict


def parse_letterboxd_csv(file_content: bytes) -> List[Dict]:
    """
    Parse le contenu brut d'un fichier ratings.csv Letterboxd.
    Retourne une liste de dicts avec une clé synthétique Nom_Année.
    """
    try:
        df = pd.read_csv(BytesIO(file_content))
    except Exception as e:
        raise ValueError(f"Impossible de lire le CSV : {e}")

    required = {"Date", "Name", "Year", "Letterboxd URI", "Rating"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Colonnes manquantes : {missing}")

    records = []
    for _, row in df.iterrows():
        try:
            rating_val = row["Rating"]
            if pd.isna(rating_val):
                continue

            rating = float(rating_val)
            date_viewed = datetime.strptime(str(row["Date"]).strip(), "%Y-%m-%d")
            name = str(row["Name"]).strip()
            year = int(row["Year"]) if pd.notna(row["Year"]) else None
            key = f"{name}_{year}" if year else name

            records.append({
                "key": key,
                "name": name,
                "year": year,
                "rating": rating,
                "date_viewed": date_viewed,
            })
        except Exception:
            continue

    return records
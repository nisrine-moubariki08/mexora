import pandas as pd
import logging

logger = logging.getLogger("mexora_etl")

def transform_produits(df: pd.DataFrame) -> pd.DataFrame:
    initial = len(df)
    logger.info(f"[TRANSFORM] produits  → début : {initial} lignes")

    # R1 — Catégories
    df["categorie"]      = df["categorie"].str.strip().str.capitalize()
    df["sous_categorie"] = df["sous_categorie"].str.strip().str.capitalize()
    df["marque"]         = df["marque"].str.strip()
    df["nom"]            = df["nom"].str.strip()

    # R2 — Prix null
    df["prix_catalogue"] = pd.to_numeric(df["prix_catalogue"], errors="coerce")
    nb_null = df["prix_catalogue"].isna().sum()
    mediane = df.groupby("sous_categorie")["prix_catalogue"].transform("median")
    df["prix_catalogue"] = df["prix_catalogue"].fillna(mediane)
    df["prix_catalogue"] = df["prix_catalogue"].fillna(df["prix_catalogue"].median())
    logger.info(f"[TRANSFORM] R2 prix null     : {nb_null} remplacés")

    # R3 — Actif
    df["actif"] = df["actif"].map(
        {True: True, False: False, "true": True, "false": False,
         "True": True, "False": False, "1": True, "0": False}
    ).fillna(True)

    logger.info(f"[TRANSFORM] produits  → fin  : {initial} → {len(df)} lignes")
    return df
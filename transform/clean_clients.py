import pandas as pd
import re
import logging

logger = logging.getLogger("mexora_etl")

PATTERN_EMAIL = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'

MAPPING_SEXE = {
    "m": "m", "1": "m", "homme": "m", "h": "m", "male": "m",
    "f": "f", "0": "f", "femme": "f", "female": "f",
}

VARIANTES_VILLES = {
    "tanger": "Tanger", "tng": "Tanger", "tnja": "Tanger",
    "casablanca": "Casablanca", "cas": "Casablanca", "casa": "Casablanca",
    "rabat": "Rabat", "rba": "Rabat",
    "fès": "Fès", "fes": "Fès", "fez": "Fès",
    "marrakech": "Marrakech", "mrk": "Marrakech",
    "agadir": "Agadir", "agd": "Agadir",
    "oujda": "Oujda", "oud": "Oujda",
    "meknès": "Meknès", "mkn": "Meknès", "meknes": "Meknès",
    "tétouan": "Tétouan", "tet": "Tétouan", "tetouan": "Tétouan",
    "safi": "Safi", "sfi": "Safi",
}

def transform_clients(df: pd.DataFrame) -> pd.DataFrame:
    initial = len(df)
    logger.info(f"[TRANSFORM] clients   → début : {initial} lignes")

    # R1 — Déduplication email
    df["email_norm"] = df["email"].str.lower().str.strip()
    df["date_inscription"] = pd.to_datetime(df["date_inscription"], errors="coerce")
    df = df.sort_values("date_inscription").drop_duplicates(
        subset=["email_norm"], keep="last"
    )
    logger.info(f"[TRANSFORM] R1 doublons      : {initial - len(df)} supprimés")

    # R2 — Sexe
    df["sexe"] = (
        df["sexe"].str.lower().str.strip()
        .map(MAPPING_SEXE).fillna("inconnu")
    )

    # R3 — Dates de naissance
    df["date_naissance"] = pd.to_datetime(df["date_naissance"], errors="coerce")
    today = pd.Timestamp("today")
    df["age"] = ((today - df["date_naissance"]).dt.days // 365).astype("Int64")
    ages_invalides = ((df["age"] < 16) | (df["age"] > 100)).sum()
    df.loc[(df["age"] < 16) | (df["age"] > 100), ["date_naissance", "age"]] = pd.NA
    logger.info(f"[TRANSFORM] R3 âges          : {ages_invalides} invalides")

    # R4 — Emails
    masque_invalide = ~df["email"].str.match(PATTERN_EMAIL, na=False)
    df.loc[masque_invalide, "email"] = None
    logger.info(f"[TRANSFORM] R4 emails        : {masque_invalide.sum()} invalides")

    # R5 — Villes
    df["ville"] = (
        df["ville"].str.lower().str.strip()
        .map(VARIANTES_VILLES).fillna("Non renseignée")
    )

    # R6 — Tranche d'âge
    df["tranche_age"] = pd.cut(
        df["age"].fillna(0).astype(int),
        bins=[0, 18, 25, 35, 45, 55, 65, 200],
        labels=["<18", "18-24", "25-34", "35-44", "45-54", "55-64", "65+"],
        right=False
    )

    logger.info(f"[TRANSFORM] clients   → fin  : {initial} → {len(df)} lignes")
    return df
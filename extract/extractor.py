import json
import logging

import pandas as pd

from config.settings import PATH_CLIENTS, PATH_COMMANDES, PATH_PRODUITS, PATH_REGIONS

logger = logging.getLogger("mexora_etl")


def _read_csv(path: str) -> pd.DataFrame:
    """Lit les CSV UTF-8 générés par le projet, avec fallback pour anciens fichiers."""
    try:
        return pd.read_csv(path, dtype=str, encoding="utf-8")
    except UnicodeDecodeError:
        return pd.read_csv(path, dtype=str, encoding="latin-1")


def extract_commandes() -> pd.DataFrame:
    df = _read_csv(PATH_COMMANDES)
    logger.info("[EXTRACT] commandes : %s lignes", len(df))
    return df


def extract_produits() -> pd.DataFrame:
    with open(PATH_PRODUITS, "r", encoding="utf-8") as f:
        data = json.load(f)
    df = pd.DataFrame(data["produits"])
    logger.info("[EXTRACT] produits : %s lignes", len(df))
    return df


def extract_clients() -> pd.DataFrame:
    df = _read_csv(PATH_CLIENTS)
    logger.info("[EXTRACT] clients : %s lignes", len(df))
    return df


def extract_regions() -> pd.DataFrame:
    df = _read_csv(PATH_REGIONS)
    logger.info("[EXTRACT] regions : %s lignes", len(df))
    return df

import pandas as pd
import logging

logger = logging.getLogger("mexora_etl")


def _construire_mapping_villes(df_regions: pd.DataFrame) -> dict:
    mapping = {}

    variantes = {
        "Tanger":     ["tanger","tng","tnja","tangier","tanger "],
        "Casablanca": ["casablanca","cas","casa","casablanca "],
        "Rabat":      ["rabat","rba"],
        "Fès":        ["fès","fes","fez","fes "],
        "Marrakech":  ["marrakech","mrk","marrakesh"],
        "Agadir":     ["agadir","agd"],
        "Oujda":      ["oujda","oud"],
        "Meknès":     ["meknès","mkn","meknes"],
        "Tétouan":    ["tétouan","tet","tetouan"],
        "Safi":       ["safi","sfi"],
    }

    for ville_std, liste in variantes.items():
        for v in liste:
            mapping[v.lower().strip()] = ville_std

    if df_regions is not None and len(df_regions) > 0:
        for _, row in df_regions.iterrows():
            mapping[str(row["code_ville"]).lower()] = row["nom_ville_standard"]
            mapping[str(row["nom_ville_standard"]).lower()] = row["nom_ville_standard"]

    return mapping


def transform_commandes(df: pd.DataFrame, df_regions: pd.DataFrame) -> pd.DataFrame:
    initial = len(df)
    logger.info(f"[TRANSFORM] commandes → début : {initial} lignes")

    # R1 — Doublons
    avant = len(df)
    df = df.drop_duplicates(subset=["id_commande"], keep="last").copy()
    logger.info(f"[TRANSFORM] R1 doublons      : {avant - len(df)} supprimées")

    # R2 — Dates
    df["date_commande"] = pd.to_datetime(
        df["date_commande"], format="mixed", dayfirst=True, errors="coerce"
    )
    dates_invalides = df["date_commande"].isna().sum()
    df = df.dropna(subset=["date_commande"]).copy()
    logger.info(f"[TRANSFORM] R2 dates         : {dates_invalides} invalides supprimées")

    df["date_livraison"] = pd.to_datetime(df["date_livraison"], errors="coerce")

    # R3 — Villes
    mapping_villes = _construire_mapping_villes(df_regions)
    df["ville_livraison_clean"] = (
        df["ville_livraison"].str.strip().str.lower()
        .map(mapping_villes).fillna("Non renseignée")
    )
    non_mappes = (df["ville_livraison_clean"] == "Non renseignée").sum()
    logger.info(f"[TRANSFORM] R3 villes        : {non_mappes} non reconnues")

    # R4 — Statuts
    mapping_statuts = {
        "livré":    "livré",   "livre":    "livré",
        "done":     "livré",
        "annulé":  "annulé",  "annule":   "annulé",   "ko": "annulé",
        "en_cours": "en_cours","ok":       "en_cours",
        "retourné": "retourné","retourne": "retourné",
    }
    df["statut_clean"] = (
        df["statut"].str.lower().str.strip()
        .map(mapping_statuts).fillna("inconnu")
    )
    inconnus = (df["statut_clean"] == "inconnu").sum()
    logger.info(f"[TRANSFORM] R4 statuts       : {inconnus} valeurs inconnues")

    # R5 — Quantités
    df["quantite"] = pd.to_numeric(df["quantite"], errors="coerce")
    avant = len(df)
    df = df[df["quantite"] > 0]
    logger.info(f"[TRANSFORM] R5 quantités     : {avant - len(df)} supprimées")

    # R6 — Prix nuls
    df["prix_unitaire"] = pd.to_numeric(df["prix_unitaire"], errors="coerce")
    avant = len(df)
    df = df[df["prix_unitaire"] > 0]
    logger.info(f"[TRANSFORM] R6 prix nuls     : {avant - len(df)} supprimées")

    # R7 — Livreurs manquants
    nb_manquants = df["id_livreur"].isna().sum() + (df["id_livreur"] == "").sum()
    df["id_livreur"] = df["id_livreur"].replace("", None).fillna("-1")
    logger.info(f"[TRANSFORM] R7 livreurs      : {nb_manquants} → '-1'")

    # Calcul mesures
    df["montant_ht"]  = df["quantite"] * df["prix_unitaire"]
    df["montant_ttc"] = (df["montant_ht"] * 1.20).round(2)
    df["delai_livraison_jours"] = (
        df["date_livraison"] - df["date_commande"]
    ).dt.days

    logger.info(f"[TRANSFORM] commandes → fin  : {initial} → {len(df)} lignes")
    return df

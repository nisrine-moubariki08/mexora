import pandas as pd
import logging
from config.settings import RAMADAN_PERIODES, FERIES_MAROC, SEUIL_GOLD, SEUIL_SILVER

logger = logging.getLogger("mexora_etl")

def build_dim_temps(date_debut: str, date_fin: str) -> pd.DataFrame:
    dates = pd.date_range(start=date_debut, end=date_fin, freq="D")
    df = pd.DataFrame({
        "id_date":         dates.strftime("%Y%m%d").astype(int),
        "date_complete":   dates.date,
        "jour":            dates.day,
        "mois":            dates.month,
        "trimestre":       dates.quarter,
        "annee":           dates.year,
        "semaine":         dates.isocalendar().week.astype(int),
        "libelle_jour":    dates.strftime("%A"),
        "libelle_mois":    dates.strftime("%B"),
        "est_weekend":     dates.dayofweek >= 5,
        "est_ferie_maroc": dates.strftime("%Y-%m-%d").isin(FERIES_MAROC),
        "periode_ramadan": False,
    })
    for debut, fin in RAMADAN_PERIODES:
        masque = (dates >= debut) & (dates <= fin)
        df.loc[masque, "periode_ramadan"] = True
    logger.info(f"[BUILD] dim_temps     : {len(df)} lignes")
    return df

def build_dim_region(df_regions: pd.DataFrame) -> pd.DataFrame:
    # Si df_regions est None ou vide, créer un DataFrame minimal
    if df_regions is None or len(df_regions) == 0:
        logger.warning("[BUILD] dim_region : df_regions vide, création manuelle")
        data = {
            "ville": ["Tanger","Casablanca","Rabat","Fès","Marrakech",
                      "Agadir","Oujda","Meknès","Tétouan","Safi"],
            "province": ["Tanger-Assilah","Casablanca","Rabat","Fès",
                         "Marrakech","Agadir-Ida-Ou-Tanane","Oujda-Angad",
                         "Meknès","Tétouan","Safi"],
            "region_admin": ["Tanger-Tétouan-Al Hoceïma","Casablanca-Settat",
                             "Rabat-Salé-Kénitra","Fès-Meknès","Marrakech-Safi",
                             "Souss-Massa","Oriental","Fès-Meknès",
                             "Tanger-Tétouan-Al Hoceïma","Marrakech-Safi"],
            "zone_geo": ["Nord","Centre","Centre","Centre","Sud",
                         "Sud","Est","Centre","Nord","Sud"],
        }
        df = pd.DataFrame(data)
    else:
        df = df_regions[["nom_ville_standard","province","region_admin","zone_geo"]].copy()
        df = df.rename(columns={"nom_ville_standard": "ville"})

    df = df.drop_duplicates(subset=["ville"]).reset_index(drop=True)
    df.insert(0, "id_region", range(1, len(df) + 1))
    df["pays"] = "Maroc"
    logger.info(f"[BUILD] dim_region    : {len(df)} lignes")
    return df

def build_dim_livreur(df_commandes: pd.DataFrame) -> pd.DataFrame:
    livreurs = [l for l in df_commandes["id_livreur"].dropna().unique() if l != "-1"]
    rows = [{"id_livreur_nk": "-1", "nom_livreur": "Inconnu",
             "type_transport": "Inconnu", "zone_couverture": "Inconnue"}]
    for lv in sorted(livreurs):
        rows.append({
            "id_livreur_nk":  lv,
            "nom_livreur":    f"Livreur {lv}",
            "type_transport":  "Véhicule",
            "zone_couverture": "Maroc",
        })
    df = pd.DataFrame(rows)
    df.insert(0, "id_livreur", range(1, len(df) + 1))
    logger.info(f"[BUILD] dim_livreur   : {len(df)} lignes")
    return df

def build_dim_produit(df_produits: pd.DataFrame) -> pd.DataFrame:
    df = df_produits[[
        "id_produit","nom","categorie","sous_categorie",
        "marque","fournisseur","prix_catalogue","origine_pays","actif"
    ]].copy()
    df = df.rename(columns={
        "id_produit":     "id_produit_nk",
        "nom":            "nom_produit",
        "prix_catalogue": "prix_standard",
    })
    df["date_debut"] = pd.Timestamp("2020-01-01").date()
    df["date_fin"]   = pd.Timestamp("9999-12-31").date()
    df["est_actif"]  = True
    df = df.reset_index(drop=True)
    df.insert(0, "id_produit_sk", range(1, len(df) + 1))
    logger.info(f"[BUILD] dim_produit   : {len(df)} lignes")
    return df

def calculer_segments_clients(df_commandes: pd.DataFrame) -> pd.DataFrame:
    date_limite = pd.Timestamp("today") - pd.Timedelta(days=365)
    df_recents = df_commandes[
        (df_commandes["date_commande"] >= date_limite) &
        (df_commandes["statut_clean"] == "livré")
    ].copy()
    if df_recents.empty:
        return pd.DataFrame(columns=["id_client", "segment_client"])
    ca = df_recents.groupby("id_client")["montant_ttc"].sum().reset_index()
    ca.columns = ["id_client", "ca_12m"]
    def segment(val):
        if val >= SEUIL_GOLD:   return "Gold"
        if val >= SEUIL_SILVER: return "Silver"
        return "Bronze"
    ca["segment_client"] = ca["ca_12m"].apply(segment)
    return ca[["id_client", "segment_client"]]

def build_dim_client(
    df_clients: pd.DataFrame,
    df_commandes: pd.DataFrame,
    df_regions: pd.DataFrame
) -> pd.DataFrame:
    segments = calculer_segments_clients(df_commandes)
    df = df_clients.merge(segments, on="id_client", how="left")
    df["segment_client"] = df["segment_client"].fillna("Bronze")
    df["nom_complet"] = (
        df["prenom"].fillna("") + " " + df["nom"].fillna("")
    ).str.strip()
    df = df.rename(columns={"id_client": "id_client_nk"})
    df = df.reset_index(drop=True)
    df.insert(0, "id_client_sk", range(1, len(df) + 1))
    colonnes = [
        "id_client_sk", "id_client_nk", "nom_complet", "email", "tranche_age",
        "sexe", "ville", "segment_client", "canal_acquisition",
        "date_inscription"
    ]
    df = df[[c for c in colonnes if c in df.columns]]
    logger.info(f"[BUILD] dim_client    : {len(df)} lignes")
    return df

def build_fait_ventes(
    df_commandes: pd.DataFrame,
    dim_temps:    pd.DataFrame,
    dim_client:   pd.DataFrame,
    dim_produit:  pd.DataFrame,
    dim_region:   pd.DataFrame,
    dim_livreur:  pd.DataFrame,
) -> pd.DataFrame:
    df = df_commandes.copy()

    # Clé date
    df["id_date"] = df["date_commande"].dt.strftime("%Y%m%d").astype(int)

    # Jointures SK
    map_client  = dim_client.set_index("id_client_nk")["id_client_sk"].to_dict()
    map_produit = dim_produit.set_index("id_produit_nk")["id_produit_sk"].to_dict()
    map_region  = dim_region.set_index("ville")["id_region"].to_dict()
    map_livreur = dim_livreur.set_index("id_livreur_nk")["id_livreur"].to_dict()

    df["id_client"]  = df["id_client"].map(map_client)
    df["id_produit"] = df["id_produit"].map(map_produit)
    df["id_region"]  = df["ville_livraison_clean"].map(map_region)
    df["id_livreur"] = df["id_livreur"].map(map_livreur)

    # Sélection colonnes finales
    fait = df[[
        "id_commande",
        "id_date", "id_produit", "id_client", "id_region", "id_livreur",
        "quantite", "prix_unitaire", "montant_ht", "montant_ttc",
        "delai_livraison_jours", "statut_clean"
    ]].rename(columns={
        "quantite":             "quantite_vendue",
        "statut_clean":         "statut_commande",
    })

    avant = len(fait)
    fait = fait.dropna(subset=["id_client", "id_produit", "id_region"])
    int_cols = [
        "id_date", "id_produit", "id_client", "id_region", "id_livreur",
        "quantite_vendue", "delai_livraison_jours"
    ]
    for col in int_cols:
        if col in fait.columns:
            fait[col] = pd.to_numeric(fait[col], errors="coerce").astype("Int64")
    logger.info(f"[BUILD] fait_ventes   : {avant - len(fait)} lignes sans clé supprimées")

    fait = fait.reset_index(drop=True)
    fait.insert(0, "id_vente", range(1, len(fait) + 1))
    fait["remise_pct"] = 0
    logger.info(f"[BUILD] fait_ventes   : {len(fait)} lignes finales")
    return fait

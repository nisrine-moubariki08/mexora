import logging
from pathlib import Path

import pandas as pd
import sqlalchemy
from sqlalchemy import text

logger = logging.getLogger("mexora_etl")

BASE_DIR = Path(__file__).resolve().parents[1]
DDL_PATH = BASE_DIR / "sql" / "create_dwh.sql"


def get_engine(db_url: str):
    engine = sqlalchemy.create_engine(db_url, pool_pre_ping=True, future=True)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    logger.info("[LOAD] Connexion PostgreSQL OK")
    return engine


def creer_schemas(engine) -> None:
    with engine.begin() as conn:
        ddl = DDL_PATH.read_text(encoding="utf-8")
        conn.execute(text(ddl))
    logger.info("[LOAD] DDL appliqué : schémas, tables, contraintes, vues et index")


def _prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    clean = df.copy()
    for col in clean.columns:
        if pd.api.types.is_datetime64_any_dtype(clean[col]):
            clean[col] = clean[col].dt.date
        elif str(clean[col].dtype) == "category":
            clean[col] = clean[col].astype(str)
    return clean.where(pd.notnull(clean), None)


def _stage(df: pd.DataFrame, table_name: str, engine, chunksize: int = 5000) -> str:
    staging_table = f"stg_{table_name}"
    clean = _prepare_dataframe(df)
    clean.to_sql(
        name=staging_table,
        con=engine,
        schema="staging_mexora",
        if_exists="replace",
        index=False,
        method="multi",
        chunksize=chunksize,
    )
    logger.info("[LOAD] staging_mexora.%s : %s lignes", staging_table, len(clean))
    return staging_table


def charger_dimension(df: pd.DataFrame, table_name: str, engine) -> None:
    """Charge les dimensions avec la stratégie adaptée au type de table."""
    if table_name == "dim_temps":
        _charger_dim_temps(df, engine)
    elif table_name == "dim_region":
        _charger_dim_region(df, engine)
    elif table_name == "dim_livreur":
        _charger_dim_livreur(df, engine)
    elif table_name == "dim_client":
        _charger_dim_client_scd1(df, engine)
    elif table_name == "dim_produit":
        _charger_dim_produit_scd2(df, engine)
    else:
        raise ValueError(f"Dimension non supportée : {table_name}")


def _charger_dim_temps(df: pd.DataFrame, engine) -> None:
    _stage(df, "dim_temps", engine)
    sql = """
        INSERT INTO dwh_mexora.dim_temps (
            id_date, date_complete, jour, mois, trimestre, annee, semaine,
            libelle_jour, libelle_mois, est_weekend, est_ferie_maroc, periode_ramadan
        )
        SELECT id_date, date_complete, jour, mois, trimestre, annee, semaine,
               libelle_jour, libelle_mois, est_weekend, est_ferie_maroc, periode_ramadan
        FROM staging_mexora.stg_dim_temps
        ON CONFLICT (id_date) DO UPDATE SET
            date_complete = EXCLUDED.date_complete,
            jour = EXCLUDED.jour,
            mois = EXCLUDED.mois,
            trimestre = EXCLUDED.trimestre,
            annee = EXCLUDED.annee,
            semaine = EXCLUDED.semaine,
            libelle_jour = EXCLUDED.libelle_jour,
            libelle_mois = EXCLUDED.libelle_mois,
            est_weekend = EXCLUDED.est_weekend,
            est_ferie_maroc = EXCLUDED.est_ferie_maroc,
            periode_ramadan = EXCLUDED.periode_ramadan;
    """
    with engine.begin() as conn:
        conn.execute(text(sql))
    logger.info("[LOAD] dim_temps upsertée : %s lignes source", len(df))


def _charger_dim_region(df: pd.DataFrame, engine) -> None:
    _stage(df, "dim_region", engine)
    sql = """
        INSERT INTO dwh_mexora.dim_region (
            id_region, ville, province, region_admin, zone_geo, pays
        )
        SELECT id_region, ville, province, region_admin, zone_geo, pays
        FROM staging_mexora.stg_dim_region
        ON CONFLICT (ville) DO UPDATE SET
            province = EXCLUDED.province,
            region_admin = EXCLUDED.region_admin,
            zone_geo = EXCLUDED.zone_geo,
            pays = EXCLUDED.pays;
        SELECT setval(
            pg_get_serial_sequence('dwh_mexora.dim_region', 'id_region'),
            COALESCE((SELECT MAX(id_region) FROM dwh_mexora.dim_region), 1),
            true
        );
    """
    with engine.begin() as conn:
        conn.execute(text(sql))
    logger.info("[LOAD] dim_region upsertée : %s lignes source", len(df))


def _charger_dim_livreur(df: pd.DataFrame, engine) -> None:
    _stage(df, "dim_livreur", engine)
    sql = """
        INSERT INTO dwh_mexora.dim_livreur (
            id_livreur, id_livreur_nk, nom_livreur, type_transport, zone_couverture
        )
        SELECT id_livreur, id_livreur_nk, nom_livreur, type_transport, zone_couverture
        FROM staging_mexora.stg_dim_livreur
        ON CONFLICT (id_livreur_nk) DO UPDATE SET
            nom_livreur = EXCLUDED.nom_livreur,
            type_transport = EXCLUDED.type_transport,
            zone_couverture = EXCLUDED.zone_couverture;
        SELECT setval(
            pg_get_serial_sequence('dwh_mexora.dim_livreur', 'id_livreur'),
            COALESCE((SELECT MAX(id_livreur) FROM dwh_mexora.dim_livreur), 1),
            true
        );
    """
    with engine.begin() as conn:
        conn.execute(text(sql))
    logger.info("[LOAD] dim_livreur upsertée : %s lignes source", len(df))


def _charger_dim_client_scd1(df: pd.DataFrame, engine) -> None:
    """SCD Type 1 : les corrections simples, dont l'email, écrasent la valeur active."""
    _stage(df, "dim_client", engine)
    sql = """
        INSERT INTO dwh_mexora.dim_client (
            id_client_sk, id_client_nk, nom_complet, email, tranche_age, sexe, ville,
            segment_client, canal_acquisition, date_inscription
        )
        SELECT id_client_sk, id_client_nk, nom_complet, email, tranche_age, sexe, ville,
               segment_client, canal_acquisition, date_inscription
        FROM staging_mexora.stg_dim_client
        ON CONFLICT (id_client_nk) DO UPDATE SET
            nom_complet = EXCLUDED.nom_complet,
            email = EXCLUDED.email,
            tranche_age = EXCLUDED.tranche_age,
            sexe = EXCLUDED.sexe,
            ville = EXCLUDED.ville,
            segment_client = EXCLUDED.segment_client,
            canal_acquisition = EXCLUDED.canal_acquisition,
            date_inscription = EXCLUDED.date_inscription,
            date_maj = CURRENT_TIMESTAMP;
        SELECT setval(
            pg_get_serial_sequence('dwh_mexora.dim_client', 'id_client_sk'),
            COALESCE((SELECT MAX(id_client_sk) FROM dwh_mexora.dim_client), 1),
            true
        );
    """
    with engine.begin() as conn:
        conn.execute(text(sql))
    logger.info("[LOAD] dim_client SCD1 upsertée : %s lignes source", len(df))


def _charger_dim_produit_scd2(df: pd.DataFrame, engine) -> None:
    """SCD Type 2 : une modification d'attribut historique crée une nouvelle version."""
    _stage(df, "dim_produit", engine)
    sql = """
        DROP TABLE IF EXISTS staging_mexora.tmp_dim_produit_source;
        CREATE TABLE staging_mexora.tmp_dim_produit_source AS
        SELECT DISTINCT ON (id_produit_nk)
               id_produit_sk, id_produit_nk, nom_produit, categorie, sous_categorie,
               marque, fournisseur, prix_standard, origine_pays, date_debut
        FROM staging_mexora.stg_dim_produit
        ORDER BY id_produit_nk, date_debut DESC;

        DROP TABLE IF EXISTS staging_mexora.tmp_dim_produit_new;
        CREATE TABLE staging_mexora.tmp_dim_produit_new AS
        SELECT s.*
        FROM staging_mexora.tmp_dim_produit_source s
        LEFT JOIN dwh_mexora.dim_produit p
          ON p.id_produit_nk = s.id_produit_nk
        WHERE p.id_produit_sk IS NULL;

        DROP TABLE IF EXISTS staging_mexora.tmp_dim_produit_changed;
        CREATE TABLE staging_mexora.tmp_dim_produit_changed AS
        SELECT s.*
        FROM staging_mexora.tmp_dim_produit_source s
        JOIN dwh_mexora.dim_produit p
          ON p.id_produit_nk = s.id_produit_nk
         AND p.est_actif = TRUE
        WHERE p.categorie IS DISTINCT FROM s.categorie
           OR p.sous_categorie IS DISTINCT FROM s.sous_categorie
           OR p.marque IS DISTINCT FROM s.marque
           OR p.fournisseur IS DISTINCT FROM s.fournisseur
           OR p.prix_standard IS DISTINCT FROM s.prix_standard
           OR p.origine_pays IS DISTINCT FROM s.origine_pays;

        UPDATE dwh_mexora.dim_produit p
           SET date_fin = GREATEST(p.date_debut, (CURRENT_DATE - INTERVAL '1 day')::date),
               est_actif = FALSE
        FROM staging_mexora.tmp_dim_produit_changed c
        WHERE p.id_produit_nk = c.id_produit_nk
          AND p.est_actif = TRUE;

        INSERT INTO dwh_mexora.dim_produit (
            id_produit_sk, id_produit_nk, nom_produit, categorie, sous_categorie, marque,
            fournisseur, prix_standard, origine_pays, date_debut, date_fin, est_actif
        )
        SELECT id_produit_sk, id_produit_nk, nom_produit, categorie, sous_categorie, marque,
               fournisseur, prix_standard, origine_pays, CURRENT_DATE, '9999-12-31', TRUE
        FROM staging_mexora.tmp_dim_produit_new;

        INSERT INTO dwh_mexora.dim_produit (
            id_produit_nk, nom_produit, categorie, sous_categorie, marque,
            fournisseur, prix_standard, origine_pays, date_debut, date_fin, est_actif
        )
        SELECT id_produit_nk, nom_produit, categorie, sous_categorie, marque,
               fournisseur, prix_standard, origine_pays, CURRENT_DATE, '9999-12-31', TRUE
        FROM staging_mexora.tmp_dim_produit_changed;

        SELECT setval(
            pg_get_serial_sequence('dwh_mexora.dim_produit', 'id_produit_sk'),
            COALESCE((SELECT MAX(id_produit_sk) FROM dwh_mexora.dim_produit), 1),
            true
        );
    """
    with engine.begin() as conn:
        conn.execute(text(sql))
    logger.info("[LOAD] dim_produit SCD2 appliquée : %s lignes source", len(df))

def charger_faits(df: pd.DataFrame, engine) -> None:
    _stage(df, "fait_ventes", engine, chunksize=10000)
    sql = """
        TRUNCATE TABLE dwh_mexora.fait_ventes RESTART IDENTITY;
        INSERT INTO dwh_mexora.fait_ventes (
            id_commande, id_date, id_produit, id_client, id_region, id_livreur,
            quantite_vendue, prix_unitaire, montant_ht, montant_ttc,
            cout_livraison, delai_livraison_jours, remise_pct, statut_commande
        )
        SELECT id_commande, id_date, id_produit, id_client, id_region, id_livreur,
               quantite_vendue, prix_unitaire, montant_ht, montant_ttc,
               NULL::numeric, delai_livraison_jours, remise_pct, statut_commande
        FROM staging_mexora.stg_fait_ventes;
    """
    with engine.begin() as conn:
        conn.execute(text(sql))
    logger.info("[LOAD] fait_ventes chargée en batch : %s lignes", len(df))


def rafraichir_reporting(engine) -> None:
    with engine.begin() as conn:
        conn.execute(text("SELECT reporting_mexora.refresh_all_views();"))
    logger.info("[LOAD] vues matérialisées rafraîchies")

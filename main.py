import sys
import logging
from datetime import datetime

from config.settings import (
    DB_URL,
    DATE_DEBUT_DIM_TEMPS,
    DATE_FIN_DIM_TEMPS
)
from utils.logger import setup_logger
from extract.extractor import (
    extract_commandes, extract_produits,
    extract_clients, extract_regions
)
from transform.clean_commandes import transform_commandes
from transform.clean_clients import transform_clients
from transform.clean_produits import transform_produits
from transform.build_dimensions import (
    build_dim_temps, build_dim_produit, build_dim_client,
    build_dim_region, build_dim_livreur, build_fait_ventes,
    calculer_segments_clients
)
from load.loader import (
    get_engine, charger_dimension,
    charger_faits, creer_schemas
)

logger = setup_logger()


def run_pipeline():
    start = datetime.now()
    logger.info("=" * 60)
    logger.info("DÉMARRAGE PIPELINE ETL MEXORA")
    logger.info("=" * 60)

    try:
        # ── 1. EXTRACT ────────────────────────────────────────
        logger.info("--- PHASE EXTRACT ---")
        df_commandes_raw = extract_commandes()
        df_produits_raw  = extract_produits()
        df_clients_raw   = extract_clients()
        df_regions_raw   = extract_regions()

        # ── 2. TRANSFORM ──────────────────────────────────────
        logger.info("--- PHASE TRANSFORM ---")
        df_commandes = transform_commandes(df_commandes_raw, df_regions_raw)
        df_clients   = transform_clients(df_clients_raw)
        df_produits  = transform_produits(df_produits_raw)

        # ── BUILD DIMENSIONS ──────────────────────────────────
        logger.info("--- BUILD DIMENSIONS ---")
        dim_temps   = build_dim_temps(DATE_DEBUT_DIM_TEMPS, DATE_FIN_DIM_TEMPS)
        dim_produit = build_dim_produit(df_produits)
        dim_region  = build_dim_region(df_regions_raw)
        dim_livreur = build_dim_livreur(df_commandes)
        dim_client  = build_dim_client(df_clients, df_commandes, df_regions_raw)

        # Mise à jour segments
        segments    = calculer_segments_clients(df_commandes)
        seg_map     = dict(zip(segments["id_client"], segments["segment_client"]))
        dim_client["segment_client"] = dim_client["id_client_nk"].map(seg_map).fillna("Bronze")

        fait_ventes = build_fait_ventes(
            df_commandes, dim_temps, dim_client,
            dim_produit, dim_region, dim_livreur
        )

        # ── 3. LOAD ───────────────────────────────────────────
        logger.info("--- PHASE LOAD ---")
        engine = get_engine(DB_URL)
        creer_schemas(engine)

        charger_dimension(dim_temps,   "dim_temps",   engine)
        charger_dimension(dim_produit, "dim_produit", engine)
        charger_dimension(dim_client,  "dim_client",  engine)
        charger_dimension(dim_region,  "dim_region",  engine)
        charger_dimension(dim_livreur, "dim_livreur", engine)
        charger_faits(fait_ventes, engine)

        duree = (datetime.now() - start).total_seconds()
        logger.info(f"PIPELINE TERMINÉ EN {duree:.2f} secondes")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"ERREUR PIPELINE : {e}", exc_info=True)
        raise


if __name__ == "__main__":
    run_pipeline()
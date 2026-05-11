import pandas as pd
import sqlalchemy
from sqlalchemy import text
import logging

logger = logging.getLogger("mexora_etl")

def get_engine(db_url: str):
    engine = sqlalchemy.create_engine(db_url)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    logger.info("[LOAD] Connexion PostgreSQL OK")
    return engine

def creer_schemas(engine):
    with engine.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS staging_mexora"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS dwh_mexora"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS reporting_mexora"))
        conn.commit()
    logger.info("[LOAD] Schémas créés")

def charger_dimension(df: pd.DataFrame, table_name: str, engine) -> None:
    df.to_sql(
        name=table_name,
        con=engine,
        schema="dwh_mexora",
        if_exists="replace",
        index=False,
        method="multi",
        chunksize=1000,
    )
    logger.info(f"[LOAD] {table_name:<20} : {len(df):>6} lignes")

def charger_faits(df: pd.DataFrame, engine) -> None:
    df.to_sql(
        name="fait_ventes",
        con=engine,
        schema="dwh_mexora",
        if_exists="replace",
        index=False,
        method="multi",
        chunksize=5000,
    )
    logger.info(f"[LOAD] fait_ventes           : {len(df):>6} lignes")
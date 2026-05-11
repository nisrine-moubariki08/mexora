import os

# BASE_DIR = dossier mexora_etl/ (pas config/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

PATH_COMMANDES = os.path.join(DATA_DIR, "commandes_mexora.csv")
PATH_PRODUITS  = os.path.join(DATA_DIR, "produits_mexora.json")
PATH_CLIENTS   = os.path.join(DATA_DIR, "clients_mexora.csv")
PATH_REGIONS   = os.path.join(DATA_DIR, "regions_maroc.csv")

FICHIER_COMMANDES = PATH_COMMANDES
FICHIER_PRODUITS  = PATH_PRODUITS
FICHIER_CLIENTS   = PATH_CLIENTS
FICHIER_REGIONS   = PATH_REGIONS

DB_HOST     = "localhost"
DB_PORT     = 5433
DB_NAME     = "mexora"
DB_USER     = "postgres"
DB_PASSWORD = "nisrine123"
DB_URL      = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

SCHEMA_STAGING   = "staging_mexora"
SCHEMA_DWH       = "dwh_mexora"
SCHEMA_REPORTING = "reporting_mexora"

DATE_DEBUT_DIM_TEMPS = "2020-01-01"
DATE_FIN_DIM_TEMPS   = "2026-12-31"

SEUIL_GOLD   = 15000
SEUIL_SILVER = 5000

RAMADAN_PERIODES = [
    ("2022-04-02", "2022-05-01"),
    ("2023-03-22", "2023-04-20"),
    ("2024-03-10", "2024-04-09"),
    ("2025-03-01", "2025-03-29"),
]

FERIES_MAROC = [
    "2024-01-01", "2024-01-11", "2024-05-01",
    "2024-07-30", "2024-08-14", "2024-11-06", "2024-11-18",
    "2025-01-01", "2025-01-11", "2025-05-01",
    "2025-07-30", "2025-08-14", "2025-11-06", "2025-11-18",
]
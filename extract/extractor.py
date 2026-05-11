import pandas as pd 
import json 
import logging 
import os 
 
logger = logging.getLogger("mexora_etl") 
 
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 
DATA_DIR = os.path.join(BASE_DIR, "data") 
 
PATH_COMMANDES = os.path.join(DATA_DIR, "commandes_mexora.csv") 
PATH_PRODUITS = os.path.join(DATA_DIR, "produits_mexora.json") 
PATH_CLIENTS = os.path.join(DATA_DIR, "clients_mexora.csv") 
PATH_REGIONS = os.path.join(DATA_DIR, "regions_maroc.csv") 
 
def extract_commandes(): 
    df = pd.read_csv(PATH_COMMANDES, dtype=str, encoding="latin-1") 
    logger.info(f"[EXTRACT] commandes : {len(df)} lignes") 
    return df 
 
def extract_produits(): 
    with open(PATH_PRODUITS, "r", encoding="utf-8") as f: 
        data = json.load(f) 
    df = pd.DataFrame(data["produits"]) 
    logger.info(f"[EXTRACT] produits : {len(df)} lignes") 
    return df 
 
def extract_clients(): 
    df = pd.read_csv(PATH_CLIENTS, dtype=str, encoding="latin-1") 
    logger.info(f"[EXTRACT] clients : {len(df)} lignes") 
    return df 
 
def extract_regions(): 
    df = pd.read_csv(PATH_REGIONS, dtype=str, encoding="latin-1") 
    logger.info(f"[EXTRACT] regions : {len(df)} lignes") 

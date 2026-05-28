# utils/logger.py

import logging
import os
from datetime import datetime

def setup_logger():
    """
    Configure le logger principal du pipeline ETL.
    Écrit dans la console ET dans un fichier log horodaté.
    """
    # Crée le dossier logs s'il n'existe pas
    os.makedirs("logs", exist_ok=True)

    # Nom du fichier log avec timestamp
    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file   = f"logs/etl_{timestamp}.log"

    # Format des messages
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Handler fichier
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)

    # Handler console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Logger principal
    logger = logging.getLogger("mexora_etl")
    logger.setLevel(logging.INFO)
    if logger.handlers:
        return logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info(f"Logger initialisé → {log_file}")
    return logger

# Instance globale utilisée partout dans le projet
logger = setup_logger()

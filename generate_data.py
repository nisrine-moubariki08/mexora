import argparse
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

SEED = 42
NOMS = ["Alami", "Benani", "Chraibi", "Dahbi", "El Amrani", "Fassi", "Ghazi", "Hassani", "Idrissi", "Jabri"]
PRENOMS = ["Ahmed", "Fatima", "Youssef", "Amina", "Omar", "Sara", "Karim", "Laila", "Mehdi", "Nadia"]


def generate_regions() -> pd.DataFrame:
    return pd.DataFrame({
        "code_ville": ["TNG", "CAS", "RBT", "MRK", "FES", "AGD", "TET", "OUJ", "KNT", "BEN", "SAF", "MKN"],
        "nom_ville_standard": ["Tanger", "Casablanca", "Rabat", "Marrakech", "Fès", "Agadir", "Tétouan", "Oujda", "Kénitra", "Benguerir", "Safi", "Meknès"],
        "province": ["Tanger-Assilah", "Casablanca", "Rabat", "Marrakech", "Fès", "Agadir-Ida Ou Tanane", "Tétouan", "Oujda-Angad", "Kénitra", "Rehamna", "Safi", "Meknès"],
        "region_admin": ["Tanger-Tétouan-Al Hoceïma", "Casablanca-Settat", "Rabat-Salé-Kénitra", "Marrakech-Safi", "Fès-Meknès", "Souss-Massa", "Tanger-Tétouan-Al Hoceïma", "Oriental", "Rabat-Salé-Kénitra", "Marrakech-Safi", "Marrakech-Safi", "Fès-Meknès"],
        "zone_geo": ["Nord", "Centre", "Centre", "Sud", "Centre", "Sud", "Nord", "Est", "Centre", "Sud", "Sud", "Centre"],
        "population": [1200000, 3700000, 580000, 930000, 1200000, 420000, 380000, 490000, 430000, 90000, 310000, 630000],
        "code_postal": ["90000", "20000", "10000", "40000", "30000", "80000", "93000", "60000", "14000", "43150", "46000", "50000"],
    })


def generate_products(n_products: int) -> list[dict]:
    categories = {
        "Électronique": ["Smartphones", "Ordinateurs", "Accessoires"],
        "Mode": ["Vêtements", "Chaussures", "Accessoires"],
        "Alimentation": ["Épicerie", "Boissons", "Produits frais"],
        "Maison": ["Cuisine", "Décoration", "Rangement"],
    }
    brands = ["Apple", "Samsung", "Nike", "Adidas", "Marjane", "Carrefour", "Ikea", "Xiaomi"]
    products = []
    for i in range(1, n_products + 1):
        category = random.choice(list(categories.keys()))
        noisy_category = random.choice([category, category.lower(), category.upper()])
        products.append({
            "id_produit": f"P{i:03d}",
            "nom": f"{random.choice(['Pack', 'Article', 'Produit', 'Selection'])} {i}",
            "categorie": noisy_category,
            "sous_categorie": random.choice(categories[category]),
            "marque": random.choice(brands),
            "fournisseur": f"Fournisseur {random.randint(1, 15)}",
            "prix_catalogue": random.choice([round(random.uniform(25, 15000), 2), None, 0]),
            "origine_pays": random.choice(["Maroc", "France", "Chine", "USA", "Turquie", None]),
            "date_creation": (datetime(2020, 1, 1) + timedelta(days=random.randint(0, 1600))).strftime("%Y-%m-%d"),
            "actif": random.choice([True, True, True, False]),
        })
    return products


def generate_clients(n_clients: int) -> pd.DataFrame:
    villes_sales = [
        "Tanger", "tanger", "TNG", "TANGER", "Tnja", "Casablanca", "Casa",
        "Rabat", "Marrakech", "Fes", "Fès", "Agadir", "Ville Fantome", ""
    ]
    rows = []
    for i in range(1, n_clients + 1):
        email = f"client{i}@{random.choice(['gmail.com', 'outlook.com', 'mexora.ma'])}"
        if random.random() < 0.07:
            email = random.choice([email.replace("@", ""), f"client{i}@invalid", "", None])
        rows.append({
            "id_client": f"C{i:05d}",
            "nom": random.choice(NOMS),
            "prenom": random.choice(PRENOMS),
            "email": email,
            "date_naissance": (datetime(1950, 1, 1) + timedelta(days=random.randint(0, 26000))).strftime("%Y-%m-%d"),
            "sexe": random.choice(["M", "F", "m", "f", "1", "0", "Homme", "Femme", "male", "female", ""]),
            "ville": random.choice(villes_sales),
            "telephone": random.choice([f"06{random.randint(10000000, 99999999)}", "0600", "", None]),
            "date_inscription": (datetime(2021, 1, 1) + timedelta(days=random.randint(0, 1500))).strftime("%Y-%m-%d"),
            "canal_acquisition": random.choice(["SEO", "Ads", "Email", "Partenaire", "Direct", None]),
        })

    # Doublons volontaires : même email, id client différent.
    for i in range(20):
        duplicated = rows[i].copy()
        duplicated["id_client"] = f"C{n_clients + i + 1:05d}"
        rows.append(duplicated)
    return pd.DataFrame(rows)


def generate_orders(n_orders: int, products: list[dict], clients: pd.DataFrame) -> pd.DataFrame:
    product_ids = [p["id_produit"] for p in products]
    client_ids = clients["id_client"].tolist()
    statuses = ["livré", "LIVRE", "DONE", "annulé", "KO", "en_cours", "OK", "retourné", ""]
    ville_sales = ["Tanger", "tanger", "TNG", "TANGER", "Tnja", "Casablanca", "Casa", "Rabat", "Marrakech", "Fès", "Fes", "Agadir", "Nowhere"]
    rows = []
    for i in range(1, n_orders + 1):
        date_cmd = datetime(2023, 1, 1) + timedelta(days=random.randint(0, 1094))
        date_fmt = random.choice([
            date_cmd.strftime("%d/%m/%Y"),
            date_cmd.strftime("%Y-%m-%d"),
            date_cmd.strftime("%b %d %Y"),
            "32/13/2024" if random.random() < 0.01 else date_cmd.strftime("%d-%m-%Y"),
        ])
        rows.append({
            "id_commande": f"CMD{random.randint(1, int(n_orders * 0.97)):07d}",
            "id_client": random.choice(client_ids),
            "id_produit": random.choice(product_ids),
            "date_commande": date_fmt,
            "quantite": random.choice([
                random.randint(1, 5), random.randint(1, 5), random.randint(1, 5),
                random.randint(-3, -1), 0, None
            ]),
            "prix_unitaire": random.choice([
                round(random.uniform(20, 12000), 2), round(random.uniform(20, 12000), 2),
                round(random.uniform(20, 12000), 2), 0, None
            ]),
            "statut": random.choice(statuses),
            "ville_livraison": random.choice(ville_sales),
            "mode_paiement": random.choice(["Carte", "Cash", "Virement", "PayPal", ""]),
            "id_livreur": random.choice([f"L{random.randint(1, 60):03d}", None, "", "-"]),
            "date_livraison": (date_cmd + timedelta(days=random.randint(-2, 10))).strftime("%Y-%m-%d") if random.random() > 0.08 else "",
        })
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Génère les données réalistes Mexora avec anomalies contrôlées.")
    parser.add_argument("--orders", type=int, default=50000)
    parser.add_argument("--clients", type=int, default=2500)
    parser.add_argument("--products", type=int, default=120)
    args = parser.parse_args()

    random.seed(SEED)
    np.random.seed(SEED)
    DATA_DIR.mkdir(exist_ok=True)

    regions = generate_regions()
    products = generate_products(args.products)
    clients = generate_clients(args.clients)
    orders = generate_orders(args.orders, products, clients)

    regions.to_csv(DATA_DIR / "regions_maroc.csv", index=False, encoding="utf-8")
    clients.to_csv(DATA_DIR / "clients_mexora.csv", index=False, encoding="utf-8")
    orders.to_csv(DATA_DIR / "commandes_mexora.csv", index=False, encoding="utf-8")
    with open(DATA_DIR / "produits_mexora.json", "w", encoding="utf-8") as f:
        json.dump({"produits": products}, f, ensure_ascii=False, indent=2)

    print("Données Mexora générées avec succès")
    print(f"Commandes : {len(orders)}")
    print(f"Clients   : {len(clients)}")
    print(f"Produits  : {len(products)}")
    print(f"Régions   : {len(regions)}")


if __name__ == "__main__":
    main()

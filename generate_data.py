# data/generate_data.py
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
import random

np.random.seed(42)
random.seed(42)

# --- Génération des régions ---
regions_data = {
    "code_ville": ["TNG", "CAS", "RBT", "MRK", "FES", "AGD", "TET", "OUJ", "KHN", "BEN"],
    "nom_ville_standard": ["Tanger", "Casablanca", "Rabat", "Marrakech", "Fès", "Agadir", "Tétouan", "Oujda", "Kénitra", "Benguerir"],
    "province": ["Tanger-Assilah", "Casablanca", "Rabat", "Marrakech", "Fès", "Agadir-Ida Ou Tanane", "Tétouan", "Oujda-Angad", "Kénitra", "Rehamna"],
    "region_admin": ["Tanger-Tétouan-Al Hoceïma", "Casablanca-Settat", "Rabat-Salé-Kénitra", "Marrakech-Safi", "Fès-Meknès", "Souss-Massa", "Tanger-Tétouan-Al Hoceïma", "Oriental", "Rabat-Salé-Kénitra", "Marrakech-Safi"],
    "zone_geo": ["Nord", "Centre", "Centre", "Sud", "Centre", "Sud", "Nord", "Est", "Centre", "Sud"],
    "population": [1200000, 3700000, 580000, 930000, 1200000, 420000, 380000, 490000, 430000, 90000],
    "code_postal": ["90000", "20000", "10000", "40000", "30000", "80000", "93000", "60000", "14000", "43150"]
}
df_regions = pd.DataFrame(regions_data)
df_regions.to_csv("regions_maroc.csv", index=False, encoding="utf-8")

# --- Génération des produits ---
categories = ["Électronique", "Mode", "Alimentation"]
sous_cat = {
    "Électronique": ["Smartphones", "Ordinateurs", "Accessoires"],
    "Mode": ["Vêtements", "Chaussures", "Accessoires"],
    "Alimentation": ["Épicerie", "Boissons", "Produits frais"]
}
produits = []
for i in range(1, 51):
    cat = random.choice(categories)
    produits.append({
        "id_produit": f"P{i:03d}",
        "nom": f"Produit {i}",
        "categorie": random.choice([cat, cat.lower(), cat.upper()]),  # Casse incohérente
        "sous_categorie": random.choice(sous_cat[cat]),
        "marque": random.choice(["Apple", "Samsung", "Nike", "Adidas", "Marjane", "Carrefour"]),
        "fournisseur": f"Fournisseur {random.randint(1,10)}",
        "prix_catalogue": random.choice([random.uniform(100, 15000), None]),
        "origine_pays": random.choice(["Maroc", "France", "Chine", "USA", "Turquie"]),
        "date_creation": (datetime(2020,1,1) + timedelta(days=random.randint(0, 1500))).strftime("%Y-%m-%d"),
        "actif": random.choice([True, True, True, False])  # 25% inactifs
    })
with open("produits_mexora.json", "w", encoding="utf-8") as f:
    json.dump({"produits": produits}, f, ensure_ascii=False, indent=2)

# --- Génération des clients ---
noms = ["Alami", "Benani", "Chraibi", "Dahbi", "El Amrani", "Fassi", "Ghazi", "Hassani"]
prenoms = ["Ahmed", "Fatima", "Youssef", "Amina", "Omar", "Sara", "Karim", "Laila"]
clients = []
for i in range(1, 1001):
    email = f"client{i}@{'gmail' if random.random() > 0.1 else 'invalid'}.com"
    if random.random() < 0.05:
        email = email.replace("@", "")  # Email invalide
    
    sexe_var = random.choice(["M", "F", "m", "f", "1", "0", "Homme", "Femme", "male", "female", ""])
    
    clients.append({
        "id_client": f"C{i:04d}",
        "nom": random.choice(noms),
        "prenom": random.choice(prenoms),
        "email": email,
        "date_naissance": (datetime(1950,1,1) + timedelta(days=random.randint(0, 25000))).strftime("%Y-%m-%d"),
        "sexe": sexe_var,
        "ville": random.choice(["Tanger", "tanger", "TNG", "TANGER", "Tnja", "Casablanca", "Rabat", "Marrakech"]),
        "telephone": f"06{random.randint(10000000, 99999999)}",
        "date_inscription": (datetime(2022,1,1) + timedelta(days=random.randint(0, 800))).strftime("%Y-%m-%d"),
        "canal_acquisition": random.choice(["SEO", "Ads", "Email", "Partenaire", "Direct"])
    })
# Ajouter quelques doublons d'emails
for i in range(5):
    clients.append({**clients[i], "id_client": f"C{1001+i:04d}"})
df_clients = pd.DataFrame(clients)
df_clients.to_csv("clients_mexora.csv", index=False, encoding="utf-8")

# --- Génération des commandes (50 000 lignes) ---
commandes = []
produit_ids = [p["id_produit"] for p in produits]
client_ids = [c["id_client"] for c in clients]
status_options = ["livré", "LIVRE", "DONE", "annulé", "KO", "en_cours", "OK", "retourné", ""]

for i in range(1, 50001):
    date_cmd = datetime(2023, 1, 1) + timedelta(days=random.randint(0, 730))
    date_fmt = random.choice([
        date_cmd.strftime("%d/%m/%Y"),
        date_cmd.strftime("%Y-%m-%d"),
        date_cmd.strftime("%b %d %Y")
    ])
    
    ville = random.choice(["Tanger", "tanger", "TNG", "TANGER", "Tnja", "Casablanca", "Rabat", "Marrakech", "Fès", "Agadir"])
    
    commandes.append({
        "id_commande": f"CMD{random.randint(1, 48500):06d}",  # Doublons intentionnels (~3%)
        "id_client": random.choice(client_ids),
        "id_produit": random.choice(produit_ids),
        "date_commande": date_fmt,
        "quantite": random.choice([random.randint(1, 5), random.randint(-3, -1), 0]),  # Négatifs possibles
        "prix_unitaire": random.choice([round(random.uniform(50, 12000), 2), 0]),  # Prix 0 possibles
        "statut": random.choice(status_options),
        "ville_livraison": ville,
        "mode_paiement": random.choice(["Carte", "Cash", "Virement", "PayPal"]),
        "id_livreur": random.choice([f"L{random.randint(1,50):03d}", None, None, None, None, None, None]),  # 7% manquants
        "date_livraison": (date_cmd + timedelta(days=random.randint(1, 7))).strftime("%Y-%m-%d") if random.random() > 0.1 else ""
    })

df_commandes = pd.DataFrame(commandes)
df_commandes.to_csv("commandes_mexora.csv", index=False, encoding="utf-8")

print("✅ Données générées avec succès !")
print(f"   Commandes : {len(df_commandes)} lignes")
print(f"   Clients : {len(df_clients)} lignes")
print(f"   Produits : {len(produits)} lignes")
print(f"   Régions : {len(df_regions)} lignes")
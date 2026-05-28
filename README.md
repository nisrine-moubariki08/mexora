# Mexora Analytics - Data Warehouse décisionnel

Projet académique de Data Engineering : construction from scratch d'un entrepôt de données PostgreSQL alimenté par un pipeline ETL Python. Le modèle cible est un schéma en étoile optimisé pour l'analyse des ventes, des clients, des produits, des régions et des livreurs.

## Architecture

```text
data/*.csv, *.json
        |
        v
extract/           lecture robuste des sources
        |
        v
transform/         nettoyage, standardisation, dimensions, faits
        |
        v
staging_mexora     tables temporaires de chargement batch
        |
        v
dwh_mexora         star schema PostgreSQL
        |
        v
reporting_mexora   vues matérialisées pour dashboard BI
```

## Modèle dimensionnel

Grain de `dwh_mexora.fait_ventes` : une ligne représente une ligne de commande pour un produit vendu à un client, à une date, dans une région de livraison, éventuellement prise en charge par un livreur.

Dimensions :

- `dim_temps` : calendrier analytique, mois, trimestre, année, week-end, jours fériés, Ramadan.
- `dim_client` : client nettoyé, email, tranche d'âge, ville, segment. SCD Type 1 pour corrections simples.
- `dim_produit` : produit, catégorie, sous-catégorie, marque, fournisseur, prix standard. SCD Type 2 pour conserver l'historique des changements.
- `dim_region` : ville standardisée, province, région administrative, zone géographique.
- `dim_livreur` : livreur, transport et zone de couverture.

Mesures principales :

- `quantite_vendue`
- `prix_unitaire`
- `montant_ht`
- `montant_ttc`
- `delai_livraison_jours`
- `remise_pct`

## SCD

`dim_client` applique une SCD Type 1 : une correction d'email ou de données descriptives écrase la valeur existante via `ON CONFLICT (id_client_nk) DO UPDATE`.

`dim_produit` applique une SCD Type 2 : si une catégorie, sous-catégorie, marque, fournisseur, prix ou origine change, l'ancienne ligne active est fermée avec `date_fin` et `est_actif = false`, puis une nouvelle version est insérée avec `est_actif = true`.

## Vues matérialisées BI

Le schéma `reporting_mexora` expose :

- `mv_ca_mensuel_region` : chiffre d'affaires mensuel par région.
- `mv_top_produits_trimestre` : classement des produits par trimestre et catégorie.
- `mv_performance_livreurs` : délais moyens et taux de retard par livreur.

Rafraîchissement :

```sql
SELECT reporting_mexora.refresh_all_views();
```

## Installation

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Configurer PostgreSQL dans `config/settings.py` :

```python
DB_HOST = "localhost"
DB_PORT = 5433
DB_NAME = "mexora"
DB_USER = "postgres"
DB_PASSWORD = "..."
```

## Exécution

Générer les données sources avec anomalies simulées :

```bash
python generate_data.py --orders 50000 --clients 2500 --products 120
```

Créer et alimenter le Data Warehouse :

```bash
python main.py
```

Vérifier l'intégrité :

```bash
psql -d mexora -f sql/check_integrity.sql
```

## Anomalies simulées

Le générateur crée volontairement :

- doublons de commandes et d'emails clients ;
- valeurs nulles ;
- emails invalides ;
- formats de dates hétérogènes ;
- villes marocaines incohérentes ou inconnues ;
- prix à zéro ;
- quantités négatives ;
- livreurs manquants ;
- délais de livraison négatifs ou absents.

Le pipeline transforme ou rejette ces anomalies selon des règles explicites dans `transform/`.

## Optimisation PostgreSQL

Le DDL ajoute :

- index simples sur les clés étrangères de la table de faits ;
- index composés pour les analyses période/région et période/produit ;
- index partiel sur les ventes livrées, car les dashboards filtrent majoritairement `statut_commande = 'livré'` ;
- index sur les vues matérialisées pour accélérer les lectures BI.

## Dashboard BI proposé

Pages recommandées :

- Vue exécutive : CA, panier moyen, commandes, clients actifs, évolution mensuelle.
- Régions : CA par région administrative, zone géographique, villes à anomalies.
- Produits : top produits trimestriels, catégories, marques, contribution au CA.
- Clients : segments Gold/Silver/Bronze, acquisition, villes, qualité email.
- Livraison : délai moyen, taux de retard, performance livreurs.

Questions métier couvertes :

- Quelle est l'évolution du CA mensuel par région ?
- Quels produits dominent chaque trimestre ?
- Quelles régions génèrent le plus de ventes ?
- Quels segments clients contribuent le plus au CA ?
- Quels livreurs ont les meilleurs délais et le moins de retards ?

## Livrables académiques

Les livrables finaux sont récapitulés dans :

- `livrables/README_livrables.md`
- `livrables/grille_conformite.md`

Générer les fichiers image/PDF :

```bash
python scripts/generate_livrables.py
```

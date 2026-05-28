# Rapport des transformations - Mexora Analytics

## Objectif

Mexora Analytics construit un Data Warehouse décisionnel PostgreSQL à partir de sources opérationnelles simulées : commandes, clients, produits et régions. Le pipeline applique une démarche ETL complète : extraction, nettoyage, modélisation dimensionnelle, chargement batch et production de vues matérialisées BI.

## Architecture Data Warehouse

```text
Sources brutes
  - data/commandes_mexora.csv
  - data/clients_mexora.csv
  - data/regions_maroc.csv
  - data/produits_mexora.json

ETL Python
  - extract/    : lecture CSV/JSON
  - transform/  : nettoyage et construction étoile
  - load/       : staging, batch insert, upsert, SCD

PostgreSQL
  - staging_mexora   : tables temporaires de chargement
  - dwh_mexora       : schéma en étoile
  - reporting_mexora : vues matérialisées pour dashboard
```

## Granularité

La table `fact_ventes` a pour grain : une ligne = une ligne de commande pour un produit.

Ce grain est choisi car il permet :

- d'analyser le chiffre d'affaires au niveau produit, client, date, région et livreur ;
- d'agréger facilement vers le mois, le trimestre, la catégorie ou la région ;
- de conserver des mesures additives fiables : quantité, montant HT, montant TTC ;
- de calculer des indicateurs semi-additifs comme les délais de livraison.

## Schéma en étoile

Table de faits :

- `dwh_mexora.fait_ventes`

Dimensions :

- `dwh_mexora.dim_temps`
- `dwh_mexora.dim_client`
- `dwh_mexora.dim_produit`
- `dwh_mexora.dim_region`
- `dwh_mexora.dim_livreur`

Les dimensions utilisent des clés substituts (`*_sk` ou identifiants techniques) afin de découpler le Data Warehouse des clés naturelles sources. Les clés étrangères de la table de faits pointent vers ces clés substituts.

## Transformations des commandes

Règles appliquées :

- suppression des doublons sur `id_commande` en conservant la dernière occurrence ;
- parsing multi-format de `date_commande` ;
- suppression des dates invalides ;
- standardisation des villes de livraison vers les villes marocaines connues ;
- normalisation des statuts vers `livré`, `annulé`, `en_cours`, `retourné`, `inconnu` ;
- rejet des quantités nulles ou négatives ;
- rejet des prix unitaires nuls ou négatifs ;
- remplacement des livreurs manquants par la clé naturelle `-1` ;
- calcul de `montant_ht`, `montant_ttc` et `delai_livraison_jours`.

## Transformations des clients

Règles appliquées :

- déduplication par email normalisé ;
- normalisation du sexe ;
- validation des dates de naissance ;
- calcul de l'âge et de la tranche d'âge ;
- invalidation des emails mal formés ;
- standardisation de la ville ;
- calcul du segment client selon le CA récent : `Gold`, `Silver`, `Bronze`.

## Transformations des produits

Règles appliquées :

- standardisation des catégories, sous-catégories, marques et noms ;
- conversion numérique du prix catalogue ;
- imputation des prix manquants par médiane de sous-catégorie, puis médiane globale ;
- normalisation du flag `actif`.

## Justification SCD

### SCD Type 1 - Client

Les corrections simples d'un client, notamment l'email, ne nécessitent pas d'historique analytique. L'objectif est de disposer de la meilleure version connue de l'information.

Exemple :

- Ancien email : `client10gmail.com`
- Email corrigé : `client10@gmail.com`

Le chargement fait un `UPSERT` sur `id_client_nk` et écrase `email`, `ville`, `segment_client` ou `canal_acquisition`.

### SCD Type 2 - Produit

Les changements de catégorie produit doivent être historisés, car ils impactent l'analyse des ventes dans le temps.

Exemple :

- Produit `P010` classé initialement en `Mode`
- Reclassé plus tard en `Maison`

Le pipeline ferme la version active :

- `date_fin = current_date - 1`
- `est_actif = false`

Puis il insère une nouvelle version :

- `date_debut = current_date`
- `date_fin = 9999-12-31`
- `est_actif = true`

## Vues matérialisées

### `mv_ca_mensuel_region`

Objectif : suivre le CA mensuel par région administrative et zone géographique.

Indicateurs :

- CA TTC ;
- CA HT ;
- nombre de commandes ;
- clients actifs ;
- panier moyen ;
- quantités vendues.

### `mv_top_produits_trimestre`

Objectif : identifier les produits les plus performants par trimestre et catégorie.

Indicateurs :

- quantités vendues ;
- CA TTC ;
- rang dans la catégorie.

### `mv_performance_livreurs`

Objectif : mesurer la qualité logistique.

Indicateurs :

- nombre de livraisons ;
- délai moyen ;
- nombre de retards ;
- taux de retard.

Stratégie de rafraîchissement :

- après chaque chargement ETL complet ;
- via `SELECT reporting_mexora.refresh_all_views();` ;
- planifiable par cron, Airflow ou pgAgent dans une version industrialisée.

## Optimisation SQL

Index simples :

- `idx_fv_date`
- `idx_fv_produit`
- `idx_fv_client`
- `idx_fv_region`
- `idx_fv_livreur`

Utilité : accélérer les jointures entre faits et dimensions.

Index composés :

- `idx_fv_date_region`
- `idx_fv_date_produit`

Utilité : optimiser les analyses fréquentes par période, région et produit.

Index partiel :

- `idx_fv_livres_date_region`

Utilité : réduire la taille de l'index pour les requêtes BI qui filtrent majoritairement les ventes livrées.

Index SCD :

- `ux_dim_produit_nk_actif`
- `idx_dim_produit_nk_periode`

Utilité : garantir une seule version active et accélérer la recherche historique.

## Dashboard BI

### Page 1 - Vue exécutive

KPIs :

- CA TTC ;
- nombre de commandes ;
- panier moyen ;
- clients actifs ;
- taux de commandes livrées.

Graphiques :

- courbe du CA mensuel ;
- barres CA par région ;
- top 10 produits.

Filtres :

- année ;
- mois ;
- région ;
- catégorie.

### Page 2 - Analyse régionale

KPIs :

- CA par région ;
- volume vendu ;
- panier moyen régional.

Graphiques :

- carte ou bar chart des régions ;
- évolution mensuelle par région ;
- villes non reconnues en source.

### Page 3 - Produits

KPIs :

- CA par catégorie ;
- quantité vendue ;
- contribution top produits.

Graphiques :

- top produits par trimestre ;
- classement par catégorie ;
- répartition CA par marque.

### Page 4 - Clients

KPIs :

- clients actifs ;
- CA par segment ;
- panier moyen par segment.

Graphiques :

- segments Gold/Silver/Bronze ;
- acquisition par canal ;
- qualité email.

### Page 5 - Livraison

KPIs :

- délai moyen ;
- taux de retard ;
- nombre de livraisons.

Graphiques :

- performance par livreur ;
- retards par mois ;
- délais par zone.

## Questions métier couvertes

1. Quelle est l'évolution du chiffre d'affaires mensuel par région ?
2. Quels produits réalisent les meilleures performances chaque trimestre ?
3. Quelles régions et zones géographiques génèrent le plus de ventes ?
4. Quels segments clients contribuent le plus au CA ?
5. Quels livreurs affichent les meilleurs délais et les taux de retard les plus faibles ?

## Qualité et limites

Le pipeline journalise chaque étape et conserve les anomalies simulées au niveau source. Les transformations rejettent les lignes incompatibles avec le modèle analytique, notamment les dates invalides, prix nuls et quantités négatives. Dans un contexte de production réel, les lignes rejetées seraient écrites dans une table de quarantaine dédiée pour audit métier.

# Dashboard final - Mexora Analytics

Ce dossier fournit la structure complète du dashboard BI final. Il est conçu pour Metabase, mais les mêmes vues SQL peuvent être utilisées dans Power BI.

## Source de données

Connexion PostgreSQL :

- base : `mexora`
- schémas : `dwh_mexora`, `reporting_mexora`
- vues principales : `mv_ca_mensuel_region`, `mv_top_produits_trimestre`, `mv_performance_livreurs`

## Pages du dashboard

### 1. Vue exécutive

Visuels :

- KPI CA TTC
- KPI nombre de commandes
- KPI clients actifs
- KPI panier moyen
- courbe CA mensuel
- bar chart CA par région

Question métier : suivre l'évolution globale et régionale du chiffre d'affaires.

### 2. Régions

Visuels :

- classement des régions par CA
- CA par zone géographique
- panier moyen par région
- évolution mensuelle régionale

Question métier : identifier les régions les plus contributrices.

### 3. Produits

Visuels :

- top 10 produits par trimestre
- CA par catégorie
- quantités vendues par marque
- rang produit dans catégorie

Question métier : détecter les produits et catégories à prioriser.

### 4. Clients

Visuels :

- CA par segment Gold/Silver/Bronze
- nombre de clients par segment
- panier moyen par segment
- acquisition par canal

Question métier : comprendre la contribution des segments clients.

### 5. Livraison

Visuels :

- délai moyen par livreur
- taux de retard par livreur
- nombre de livraisons par mois
- classement des livreurs à risque

Question métier : piloter la performance logistique.

## Filtres recommandés

- Année
- Mois
- Région administrative
- Zone géographique
- Catégorie produit
- Segment client
- Statut commande

## Fichier SQL

Le fichier `metabase_dashboard.sql` contient les requêtes des 5 questions métier et les KPIs globaux. Dans Metabase, créer une question SQL pour chaque bloc, choisir la visualisation indiquée, puis les assembler dans un dashboard nommé `Mexora Analytics - Dashboard DW`.

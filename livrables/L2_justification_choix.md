# L2 - Justification des choix

## Modélisation

Le projet utilise un schéma en étoile centré sur `dwh_mexora.fait_ventes`. Ce modèle est adapté aux usages BI car il réduit la complexité des jointures et facilite les agrégations par date, région, client, produit et livreur.

## Granularité

Le grain de la table de faits est : une ligne = une ligne de commande produit.

Ce choix permet de conserver le détail analytique nécessaire pour répondre aux questions métier :

- chiffre d'affaires mensuel par région ;
- top produits par trimestre ;
- contribution des segments clients ;
- performance des livreurs.

## Additivité

Mesures additives :

- `quantite_vendue`
- `montant_ht`
- `montant_ttc`

Mesure semi-additive :

- `delai_livraison_jours`, à analyser par moyenne, médiane ou percentile.

Mesure non additive :

- `remise_pct`, à recalculer ou moyenner avec prudence.

## SCD

`dim_client` utilise une SCD Type 1. Les corrections d'email ou de ville écrasent l'ancienne valeur, car l'historique de correction n'apporte pas de valeur décisionnelle forte.

`dim_produit` utilise une SCD Type 2. Les changements de catégorie, marque, fournisseur, prix standard ou origine doivent être historisés pour conserver la cohérence des analyses passées.

## PostgreSQL

Les index simples accélèrent les jointures. Les index composés optimisent les analyses période/région et période/produit. L'index partiel sur les ventes livrées cible le cas BI le plus fréquent : le calcul du CA réel.

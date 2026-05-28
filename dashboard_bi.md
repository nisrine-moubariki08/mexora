# Dashboard BI - Mexora Analytics

## Objectif

Le dashboard doit permettre au comité métier de piloter les ventes, la performance produit, la répartition régionale, la contribution client et la qualité de livraison.

## Questions métier

1. Quelle est l'évolution du chiffre d'affaires mensuel par région ?
2. Quels sont les meilleurs produits par trimestre ?
3. Quelles régions génèrent le plus de ventes ?
4. Quels segments clients contribuent le plus au chiffre d'affaires ?
5. Quels livreurs sont les plus performants ?

## Page 1 - Vue exécutive

KPIs :

- CA TTC
- CA HT
- Nombre de commandes
- Clients actifs
- Panier moyen

Graphiques :

- courbe CA mensuel ;
- barres CA par région ;
- top 10 produits ;
- répartition des statuts commandes.

Filtres :

- année ;
- mois ;
- région ;
- catégorie ;
- segment client.

Source principale :

- `reporting_mexora.mv_ca_mensuel_region`

## Page 2 - Régions

KPIs :

- CA par région administrative ;
- volume vendu ;
- nombre de clients actifs ;
- panier moyen régional.

Graphiques :

- bar chart régions ;
- évolution mensuelle par région ;
- CA par zone géographique.

Tables de détail :

- top villes ;
- anomalies de villes non reconnues si table de quarantaine ajoutée.

## Page 3 - Produits

KPIs :

- CA par catégorie ;
- quantité vendue ;
- nombre de produits actifs ;
- contribution du top 10.

Graphiques :

- classement des produits par trimestre ;
- CA par catégorie ;
- CA par marque ;
- évolution des catégories produits.

Source principale :

- `reporting_mexora.mv_top_produits_trimestre`

## Page 4 - Clients

KPIs :

- clients actifs ;
- CA par segment ;
- panier moyen par segment ;
- nouveaux clients.

Graphiques :

- répartition Gold/Silver/Bronze ;
- acquisition par canal ;
- CA par segment ;
- distribution par tranche d'âge.

Tables :

- clients à fort CA ;
- emails invalides en source si table de qualité ajoutée.

## Page 5 - Livraison

KPIs :

- délai moyen ;
- taux de retard ;
- nombre de livraisons ;
- livreur le plus performant.

Graphiques :

- performance livreurs ;
- retards mensuels ;
- délais par zone de couverture.

Source principale :

- `reporting_mexora.mv_performance_livreurs`

## Insights attendus

- identifier les régions à forte croissance ;
- détecter les produits dominants par saison ;
- comprendre la contribution des segments clients ;
- repérer les livreurs avec retard récurrent ;
- prioriser les actions commerciales et logistiques.

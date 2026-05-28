-- ============================================================
-- Mexora Analytics - Questions SQL pour dashboard Metabase
-- Chaque requête correspond à un visuel du dashboard final.
-- ============================================================

-- Q1. Evolution du CA mensuel par région
SELECT
    annee,
    mois,
    region_admin,
    ca_ttc,
    nb_commandes,
    panier_moyen
FROM reporting_mexora.mv_ca_mensuel_region
ORDER BY annee, mois, region_admin;

-- Q2. Top produits par trimestre
SELECT
    annee,
    trimestre,
    categorie,
    nom_produit,
    marque,
    quantite_vendue,
    ca_ttc,
    rang_categorie
FROM reporting_mexora.mv_top_produits_trimestre
WHERE rang_categorie <= 10
ORDER BY annee, trimestre, categorie, rang_categorie;

-- Q3. Régions les plus performantes
SELECT
    region_admin,
    zone_geo,
    SUM(ca_ttc) AS ca_ttc,
    SUM(nb_commandes) AS nb_commandes,
    SUM(nb_clients) AS nb_clients,
    ROUND(SUM(ca_ttc) / NULLIF(SUM(nb_commandes), 0), 2) AS panier_moyen
FROM reporting_mexora.mv_ca_mensuel_region
GROUP BY region_admin, zone_geo
ORDER BY ca_ttc DESC;

-- Q4. Contribution CA par segment client
SELECT
    c.segment_client,
    COUNT(DISTINCT f.id_client) AS nb_clients,
    COUNT(DISTINCT f.id_commande) AS nb_commandes,
    SUM(f.montant_ttc) AS ca_ttc,
    ROUND(SUM(f.montant_ttc) / NULLIF(COUNT(DISTINCT f.id_commande), 0), 2) AS panier_moyen
FROM dwh_mexora.fait_ventes f
JOIN dwh_mexora.dim_client c ON c.id_client_sk = f.id_client
WHERE f.statut_commande = 'livré'
GROUP BY c.segment_client
ORDER BY ca_ttc DESC;

-- Q5. Performance des livreurs
SELECT
    annee,
    mois,
    id_livreur_nk,
    nom_livreur,
    zone_couverture,
    nb_livraisons,
    delai_moyen_jours,
    taux_retard_pct
FROM reporting_mexora.mv_performance_livreurs
ORDER BY annee, mois, taux_retard_pct DESC;

-- KPI global - Vue exécutive
SELECT
    SUM(montant_ttc) AS ca_ttc,
    COUNT(DISTINCT id_commande) AS nb_commandes,
    COUNT(DISTINCT id_client) AS nb_clients_actifs,
    ROUND(SUM(montant_ttc) / NULLIF(COUNT(DISTINCT id_commande), 0), 2) AS panier_moyen,
    ROUND(
        COUNT(*) FILTER (WHERE statut_commande = 'livré') * 100.0 / NULLIF(COUNT(*), 0),
        2
    ) AS taux_livraison_pct
FROM dwh_mexora.fait_ventes;

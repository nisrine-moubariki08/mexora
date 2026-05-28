-- ============================================================
-- Mexora Analytics - contrôles qualité Data Warehouse
-- ============================================================

SELECT 'FK orphelines vers dim_temps' AS check_name, COUNT(*) AS nb_anomalies
FROM dwh_mexora.fait_ventes f
LEFT JOIN dwh_mexora.dim_temps d ON d.id_date = f.id_date
WHERE d.id_date IS NULL

UNION ALL
SELECT 'FK orphelines vers dim_produit', COUNT(*)
FROM dwh_mexora.fait_ventes f
LEFT JOIN dwh_mexora.dim_produit d ON d.id_produit_sk = f.id_produit
WHERE d.id_produit_sk IS NULL

UNION ALL
SELECT 'FK orphelines vers dim_client', COUNT(*)
FROM dwh_mexora.fait_ventes f
LEFT JOIN dwh_mexora.dim_client d ON d.id_client_sk = f.id_client
WHERE d.id_client_sk IS NULL

UNION ALL
SELECT 'FK orphelines vers dim_region', COUNT(*)
FROM dwh_mexora.fait_ventes f
LEFT JOIN dwh_mexora.dim_region d ON d.id_region = f.id_region
WHERE d.id_region IS NULL

UNION ALL
SELECT 'FK orphelines vers dim_livreur', COUNT(*)
FROM dwh_mexora.fait_ventes f
LEFT JOIN dwh_mexora.dim_livreur d ON d.id_livreur = f.id_livreur
WHERE f.id_livreur IS NOT NULL AND d.id_livreur IS NULL;

SELECT 'Produits avec plusieurs versions actives' AS check_name, COUNT(*) AS nb_anomalies
FROM (
    SELECT id_produit_nk
    FROM dwh_mexora.dim_produit
    WHERE est_actif = TRUE
    GROUP BY id_produit_nk
    HAVING COUNT(*) > 1
) x

UNION ALL
SELECT 'Clients dupliqués par NK', COUNT(*)
FROM (
    SELECT id_client_nk
    FROM dwh_mexora.dim_client
    GROUP BY id_client_nk
    HAVING COUNT(*) > 1
) x

UNION ALL
SELECT 'Périodes SCD produit incohérentes', COUNT(*)
FROM dwh_mexora.dim_produit
WHERE date_fin < date_debut;

SELECT 'Quantités invalides dans faits' AS check_name, COUNT(*) AS nb_anomalies
FROM dwh_mexora.fait_ventes
WHERE quantite_vendue <= 0

UNION ALL
SELECT 'Prix invalides dans faits', COUNT(*)
FROM dwh_mexora.fait_ventes
WHERE prix_unitaire <= 0

UNION ALL
SELECT 'Montants invalides dans faits', COUNT(*)
FROM dwh_mexora.fait_ventes
WHERE montant_ht <= 0 OR montant_ttc <= 0;

SELECT
    COUNT(*) AS nb_lignes_faits,
    COUNT(DISTINCT id_commande) AS nb_commandes,
    COUNT(DISTINCT id_date) AS nb_dates,
    COUNT(DISTINCT id_produit) AS nb_produits,
    COUNT(DISTINCT id_client) AS nb_clients,
    ROUND(SUM(montant_ttc), 2) AS ca_total_ttc,
    ROUND(AVG(montant_ttc), 2) AS panier_ligne_moyen
FROM dwh_mexora.fait_ventes
WHERE statut_commande = 'livré';

SELECT 'mv_ca_mensuel_region' AS vue, COUNT(*) AS nb_lignes
FROM reporting_mexora.mv_ca_mensuel_region
UNION ALL
SELECT 'mv_top_produits_trimestre', COUNT(*)
FROM reporting_mexora.mv_top_produits_trimestre
UNION ALL
SELECT 'mv_performance_livreurs', COUNT(*)
FROM reporting_mexora.mv_performance_livreurs;

-- ============================================================
-- VÉRIFICATION DE L'INTÉGRITÉ RÉFÉRENTIELLE
-- ============================================================

-- 1. Vérifier les clés étrangères orphelines dans fait_ventes
SELECT 'FK orphelines vers dim_temps' AS check_name,
       COUNT(*) AS nb_anomalies
FROM dwh_mexora.fait_ventes f
LEFT JOIN dwh_mexora.dim_temps t ON f.id_date = t.id_date
WHERE t.id_date IS NULL

UNION ALL

SELECT 'FK orphelines vers dim_produit',
       COUNT(*)
FROM dwh_mexora.fait_ventes f
LEFT JOIN dwh_mexora.dim_produit p ON f.id_produit = p.id_produit_sk
WHERE p.id_produit_sk IS NULL

UNION ALL

SELECT 'FK orphelines vers dim_client',
       COUNT(*)
FROM dwh_mexora.fait_ventes f
LEFT JOIN dwh_mexora.dim_client c ON f.id_client = c.id_client_sk
WHERE c.id_client_sk IS NULL

UNION ALL

SELECT 'FK orphelines vers dim_region',
       COUNT(*)
FROM dwh_mexora.fait_ventes f
LEFT JOIN dwh_mexora.dim_region r ON f.id_region = r.id_region
WHERE r.id_region IS NULL;

-- 2. Vérifier les doublons de natural keys actives dans les dimensions SCD
SELECT 'Doublons dim_produit (NK actifs)' AS check_name,
       COUNT(*) AS nb_anomalies
FROM (
    SELECT id_produit_nk
    FROM dwh_mexora.dim_produit
    WHERE est_actif = TRUE
    GROUP BY id_produit_nk
    HAVING COUNT(*) > 1
) sub

UNION ALL

SELECT 'Doublons dim_client (NK actifs)',
       COUNT(*)
FROM (
    SELECT id_client_nk
    FROM dwh_mexora.dim_client
    WHERE est_actif = TRUE
    GROUP BY id_client_nk
    HAVING COUNT(*) > 1
) sub;

-- 3. Vérifier la cohérence des mesures
SELECT 'Quantités négatives dans faits' AS check_name,
       COUNT(*) AS nb_anomalies
FROM dwh_mexora.fait_ventes
WHERE quantite_vendue <= 0

UNION ALL

SELECT 'Montants nuls ou négatifs',
       COUNT(*)
FROM dwh_mexora.fait_ventes
WHERE montant_ht <= 0 OR montant_ttc <= 0

UNION ALL

SELECT 'Délais livraison négatifs',
       COUNT(*)
FROM dwh_mexora.fait_ventes
WHERE delai_livraison_jours < 0;

-- 4. Statistiques globales
SELECT 
    'FAIT_VENTES' AS table_name,
    COUNT(*) AS nb_lignes,
    COUNT(DISTINCT id_date) AS nb_dates,
    COUNT(DISTINCT id_produit) AS nb_produits,
    COUNT(DISTINCT id_client) AS nb_clients,
    SUM(montant_ttc) AS ca_total,
    AVG(montant_ttc) AS panier_moyen
FROM dwh_mexora.fait_ventes
WHERE statut_commande = 'livré';
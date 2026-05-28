-- ============================================================
-- Mexora Analytics - Data Warehouse PostgreSQL
-- Grain fact_ventes : une ligne = une ligne de commande pour un produit.
-- ============================================================

CREATE SCHEMA IF NOT EXISTS staging_mexora;
CREATE SCHEMA IF NOT EXISTS dwh_mexora;
CREATE SCHEMA IF NOT EXISTS reporting_mexora;

DROP MATERIALIZED VIEW IF EXISTS reporting_mexora.mv_ca_mensuel_region CASCADE;
DROP MATERIALIZED VIEW IF EXISTS reporting_mexora.mv_top_produits_trimestre CASCADE;
DROP MATERIALIZED VIEW IF EXISTS reporting_mexora.mv_performance_livreurs CASCADE;
DROP MATERIALIZED VIEW IF EXISTS reporting_mexora.mv_ca_mensuel CASCADE;
DROP MATERIALIZED VIEW IF EXISTS reporting_mexora.mv_top_produits CASCADE;

DROP TABLE IF EXISTS dwh_mexora.fait_ventes CASCADE;
DROP TABLE IF EXISTS dwh_mexora.dim_temps CASCADE;
DROP TABLE IF EXISTS dwh_mexora.dim_client CASCADE;
DROP TABLE IF EXISTS dwh_mexora.dim_produit CASCADE;
DROP TABLE IF EXISTS dwh_mexora.dim_region CASCADE;
DROP TABLE IF EXISTS dwh_mexora.dim_livreur CASCADE;

CREATE TABLE dwh_mexora.dim_temps (
    id_date           INTEGER PRIMARY KEY,
    date_complete     DATE NOT NULL UNIQUE,
    jour              SMALLINT NOT NULL CHECK (jour BETWEEN 1 AND 31),
    mois              SMALLINT NOT NULL CHECK (mois BETWEEN 1 AND 12),
    trimestre         SMALLINT NOT NULL CHECK (trimestre BETWEEN 1 AND 4),
    annee             SMALLINT NOT NULL,
    semaine           SMALLINT,
    libelle_jour      VARCHAR(20),
    libelle_mois      VARCHAR(20),
    est_weekend       BOOLEAN NOT NULL DEFAULT FALSE,
    est_ferie_maroc   BOOLEAN NOT NULL DEFAULT FALSE,
    periode_ramadan   BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE dwh_mexora.dim_client (
    id_client_sk      SERIAL PRIMARY KEY,
    id_client_nk      VARCHAR(20) NOT NULL UNIQUE,
    nom_complet       VARCHAR(200),
    email             VARCHAR(255),
    tranche_age       VARCHAR(10),
    sexe              VARCHAR(10),
    ville             VARCHAR(100),
    segment_client    VARCHAR(20) CHECK (segment_client IN ('Gold', 'Silver', 'Bronze')),
    canal_acquisition VARCHAR(50),
    date_inscription  DATE,
    date_maj          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE dwh_mexora.dim_produit (
    id_produit_sk     SERIAL PRIMARY KEY,
    id_produit_nk     VARCHAR(20) NOT NULL,
    nom_produit       VARCHAR(200) NOT NULL,
    categorie         VARCHAR(100),
    sous_categorie    VARCHAR(100),
    marque            VARCHAR(100),
    fournisseur       VARCHAR(100),
    prix_standard     NUMERIC(12,2),
    origine_pays      VARCHAR(50),
    date_debut        DATE NOT NULL DEFAULT CURRENT_DATE,
    date_fin          DATE NOT NULL DEFAULT DATE '9999-12-31',
    est_actif         BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT ck_dim_produit_periode CHECK (date_fin >= date_debut)
);

CREATE TABLE dwh_mexora.dim_region (
    id_region         SERIAL PRIMARY KEY,
    ville             VARCHAR(100) NOT NULL UNIQUE,
    province          VARCHAR(100),
    region_admin      VARCHAR(100),
    zone_geo          VARCHAR(50),
    pays              VARCHAR(50) NOT NULL DEFAULT 'Maroc'
);

CREATE TABLE dwh_mexora.dim_livreur (
    id_livreur        SERIAL PRIMARY KEY,
    id_livreur_nk     VARCHAR(20) NOT NULL UNIQUE,
    nom_livreur       VARCHAR(100),
    type_transport    VARCHAR(50),
    zone_couverture   VARCHAR(100)
);

CREATE TABLE dwh_mexora.fait_ventes (
    id_vente              BIGSERIAL PRIMARY KEY,
    id_commande           VARCHAR(30) NOT NULL,
    id_date               INTEGER NOT NULL REFERENCES dwh_mexora.dim_temps(id_date),
    id_produit            INTEGER NOT NULL REFERENCES dwh_mexora.dim_produit(id_produit_sk),
    id_client             INTEGER NOT NULL REFERENCES dwh_mexora.dim_client(id_client_sk),
    id_region             INTEGER NOT NULL REFERENCES dwh_mexora.dim_region(id_region),
    id_livreur            INTEGER REFERENCES dwh_mexora.dim_livreur(id_livreur),
    quantite_vendue       INTEGER NOT NULL CHECK (quantite_vendue > 0),
    prix_unitaire         NUMERIC(12,2) NOT NULL CHECK (prix_unitaire > 0),
    montant_ht            NUMERIC(14,2) NOT NULL CHECK (montant_ht > 0),
    montant_ttc           NUMERIC(14,2) NOT NULL CHECK (montant_ttc > 0),
    cout_livraison        NUMERIC(10,2),
    delai_livraison_jours SMALLINT,
    remise_pct            NUMERIC(5,2) NOT NULL DEFAULT 0 CHECK (remise_pct BETWEEN 0 AND 100),
    statut_commande       VARCHAR(20) NOT NULL CHECK (statut_commande IN ('livré','annulé','en_cours','retourné','inconnu')),
    date_chargement       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Une seule version active par produit : base de la SCD Type 2.
CREATE UNIQUE INDEX IF NOT EXISTS ux_dim_produit_nk_actif
    ON dwh_mexora.dim_produit(id_produit_nk)
    WHERE est_actif = TRUE;

CREATE INDEX IF NOT EXISTS idx_dim_produit_nk_periode
    ON dwh_mexora.dim_produit(id_produit_nk, date_debut, date_fin);

CREATE INDEX IF NOT EXISTS idx_dim_client_segment
    ON dwh_mexora.dim_client(segment_client);

-- Index simples : accélèrent les jointures étoile.
CREATE INDEX IF NOT EXISTS idx_fv_date     ON dwh_mexora.fait_ventes(id_date);
CREATE INDEX IF NOT EXISTS idx_fv_produit  ON dwh_mexora.fait_ventes(id_produit);
CREATE INDEX IF NOT EXISTS idx_fv_client   ON dwh_mexora.fait_ventes(id_client);
CREATE INDEX IF NOT EXISTS idx_fv_region   ON dwh_mexora.fait_ventes(id_region);
CREATE INDEX IF NOT EXISTS idx_fv_livreur  ON dwh_mexora.fait_ventes(id_livreur);

-- Index composés : requêtes CA par période/région et top produits.
CREATE INDEX IF NOT EXISTS idx_fv_date_region
    ON dwh_mexora.fait_ventes(id_date, id_region)
    INCLUDE (montant_ttc, quantite_vendue);

CREATE INDEX IF NOT EXISTS idx_fv_date_produit
    ON dwh_mexora.fait_ventes(id_date, id_produit)
    INCLUDE (montant_ttc);

-- Index partiel : la majorité des analyses BI filtrent les ventes livrées.
CREATE INDEX IF NOT EXISTS idx_fv_livres_date_region
    ON dwh_mexora.fait_ventes(id_date, id_region)
    WHERE statut_commande = 'livré';

CREATE MATERIALIZED VIEW reporting_mexora.mv_ca_mensuel_region AS
SELECT
    t.annee,
    t.mois,
    t.libelle_mois,
    r.region_admin,
    r.zone_geo,
    SUM(f.montant_ttc) AS ca_ttc,
    SUM(f.montant_ht) AS ca_ht,
    COUNT(*) AS nb_lignes_commande,
    COUNT(DISTINCT f.id_commande) AS nb_commandes,
    COUNT(DISTINCT f.id_client) AS nb_clients,
    SUM(f.quantite_vendue) AS quantite_vendue,
    ROUND(SUM(f.montant_ttc) / NULLIF(COUNT(DISTINCT f.id_commande), 0), 2) AS panier_moyen
FROM dwh_mexora.fait_ventes f
JOIN dwh_mexora.dim_temps t ON t.id_date = f.id_date
JOIN dwh_mexora.dim_region r ON r.id_region = f.id_region
WHERE f.statut_commande = 'livré'
GROUP BY t.annee, t.mois, t.libelle_mois, r.region_admin, r.zone_geo
WITH NO DATA;

CREATE MATERIALIZED VIEW reporting_mexora.mv_top_produits_trimestre AS
SELECT
    t.annee,
    t.trimestre,
    p.categorie,
    p.nom_produit,
    p.marque,
    SUM(f.quantite_vendue) AS quantite_vendue,
    SUM(f.montant_ttc) AS ca_ttc,
    RANK() OVER (
        PARTITION BY t.annee, t.trimestre, p.categorie
        ORDER BY SUM(f.montant_ttc) DESC
    ) AS rang_categorie
FROM dwh_mexora.fait_ventes f
JOIN dwh_mexora.dim_temps t ON t.id_date = f.id_date
JOIN dwh_mexora.dim_produit p ON p.id_produit_sk = f.id_produit
WHERE f.statut_commande = 'livré'
GROUP BY t.annee, t.trimestre, p.categorie, p.nom_produit, p.marque
WITH NO DATA;

CREATE MATERIALIZED VIEW reporting_mexora.mv_performance_livreurs AS
SELECT
    t.annee,
    t.mois,
    l.id_livreur_nk,
    l.nom_livreur,
    l.zone_couverture,
    COUNT(*) AS nb_livraisons,
    ROUND(AVG(f.delai_livraison_jours), 2) AS delai_moyen_jours,
    COUNT(*) FILTER (WHERE f.delai_livraison_jours > 3) AS nb_livraisons_retard,
    ROUND(
        COUNT(*) FILTER (WHERE f.delai_livraison_jours > 3) * 100.0 / NULLIF(COUNT(*), 0),
        2
    ) AS taux_retard_pct
FROM dwh_mexora.fait_ventes f
JOIN dwh_mexora.dim_temps t ON t.id_date = f.id_date
JOIN dwh_mexora.dim_livreur l ON l.id_livreur = f.id_livreur
WHERE f.statut_commande IN ('livré', 'retourné')
  AND f.delai_livraison_jours IS NOT NULL
GROUP BY t.annee, t.mois, l.id_livreur_nk, l.nom_livreur, l.zone_couverture
WITH NO DATA;

CREATE INDEX IF NOT EXISTS idx_mv_ca_mensuel_region_periode
    ON reporting_mexora.mv_ca_mensuel_region(annee, mois, region_admin);

CREATE INDEX IF NOT EXISTS idx_mv_top_produits_trimestre
    ON reporting_mexora.mv_top_produits_trimestre(annee, trimestre, categorie, rang_categorie);

CREATE INDEX IF NOT EXISTS idx_mv_perf_livreurs_periode
    ON reporting_mexora.mv_performance_livreurs(annee, mois, id_livreur_nk);

CREATE OR REPLACE FUNCTION reporting_mexora.refresh_all_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW reporting_mexora.mv_ca_mensuel_region;
    REFRESH MATERIALIZED VIEW reporting_mexora.mv_top_produits_trimestre;
    REFRESH MATERIALIZED VIEW reporting_mexora.mv_performance_livreurs;
END;
$$ LANGUAGE plpgsql;

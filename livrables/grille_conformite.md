# Grille de conformité - Mexora Analytics

| Étape | Critère | Couverture projet | Fichiers |
|---|---|---|---|
| Étape 1 - Modélisation | Schéma correct et complet | Schéma en étoile avec 1 fait et 5 dimensions | `sql/create_dwh.sql`, `livrables/L1_schema_etoile_annote.png` |
| Étape 1 - Modélisation | Granularité justifiée | Grain documenté : ligne de commande produit | `README.md`, `rapport_transformations.md`, `livrables/L2_justification_choix.md` |
| Étape 1 - Modélisation | Additivité des mesures | Additives, semi-additives et non additives identifiées | `rapport_transformations.md`, `livrables/L2_justification_choix.md` |
| Étape 1 - Modélisation | SCD correctement identifiés et justifiés | SCD1 client, SCD2 produit avec dates et actif | `load/loader.py`, `sql/create_dwh.sql`, `rapport_transformations.md` |
| Étape 2 - ETL Python | Qualité du code | Pipeline modulaire extract/transform/load | `main.py`, `extract/`, `transform/`, `load/` |
| Étape 2 - ETL Python | Exhaustivité transformations | Nettoyage doublons, dates, villes, emails, prix, quantités, statuts | `transform/`, `rapport_transformations.md` |
| Étape 2 - ETL Python | Logging et documentation règles | Logs détaillés et rapport des règles | `utils/logger.py`, `logs/`, `rapport_transformations.md` |
| Étape 2 - ETL Python | Gestion erreurs | Try/except pipeline, coercition robuste, rejets contrôlés | `main.py`, `transform/` |
| Étape 3 - PostgreSQL | Schéma SQL correct | Contraintes PK/FK/check, schémas staging/dwh/reporting | `sql/create_dwh.sql` |
| Étape 3 - PostgreSQL | Indexation appropriée | Index simples, composés, partiels, vues | `sql/create_dwh.sql` |
| Étape 3 - PostgreSQL | 3 vues matérialisées fonctionnelles | CA mensuel, top produits, performance livreurs | `sql/create_dwh.sql` |
| Étape 4 - Dashboard | 5 questions répondues visuellement | Structure Metabase + requêtes par question | `dashboard/README.md`, `dashboard/metabase_dashboard.sql` |
| Étape 4 - Dashboard | Qualité visualisation | Pages, KPIs, filtres, types de graphiques | `dashboard_bi.md`, `dashboard/README.md` |
| Étape 4 - Dashboard | Insights métier identifiés | Insights synthétiques | `livrables/L8_insights_metier.md`, `livrables/L8_insights_metier.pdf` |

Score visé : 105/105.

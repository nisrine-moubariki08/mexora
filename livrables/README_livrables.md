# Livrables finaux Mexora Analytics

## Rapport Word complet

- `livrables/Rapport_Mexora_ETL_PRJ1_complete.docx`

Ce document reprend l'ancien rapport Word et ajoute une annexe de mise à jour avec les éléments manquants et les contrôles de données vérifiés.

## L1 - Schéma entité-relation annoté

- `livrables/L1_schema_etoile_annote.png`
- `livrables/L1_schema_etoile_annote.md`

## L2 - Document de justification des choix

- `livrables/L2_justification_choix.pdf`
- `livrables/L2_justification_choix.md`

## L3 - Code Python ETL complet

- `main.py`
- `extract/`
- `transform/`
- `load/`
- `generate_data.py`
- `utils/`

## L4 - Rapport des transformations

- `rapport_transformations.md`

## L5 - Scripts SQL création DWH

- `sql/create_dwh.sql`

## L6 - Script SQL vérification intégrité

- `sql/check_integrity.sql`

## L7 - Dashboard final

- `dashboard/README.md`
- `dashboard/metabase_dashboard.sql`
- `dashboard_bi.md`

Remarque : le projet fournit une version Metabase prête à construire. Le fichier `.pbix` Power BI doit être généré manuellement dans Power BI Desktop en connectant PostgreSQL aux vues matérialisées du schéma `reporting_mexora`.

## L8 - Document d'insights métier

- `livrables/L8_insights_metier.pdf`
- `livrables/L8_insights_metier.md`

## Vérification rapide

```bash
python generate_data.py
python main.py
python scripts/generate_livrables.py
```

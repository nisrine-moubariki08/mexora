# L1 - Schéma entité-relation annoté

Fichier image attendu :

- `L1_schema_etoile_annote.png`

Le schéma représente le modèle en étoile du Data Warehouse Mexora :

- table de faits centrale : `dwh_mexora.fait_ventes` ;
- dimensions : `dim_temps`, `dim_client`, `dim_produit`, `dim_region`, `dim_livreur` ;
- granularité : une ligne = une ligne de commande produit ;
- mesures additives, semi-additives et non additives ;
- SCD Type 1 sur client ;
- SCD Type 2 sur produit.

Pour régénérer l'image :

```bash
python scripts/generate_livrables.py
```

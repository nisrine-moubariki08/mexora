# Pipeline ETL Mexora

## Installation

```bash
# 1. Cloner le repo
git clone &lt;votre-repo&gt;
cd mexora_etl

# 2. Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou venv\Scripts\activate  # Windows

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Créer la base PostgreSQL
createdb mexora_dwh

# 5. Configurer la connexion (optionnel)
export DATABASE_URL="postgresql://user:password@localhost:5432/mexora_dwh"
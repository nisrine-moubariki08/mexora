import json
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

import pandas as pd
from sqlalchemy import text

from config.settings import DB_URL
from load.loader import get_engine

OLD_REPORT = Path(r"C:\Users\pcc\Downloads\Rapport_Mexora_ETL_PRJ1 (1).docx")
OUTPUT_REPORT = BASE_DIR / "livrables" / "Rapport_Mexora_ETL_PRJ1_complete.docx"

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}
ET.register_namespace("w", W_NS)


def w_tag(name: str) -> str:
    return f"{{{W_NS}}}{name}"


def add_paragraph(body, text_value: str = "", style: str | None = None, bold: bool = False) -> None:
    p = ET.Element(w_tag("p"))
    if style:
        p_pr = ET.SubElement(p, w_tag("pPr"))
        p_style = ET.SubElement(p_pr, w_tag("pStyle"))
        p_style.set(w_tag("val"), style)
    r = ET.SubElement(p, w_tag("r"))
    if bold:
        r_pr = ET.SubElement(r, w_tag("rPr"))
        ET.SubElement(r_pr, w_tag("b"))
    t = ET.SubElement(r, w_tag("t"))
    t.text = text_value
    t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    insert_before_sectpr(body, p)


def add_bullet(body, text_value: str) -> None:
    add_paragraph(body, f"- {text_value}")


def add_page_break(body) -> None:
    p = ET.Element(w_tag("p"))
    r = ET.SubElement(p, w_tag("r"))
    br = ET.SubElement(r, w_tag("br"))
    br.set(w_tag("type"), "page")
    insert_before_sectpr(body, p)


def insert_before_sectpr(body, element) -> None:
    sectpr = body.find("w:sectPr", NS)
    if sectpr is None:
        body.append(element)
    else:
        index = list(body).index(sectpr)
        body.insert(index, element)


def add_table(body, headers: list[str], rows: list[list[str]]) -> None:
    tbl = ET.Element(w_tag("tbl"))
    tbl_pr = ET.SubElement(tbl, w_tag("tblPr"))
    borders = ET.SubElement(tbl_pr, w_tag("tblBorders"))
    for side in ["top", "left", "bottom", "right", "insideH", "insideV"]:
        border = ET.SubElement(borders, w_tag(side))
        border.set(w_tag("val"), "single")
        border.set(w_tag("sz"), "6")
        border.set(w_tag("space"), "0")
        border.set(w_tag("color"), "808080")

    def cell(value: str, is_header: bool = False):
        tc = ET.Element(w_tag("tc"))
        p = ET.SubElement(tc, w_tag("p"))
        r = ET.SubElement(p, w_tag("r"))
        if is_header:
            r_pr = ET.SubElement(r, w_tag("rPr"))
            ET.SubElement(r_pr, w_tag("b"))
        t = ET.SubElement(r, w_tag("t"))
        t.text = str(value)
        return tc

    tr = ET.SubElement(tbl, w_tag("tr"))
    for header in headers:
        tr.append(cell(header, True))
    for row in rows:
        tr = ET.SubElement(tbl, w_tag("tr"))
        for value in row:
            tr.append(cell(value))
    insert_before_sectpr(body, tbl)


def compute_data_quality() -> dict:
    data_dir = BASE_DIR / "data"
    commandes = pd.read_csv(data_dir / "commandes_mexora.csv", dtype=str)
    clients = pd.read_csv(data_dir / "clients_mexora.csv", dtype=str)
    regions = pd.read_csv(data_dir / "regions_maroc.csv", dtype=str)
    produits = json.loads((data_dir / "produits_mexora.json").read_text(encoding="utf-8"))["produits"]

    prix = pd.to_numeric(commandes["prix_unitaire"], errors="coerce")
    quantite = pd.to_numeric(commandes["quantite"], errors="coerce")
    dates = pd.to_datetime(commandes["date_commande"], format="mixed", dayfirst=True, errors="coerce")
    email_regex = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")
    emails_invalides = clients["email"].fillna("").apply(lambda value: not bool(email_regex.match(str(value)))).sum()
    livreur_missing = commandes["id_livreur"].isna() | commandes["id_livreur"].fillna("").str.strip().isin(["", "-"])

    known_city_tokens = {
        "tanger", "tng", "tnja", "tangier", "casablanca", "cas", "casa",
        "rabat", "rba", "fès", "fes", "fez", "marrakech", "mrk",
        "agadir", "agd", "oujda", "oud", "meknès", "mkn", "meknes",
        "tétouan", "tet", "tetouan", "safi", "sfi"
    }
    raw_cities = commandes["ville_livraison"].fillna("").str.lower().str.strip()
    villes_incoherentes = (~raw_cities.isin(known_city_tokens)).sum()

    return {
        "commandes": len(commandes),
        "clients": len(clients),
        "produits": len(produits),
        "regions": len(regions),
        "doublons_commandes": int(commandes.duplicated("id_commande").sum()),
        "emails_dupliques": int(clients["email"].str.lower().str.strip().duplicated().sum()),
        "emails_invalides": int(emails_invalides),
        "dates_invalides": int(dates.isna().sum()),
        "villes_incoherentes": int(villes_incoherentes),
        "prix_zero": int((prix == 0).sum()),
        "prix_null": int(prix.isna().sum()),
        "quantites_negatives": int((quantite < 0).sum()),
        "quantites_zero": int((quantite == 0).sum()),
        "quantites_null": int(quantite.isna().sum()),
        "livreurs_manquants": int(livreur_missing.sum()),
    }


def compute_dwh_quality() -> dict:
    engine = get_engine(DB_URL)
    queries = {
        "fait_ventes": "SELECT COUNT(*) FROM dwh_mexora.fait_ventes",
        "dim_temps": "SELECT COUNT(*) FROM dwh_mexora.dim_temps",
        "dim_client": "SELECT COUNT(*) FROM dwh_mexora.dim_client",
        "dim_produit": "SELECT COUNT(*) FROM dwh_mexora.dim_produit",
        "dim_region": "SELECT COUNT(*) FROM dwh_mexora.dim_region",
        "dim_livreur": "SELECT COUNT(*) FROM dwh_mexora.dim_livreur",
        "mv_ca_mensuel_region": "SELECT COUNT(*) FROM reporting_mexora.mv_ca_mensuel_region",
        "mv_top_produits_trimestre": "SELECT COUNT(*) FROM reporting_mexora.mv_top_produits_trimestre",
        "mv_performance_livreurs": "SELECT COUNT(*) FROM reporting_mexora.mv_performance_livreurs",
        "fk_orphelines_client": """
            SELECT COUNT(*)
            FROM dwh_mexora.fait_ventes f
            LEFT JOIN dwh_mexora.dim_client c ON c.id_client_sk = f.id_client
            WHERE c.id_client_sk IS NULL
        """,
        "produits_versions_actives_dupliquees": """
            SELECT COUNT(*)
            FROM (
                SELECT id_produit_nk
                FROM dwh_mexora.dim_produit
                WHERE est_actif = TRUE
                GROUP BY id_produit_nk
                HAVING COUNT(*) > 1
            ) x
        """,
    }
    with engine.connect() as conn:
        return {name: int(conn.execute(text(query)).scalar()) for name, query in queries.items()}


def append_update_sections(document_xml: bytes, raw_quality: dict, dwh_quality: dict) -> bytes:
    root = ET.fromstring(document_xml)
    body = root.find("w:body", NS)
    if body is None:
        raise RuntimeError("Document Word invalide : body introuvable.")

    add_page_break(body)
    add_paragraph(body, "Annexe de mise à jour — Version Data Warehouse complète", "Heading1")
    add_paragraph(
        body,
        "Cette annexe complète l'ancien rapport avec les éléments exigés par la nouvelle grille : "
        "schéma en étoile professionnel, granularité, additivité des mesures, SCD, vues matérialisées, "
        "indexation PostgreSQL, dashboard BI et vérification réelle des données.",
    )

    add_paragraph(body, "1. Couverture des critères d'évaluation", "Heading2")
    add_table(
        body,
        ["Critère", "Réponse ajoutée dans le projet"],
        [
            ["Schéma correct et complet", "Star schema : fact_ventes + dim_temps, dim_client, dim_produit, dim_region, dim_livreur."],
            ["Granularité justifiée", "Une ligne de fact_ventes représente une ligne de commande produit."],
            ["Additivité des mesures", "Montants et quantités additives ; délai semi-additif ; remise non additive."],
            ["SCD", "SCD Type 1 client, SCD Type 2 produit avec date_debut, date_fin, est_actif."],
            ["ETL Python", "Pipeline modulaire extract/transform/load avec logs, gestion erreurs, batch et upsert."],
            ["PostgreSQL", "Contraintes PK/FK/check, index simples, composés, partiels et vues matérialisées."],
            ["Dashboard", "5 questions métier couvertes par les requêtes Metabase/Power BI."],
        ],
    )

    add_paragraph(body, "2. Modélisation dimensionnelle finale", "Heading2")
    for item in [
        "Table de faits : dwh_mexora.fait_ventes.",
        "Dimensions : dim_temps, dim_client, dim_produit, dim_region, dim_livreur.",
        "Grain : une ligne = une commande ligne produit.",
        "Clés étrangères : id_date, id_client, id_produit, id_region, id_livreur.",
        "Mesures additives : quantite_vendue, montant_ht, montant_ttc.",
        "Mesure semi-additive : delai_livraison_jours.",
        "Mesure non additive : remise_pct.",
    ]:
        add_bullet(body, item)

    add_paragraph(body, "3. SCD retenues", "Heading2")
    add_paragraph(
        body,
        "SCD Type 1 — dim_client : les corrections simples comme l'email, la ville ou le canal d'acquisition "
        "écrasent la valeur existante grâce à un upsert sur id_client_nk. Ce choix donne toujours la meilleure "
        "version connue du client."
    )
    add_paragraph(
        body,
        "SCD Type 2 — dim_produit : les changements de catégorie, sous-catégorie, marque, fournisseur, prix standard "
        "ou origine créent une nouvelle version produit. Les colonnes date_debut, date_fin et est_actif conservent "
        "l'historique analytique."
    )

    add_paragraph(body, "4. Vérification des données sources", "Heading2")
    add_table(
        body,
        ["Contrôle", "Valeur vérifiée"],
        [
            ["Commandes générées", raw_quality["commandes"]],
            ["Clients générés", raw_quality["clients"]],
            ["Produits générés", raw_quality["produits"]],
            ["Régions générées", raw_quality["regions"]],
            ["Doublons id_commande", raw_quality["doublons_commandes"]],
            ["Emails dupliqués", raw_quality["emails_dupliques"]],
            ["Emails invalides", raw_quality["emails_invalides"]],
            ["Dates commande invalides", raw_quality["dates_invalides"]],
            ["Villes livraison incohérentes", raw_quality["villes_incoherentes"]],
            ["Prix à zéro", raw_quality["prix_zero"]],
            ["Prix nuls ou non numériques", raw_quality["prix_null"]],
            ["Quantités négatives", raw_quality["quantites_negatives"]],
            ["Quantités nulles", raw_quality["quantites_zero"]],
            ["Livreurs manquants", raw_quality["livreurs_manquants"]],
        ],
    )

    add_paragraph(body, "5. Vérification du Data Warehouse chargé", "Heading2")
    add_table(
        body,
        ["Objet PostgreSQL", "Nombre de lignes / anomalies"],
        [
            ["dwh_mexora.fait_ventes", dwh_quality["fait_ventes"]],
            ["dwh_mexora.dim_temps", dwh_quality["dim_temps"]],
            ["dwh_mexora.dim_client", dwh_quality["dim_client"]],
            ["dwh_mexora.dim_produit", dwh_quality["dim_produit"]],
            ["dwh_mexora.dim_region", dwh_quality["dim_region"]],
            ["dwh_mexora.dim_livreur", dwh_quality["dim_livreur"]],
            ["reporting_mexora.mv_ca_mensuel_region", dwh_quality["mv_ca_mensuel_region"]],
            ["reporting_mexora.mv_top_produits_trimestre", dwh_quality["mv_top_produits_trimestre"]],
            ["reporting_mexora.mv_performance_livreurs", dwh_quality["mv_performance_livreurs"]],
            ["FK client orphelines", dwh_quality["fk_orphelines_client"]],
            ["Produits avec plusieurs versions actives", dwh_quality["produits_versions_actives_dupliquees"]],
        ],
    )

    add_paragraph(body, "6. Vues matérialisées et dashboard BI", "Heading2")
    for item in [
        "mv_ca_mensuel_region : CA mensuel par région, commandes, clients actifs, panier moyen.",
        "mv_top_produits_trimestre : top produits par trimestre et catégorie.",
        "mv_performance_livreurs : délai moyen, retards et taux de retard par livreur.",
        "Dashboard : vue exécutive, régions, produits, clients, livraison.",
        "Les 5 questions métier sont couvertes dans dashboard/metabase_dashboard.sql.",
    ]:
        add_bullet(body, item)

    add_paragraph(body, "7. Fichiers livrables ajoutés au dépôt", "Heading2")
    for item in [
        "livrables/grille_conformite.md",
        "livrables/L1_schema_etoile_annote.png",
        "livrables/L2_justification_choix.pdf",
        "livrables/L8_insights_metier.pdf",
        "dashboard/metabase_dashboard.sql",
        "sql/create_dwh.sql",
        "sql/check_integrity.sql",
    ]:
        add_bullet(body, item)

    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def build_augmented_docx() -> None:
    if not OLD_REPORT.exists():
        raise FileNotFoundError(f"Ancien rapport introuvable : {OLD_REPORT}")

    raw_quality = compute_data_quality()
    dwh_quality = compute_dwh_quality()
    OUTPUT_REPORT.parent.mkdir(exist_ok=True)

    with zipfile.ZipFile(OLD_REPORT, "r") as zin:
        original_files = {name: zin.read(name) for name in zin.namelist()}

    original_files["word/document.xml"] = append_update_sections(
        original_files["word/document.xml"], raw_quality, dwh_quality
    )

    with zipfile.ZipFile(OUTPUT_REPORT, "w", zipfile.ZIP_DEFLATED) as zout:
        for name, content in original_files.items():
            zout.writestr(name, content)

    print(f"Rapport Word complété : {OUTPUT_REPORT}")


if __name__ == "__main__":
    build_augmented_docx()

from pathlib import Path
import textwrap

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

BASE_DIR = Path(__file__).resolve().parents[1]
LIVRABLES_DIR = BASE_DIR / "livrables"


def add_box(ax, xy, width, height, title, lines, color):
    x, y = xy
    box = FancyBboxPatch(
        (x, y), width, height,
        boxstyle="round,pad=0.018,rounding_size=0.015",
        linewidth=1.4, edgecolor="#233142", facecolor=color
    )
    ax.add_patch(box)
    ax.text(x + width / 2, y + height - 0.055, title, ha="center", va="top",
            fontsize=11, fontweight="bold", color="#17202a")
    wrapped = []
    for line in lines:
        wrapped.extend(textwrap.wrap(line, width=24) or [""])
    ax.text(x + 0.025, y + height - 0.13, "\n".join(wrapped), ha="left", va="top",
            fontsize=8.2, color="#17202a", linespacing=1.3)


def add_arrow(ax, start, end):
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=15,
                                 linewidth=1.2, color="#34495e"))


def generate_schema_png():
    fig, ax = plt.subplots(figsize=(15, 9))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_title("Mexora Analytics - Schéma en étoile annoté", fontsize=18, fontweight="bold", pad=20)

    fact = (
        "fact_ventes",
        [
            "Grain : 1 ligne = 1 ligne de commande produit",
            "FK : id_date, id_client, id_produit, id_region, id_livreur",
            "Mesures additives : quantite_vendue, montant_ht, montant_ttc",
            "Mesure semi-additive : delai_livraison_jours",
            "Mesure non additive : remise_pct"
        ],
        "#f9e79f",
        (0.38, 0.36), 0.27, 0.30
    )
    dims = [
        ("dim_temps", ["PK id_date", "Jour, mois, trimestre, année", "Week-end, férié Maroc, Ramadan"], "#d6eaf8", (0.39, 0.74), 0.25, 0.17),
        ("dim_client", ["PK id_client_sk", "NK id_client_nk", "Email, tranche_age, segment", "SCD Type 1 : corrections écrasées"], "#d5f5e3", (0.05, 0.44), 0.25, 0.22),
        ("dim_produit", ["PK id_produit_sk", "NK id_produit_nk", "Catégorie, marque, prix", "SCD Type 2 : date_debut, date_fin, est_actif"], "#fadbd8", (0.70, 0.44), 0.25, 0.23),
        ("dim_region", ["PK id_region", "Ville, province, région admin", "Zone géographique, pays"], "#e8daef", (0.18, 0.10), 0.25, 0.18),
        ("dim_livreur", ["PK id_livreur", "NK id_livreur_nk", "Transport, zone couverture", "Livreur inconnu = -1"], "#fdebd0", (0.61, 0.10), 0.25, 0.18),
    ]

    add_box(ax, fact[3], fact[4], fact[5], fact[0], fact[1], fact[2])
    for title, lines, color, xy, w, h in dims:
        add_box(ax, xy, w, h, title, lines, color)

    add_arrow(ax, (0.515, 0.74), (0.515, 0.66))
    add_arrow(ax, (0.30, 0.55), (0.38, 0.51))
    add_arrow(ax, (0.70, 0.55), (0.65, 0.51))
    add_arrow(ax, (0.32, 0.25), (0.42, 0.36))
    add_arrow(ax, (0.63, 0.28), (0.58, 0.36))

    ax.text(0.02, 0.02,
            "PostgreSQL : staging_mexora -> dwh_mexora -> reporting_mexora | Vues matérialisées : CA mensuel, top produits, performance livreurs",
            fontsize=9, color="#566573")
    output = LIVRABLES_DIR / "L1_schema_etoile_annote.png"
    fig.savefig(output, dpi=180, bbox_inches="tight")
    plt.close(fig)


def write_pdf(path, title, sections, page_note=None):
    with PdfPages(path) as pdf:
        fig = plt.figure(figsize=(8.27, 11.69))
        fig.patch.set_facecolor("white")
        fig.text(0.08, 0.94, title, fontsize=18, fontweight="bold", color="#17202a")
        y = 0.89
        for heading, body in sections:
            fig.text(0.08, y, heading, fontsize=12, fontweight="bold", color="#1f618d")
            y -= 0.025
            lines = []
            for paragraph in body:
                lines.extend(textwrap.wrap(paragraph, width=95))
                lines.append("")
            fig.text(0.08, y, "\n".join(lines).strip(), fontsize=9.2, color="#17202a", va="top", linespacing=1.28)
            y -= 0.035 + 0.018 * len(lines)
        if page_note:
            fig.text(0.08, 0.04, page_note, fontsize=8, color="#566573")
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)


def generate_pdfs():
    write_pdf(
        LIVRABLES_DIR / "L2_justification_choix.pdf",
        "Mexora Analytics - Justification des choix",
        [
            ("Modélisation", [
                "Le modèle retenu est un schéma en étoile centré sur fact_ventes. Ce choix simplifie les requêtes analytiques et rend les agrégations lisibles pour un dashboard BI.",
                "Le grain est une ligne de commande produit. Cette granularité permet d'analyser les ventes par date, produit, client, région et livreur sans perdre le détail transactionnel utile."
            ]),
            ("Additivité des mesures", [
                "quantite_vendue, montant_ht et montant_ttc sont additives sur toutes les dimensions. delai_livraison_jours est semi-additif : il doit être agrégé par moyenne ou percentile. remise_pct est non additive : elle doit être recalculée ou moyennée avec prudence."
            ]),
            ("SCD", [
                "dim_client utilise une SCD Type 1 pour les corrections simples comme email, ville ou canal d'acquisition : on conserve la meilleure valeur connue.",
                "dim_produit utilise une SCD Type 2 pour historiser les changements de catégorie, marque, fournisseur, prix standard ou origine. Les colonnes date_debut, date_fin et est_actif permettent de savoir quelle version était valide."
            ]),
            ("PostgreSQL et performance", [
                "Les clés étrangères sont indexées pour accélérer les jointures étoile. Les index composés répondent aux requêtes fréquentes période/région et période/produit. L'index partiel sur les ventes livrées réduit le coût des dashboards qui filtrent le chiffre d'affaires réel."
            ])
        ],
        "Livrable L2 - version courte conçue pour tenir en 2 pages maximum."
    )
    write_pdf(
        LIVRABLES_DIR / "L8_insights_metier.pdf",
        "Mexora Analytics - Insights métier",
        [
            ("1. Croissance régionale", [
                "Le CA mensuel par région permet d'identifier les zones qui portent la croissance et celles qui nécessitent une action commerciale ciblée."
            ]),
            ("2. Performance produit", [
                "Le classement trimestriel révèle les catégories et produits dominants. Il sert à prioriser stock, campagnes marketing et négociation fournisseur."
            ]),
            ("3. Segmentation client", [
                "Les segments Gold, Silver et Bronze mettent en évidence la contribution client au CA. Les campagnes de fidélisation doivent viser en priorité les clients Gold et les Silver proches du seuil Gold."
            ]),
            ("4. Livraison", [
                "Le taux de retard par livreur permet d'identifier les zones ou prestataires à améliorer. Un délai moyen élevé peut expliquer retours, annulations ou baisse de satisfaction."
            ]),
            ("5. Qualité des données", [
                "Les anomalies simulées montrent l'importance du nettoyage avant chargement : doublons, dates invalides, prix nuls, quantités négatives et villes incohérentes sont contrôlés par l'ETL."
            ])
        ],
        "Livrable L8 - document synthétique 1 page."
    )


def main():
    LIVRABLES_DIR.mkdir(exist_ok=True)
    generate_schema_png()
    generate_pdfs()
    print(f"Livrables générés dans {LIVRABLES_DIR}")


if __name__ == "__main__":
    main()

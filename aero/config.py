"""Constantes partagées : identité, listes de référence, échelles de cotation."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DB_PATH = Path(os.environ.get("AERO_DB", DATA_DIR / "aero_risques.db"))

APP_NAME = "AERO PRECISION INDUSTRIES"
HEADER_TITLE = "Usinage des Pièces Aéronautiques · Management des Risques"
HEADER_SUBTITLE = "SURVEILLANCE · ISO 31000 · ISO 31010 · EN 9100"
WELCOME = "Bienvenue dans le site de notre entreprise AERO PRECISION INDUSTRIES"

# Fond de la page d'accueil. Un fichier static/fond_accueil.jpg (ou .jpeg, .png, .webp)
# est prioritaire sur le lien distant et permet une démonstration hors ligne.
FOND_ACCUEIL_URL = (
    "https://media.licdn.com/dms/image/v2/D4E12AQHWH6sDhG66sg/article-cover_image-shrink_720_1280/"
    "article-cover_image-shrink_720_1280/0/1695818666276?e=2147483647&v=beta&t=JvBTlXcaVDyK3A19oP292OEb5er-7c8HttEYJhjzILU"
)
# 0 = invisible, 1 = image pleine.
OPACITE_FOND_ACCUEIL = 0.25

DEMO_USERNAME = "youssouf_aero"
DEMO_PASSWORD = "aero_20262027"

NIVEAUX = ["Faible", "Modéré", "Élevé", "Critique"]
COULEURS_NIVEAU = {
    "Faible": "#22C55E",
    "Modéré": "#EAB308",
    "Élevé": "#F97316",
    "Critique": "#DC2626",
}
TEINTES_NIVEAU = {
    "Faible": "#DCFCE7",
    "Modéré": "#FEF9C3",
    "Élevé": "#FFEDD5",
    "Critique": "#FEE2E2",
}

INK = "#0B1F3A"
STEEL = "#5B6B82"
LINE = "#E2E7F3"
ACCENT = "#F59E0B"

STATUT_A_FAIRE, STATUT_EN_COURS, STATUT_TERMINE = "À faire", "En cours", "Terminé"
STATUTS = [STATUT_A_FAIRE, STATUT_EN_COURS, STATUT_TERMINE]

CATEGORIES = ["Technique", "Qualité", "Humain", "Matière", "Machine", "Logistique", "Sécurité produit"]
PROCESSUS = ["Méthodes", "Production", "Qualité", "Maintenance", "Achats", "Logistique"]
RESPONSABLES = [
    "Production",
    "Qualité",
    "Achats",
    "Méthodes",
    "Maintenance",
    "Logistique",
    "Responsable Méthodes",
    "Technicien Méthodes",
    "Chef d'atelier",
    "Responsable Production",
    "Responsable Qualité",
    "Responsable Achats",
    "Responsable Maintenance",
]

ECHELLES = {
    "G": {
        "nom": "Gravité",
        1: "Effet imperceptible, aucune conséquence sur la pièce",
        5: "Non-conformité avec retouche ou dérogation client",
        10: "Atteinte possible à la sécurité du vol",
    },
    "O": {
        "nom": "Occurrence",
        1: "Quasi impossible, jamais observé",
        5: "Occasionnel, quelques cas par an",
        10: "Quasi systématique, à chaque lot",
    },
    "D": {
        "nom": "Détection",
        1: "Détection certaine avant l'étape suivante",
        5: "Détection possible, contrôle partiel ou tardif",
        10: "Aucun moyen de détection avant livraison",
    },
}

SCENARIO_CAS = "cas"
SCENARIO_ETENDU = "etendu"
SCENARIOS = {
    SCENARIO_CAS: "Étude de cas, support de fixation (5 risques)",
    SCENARIO_ETENDU: "Portefeuille atelier complet (12 risques)",
}

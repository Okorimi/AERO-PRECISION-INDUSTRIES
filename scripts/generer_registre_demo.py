"""Génère un registre SIMULÉ, aux colonnes identiques à celles du sujet YaneCode.

Il sert uniquement à faire fonctionner l'application tant que le vrai fichier
guihini_abakar_youssouf.csv n'a pas été placé dans le dossier data/.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

SORTIE = Path(__file__).resolve().parent.parent / "data" / "registre_demo_simule.csv"
rng = np.random.default_rng(2026)

# processus, clause, catégorie, poids, gravités possibles, probabilités possibles, seuil
PROCESSUS = [
    ("Achats et fournisseurs", "8.4", "Fournisseurs", 19, (2, 3, 4), (3, 4, 5), 10),
    ("Production et usinage", "8.5.1", "Production", 15, (3, 4), (3, 4, 5), 10),
    ("Procédés spéciaux", "8.5.1.2", "Production", 7, (3, 4), (2, 3, 4), 10),
    ("Prévention des pièces contrefaites", "8.1.4", "Pièces contrefaites", 3, (4, 5), (1, 2), 6),
    ("Sécurité produit", "8.1.3", "Sécurité produit", 3, (5,), (1, 2), 6),
    ("Métrologie", "7.1.5", "Métrologie", 7, (2, 3, 4), (2, 3), 10),
    ("Conception et développement", "8.3", "Conception", 6, (3, 4), (1, 2, 3), 10),
    ("Gestion de configuration", "8.1.2", "Configuration", 6, (2, 3, 4), (2, 3), 10),
    ("Compétences", "7.2", "Ressources humaines", 7, (2, 3), (2, 3, 4), 12),
    ("Infrastructures et maintenance", "7.1.3", "Maintenance", 8, (2, 3, 4), (2, 3, 4), 10),
    ("Identification et traçabilité", "8.5.2", "Traçabilité", 6, (3, 4), (2, 3), 10),
    ("Risques opérationnels", "8.1.1", "Planification", 5, (2, 3, 4), (2, 3), 12),
    ("Maîtrise des non-conformités", "8.7", "Qualité", 5, (2, 3, 4), (2, 3), 10),
    ("Audit interne", "9.2", "Qualité", 3, (1, 2, 3), (2, 3), 12),
]
SITES = ["Casablanca", "Nouaceur", "Tanger", "Safi"]
PROGRAMMES = ["Mono-couloir", "Long-courrier", "Turbopropulseur", "Aviation d'affaires", "Défense"]
TECHNIQUES = ["AMDEC", "FTA", "Bow-tie", "HAZOP", "Ishikawa", "Monte-Carlo", "Delphi", "Matrice de criticité"]
SOURCES = ["Audit interne", "Audit client", "Retour d'expérience", "Revue de processus", "Non-conformité", "Veille fournisseurs"]
PROPRIETAIRES = ["Directeur Qualité", "Responsable Achats", "Responsable Production", "Responsable Méthodes", "Responsable Maintenance", "Responsable Sécurité produit"]


def niveau(c: float) -> str:
    return "Faible" if c <= 4 else "Modéré" if c <= 9 else "Élevé" if c <= 14 else "Critique"


def generer(n: int = 640) -> pd.DataFrame:
    poids = np.array([p[3] for p in PROCESSUS], dtype=float)
    poids /= poids.sum()
    debut = pd.Timestamp("2023-01-01")
    fin = pd.Timestamp("2026-10-15")
    jours = (fin - debut).days
    lignes = []
    for i in range(1, n + 1):
        nom, clause, categorie, _, gravites, probas, seuil = PROCESSUS[rng.choice(len(PROCESSUS), p=poids)]
        g, p, d = int(rng.choice(gravites)), int(rng.choice(probas)), int(rng.integers(1, 6))
        c = g * p
        date_id = debut + pd.Timedelta(days=int(rng.integers(0, jours)))

        if c <= 4 and rng.random() < 0.7:
            option = "Accepter"
        else:
            option = str(rng.choice(["Réduire", "Transférer", "Éviter"], p=[0.84, 0.08, 0.08]))

        if option == "Accepter":
            statut, efficacite, cout = "Sans objet", 0, 0.0
            action = "Surveillance périodique, sans action dédiée"
        else:
            statut = str(rng.choice(["Terminée", "En cours", "En retard", "Planifiée"], p=[0.68, 0.16, 0.09, 0.07]))
            bornes = {"Réduire": (45, 75), "Transférer": (35, 60), "Éviter": (70, 90)}[option]
            efficacite = int(rng.integers(*bornes)) if statut == "Terminée" else int(rng.integers(20, 45))
            cout = float(round(rng.gamma(2.2, 4200) * (0.6 + g * 0.45), -2))
            action = f"Plan de maîtrise {nom.lower()}"

        residuelle = max(1, round(c * (1 - efficacite / 100)))
        materialise = rng.random() < 0.05 + residuelle / 25 * 0.4
        impact = float(round(rng.gamma(1.8, 30000) * (g**1.6) / 4, -2)) if materialise else 0.0

        echeance = realisation = pd.NaT
        if statut == "Terminée":
            echeance = date_id + pd.Timedelta(days=int(rng.integers(30, 180)))
            realisation = echeance + pd.Timedelta(days=int(rng.integers(-20, 35)))

        lignes.append(
            {
                "id_risque": f"RSK-{i:04d}",
                "date_identification": date_id.date().isoformat(),
                "site": str(rng.choice(SITES)),
                "programme": str(rng.choice(PROGRAMMES)),
                "processus": nom,
                "clause_EN9100": clause,
                "categorie_risque": categorie,
                "risque": f"Défaillance {categorie.lower()} sur le processus {nom.lower()}",
                "cause": "Cause simulée",
                "consequence": "Conséquence simulée",
                "source_identification": str(rng.choice(SOURCES)),
                "technique_ISO31010": str(rng.choice(TECHNIQUES)),
                "gravite": g,
                "probabilite": p,
                "detectabilite": d,
                "criticite_inherente": c,
                "RPN": g * p * d,
                "niveau_risque_inherent": niveau(c),
                "seuil_appetence": seuil,
                "option_traitement_ISO31000": option,
                "action_maitrise": action,
                "proprietaire_risque": str(rng.choice(PROPRIETAIRES)),
                "cout_action_mad": cout,
                "statut_action": statut,
                "date_echeance": echeance.date().isoformat() if pd.notna(echeance) else "",
                "date_realisation": realisation.date().isoformat() if pd.notna(realisation) else "",
                "efficacite_action_pct": efficacite,
                "criticite_residuelle": residuelle,
                "niveau_risque_residuel": niveau(residuelle),
                "reduction_criticite_pct": round((c - residuelle) / c * 100, 1),
                "risque_acceptable": "Oui" if residuelle <= seuil else "Non",
                "risque_materialise": "Oui" if materialise else "Non",
                "impact_financier_reel_mad": impact,
            }
        )
    df = pd.DataFrame(lignes)
    # Quelques défauts réalistes pour que l'étape de nettoyage ait un effet visible.
    doublons = df.sample(6, random_state=7)
    df.loc[df.sample(12, random_state=3).index, "site"] = "  Casablanca "
    return pd.concat([df, doublons], ignore_index=True)


if __name__ == "__main__":
    SORTIE.parent.mkdir(exist_ok=True)
    table = generer()
    table.to_csv(SORTIE, index=False, encoding="utf-8")
    print(f"{len(table)} lignes écrites dans {SORTIE}")
    print("Criticité moyenne :", round(table.criticite_inherente.mean(), 2), "->", round(table.criticite_residuelle.mean(), 2))

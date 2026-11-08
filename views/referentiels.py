from __future__ import annotations

import pandas as pd
import streamlit as st

from aero import ui


def _table(lignes: list[tuple[str, str, str]], colonnes: list[str]) -> None:
    st.table(pd.DataFrame(lignes, columns=colonnes).set_index(colonnes[0]))


def render() -> None:
    ui.en_tete("Référentiels", "Ces normes servent ici de cadre méthodologique. L'application ne constitue ni une certification ni une preuve de conformité.")

    with ui.carte("iso31000", "ISO 31000 : processus de management du risque"):
        _table(
            [
                ("Domaine d'application, contexte et critères", "Fixer le périmètre et les seuils de criticité", "Tableau de bord, contexte projet"),
                ("Identification", "Recenser les risques, leurs causes et leurs effets", "Identification"),
                ("Analyse", "Coter gravité, occurrence et détection", "Évaluation"),
                ("Évaluation", "Comparer le niveau obtenu aux critères", "Matrice de criticité"),
                ("Traitement", "Décider et suivre les actions", "Actions"),
                ("Surveillance et revue", "Réévaluer et mesurer le gain", "Suivi avant / après"),
                ("Enregistrement et rapport", "Conserver et diffuser les résultats", "Export CSV, Registre 2023-2026"),
            ],
            ["Étape", "Objectif", "Mise en œuvre dans l'application"],
        )
    st.write("")
    with ui.carte("iso31010", "ISO 31010 : techniques d'appréciation du risque"):
        _table(
            [
                ("AMDEC", "NPR = G × O × D, sur une échelle de 1 à 10", "Évaluation, Suivi avant / après"),
                ("Matrice de criticité", "Gravité × occurrence, grille 5 × 5", "Matrice de criticité"),
                ("Autres techniques (FTA, Bow-tie, HAZOP…)", "Analyse de leur usage et de leur efficacité dans l'historique", "Registre 2023-2026"),
            ],
            ["Technique", "Application", "Page"],
        )
    st.write("")
    with ui.carte("en9100", "EN 9100 : exigences du secteur aéronautique"):
        _table(
            [
                ("§6.1", "Actions face aux risques et opportunités", "Identification, Évaluation, Actions"),
                ("§8.1.1", "Gestion des risques opérationnels", "Base AMDEC, Matrice, Suivi avant / après"),
                ("§8.1.3, §8.1.4, §8.4, §7.1.5", "Sécurité produit, pièces contrefaites, prestataires externes, métrologie", "Registre 2023-2026, vue Cartographie"),
            ],
            ["Clause", "Sujet", "Fonctionnalités liées"],
        )
    st.write("")
    with ui.carte("seuils", "Règles de calcul appliquées"):
        _table(
            [
                ("Faible", "NPR < 50", "Surveillance"),
                ("Modéré", "50 ≤ NPR ≤ 99", "Action à planifier"),
                ("Élevé", "100 ≤ NPR ≤ 199", "Action requise"),
                ("Critique", "NPR ≥ 200", "Traitement prioritaire"),
                ("Maîtrisé", "Actions terminées et NPR′ < 100", "Risque compté comme maîtrisé"),
            ],
            ["Niveau", "Condition", "Conduite à tenir"],
        )

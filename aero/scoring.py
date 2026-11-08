"""Règles de calcul AMDEC. Aucune dépendance à Streamlit : tout est testable."""
from __future__ import annotations

import math
from typing import Iterable

from .config import STATUT_TERMINE


def calc_npr(g: int, o: int, d: int) -> int:
    """NPR = Gravité × Occurrence × Détection, chaque note étant comprise entre 1 et 10."""
    for note in (g, o, d):
        if not 1 <= int(note) <= 10:
            raise ValueError(f"Note hors échelle 1-10 : {note}")
    return int(g) * int(o) * int(d)


def niveau_npr(npr: int) -> str:
    if npr < 50:
        return "Faible"
    if npr < 100:
        return "Modéré"
    if npr < 200:
        return "Élevé"
    return "Critique"


def niveau5(valeur: int) -> int:
    """Ramène une note 1-10 sur l'échelle 1-5 de la matrice."""
    return math.ceil(int(valeur) / 2)


def zone_matrice(g5: int, o5: int) -> str:
    """Couleur d'une case de la matrice, selon le produit G × O sur 25."""
    produit = g5 * o5
    if produit <= 4:
        return "Faible"
    if produit <= 9:
        return "Modéré"
    if produit <= 14:
        return "Élevé"
    return "Critique"


def delta_npr(avant: int, apres: int) -> int:
    """Gain de sécurité : positif quand le risque baisse."""
    return avant - apres


def reduction_pct(avant: int, apres: int) -> float:
    return (avant - apres) / avant * 100 if avant else 0.0


def est_maitrise(statuts: Iterable[str], npr_residuel: int | None) -> bool:
    """Maîtrisé : au moins une action, toutes terminées, et NPR' réévalué sous 100."""
    statuts = list(statuts)
    return bool(statuts) and all(s == STATUT_TERMINE for s in statuts) and npr_residuel is not None and npr_residuel < 100

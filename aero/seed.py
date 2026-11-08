"""Jeux de données de démonstration. Les dates sont relatives au jour du chargement."""
from __future__ import annotations

from datetime import date, timedelta


def _risk(titre, processus, categorie, cause, effet, age, g, o, d, action, responsable, statut, echeance, res=None):
    jour = date.today()
    return {
        "titre": titre,
        "processus": processus,
        "categorie": categorie,
        "cause": cause,
        "effet": effet,
        "date_identification": jour - timedelta(days=age),
        "gravite": g,
        "occurrence": o,
        "detection": d,
        "residuel": res,
        "actions": [
            {
                "description": action,
                "responsable": responsable,
                "statut": statut,
                "echeance": jour + timedelta(days=echeance),
            }
        ],
    }


def cas_etude() -> list[dict]:
    """Les 5 risques de l'audit du support de fixation. Le NPR′ cible passe chacun sous 100."""
    return [
        _risk(
            "Mauvais réglage CNC", "Production", "Machine",
            "Réglage de la machine CNC non documenté avant lancement de la production.",
            "Série lancée sur un réglage non validé, pièces hors tolérance.",
            14, 8, 5, 5, "Valider les réglages avant production", "Production", "À faire", 21, (8, 2, 3),
        ),
        _risk(
            "Défaut dimensionnel", "Qualité", "Qualité",
            "Contrôles dimensionnels principalement réalisés en fin de processus (écart mesuré +0,13 mm).",
            "Lot potentiellement non conforme, rebut ou dérogation.",
            14, 8, 4, 5, "Isoler les pièces non conformes et inspecter le lot", "Qualité", "En cours", 7, (8, 2, 3),
        ),
        _risk(
            "Détection tardive", "Qualité", "Qualité",
            "Absence de contrôles volants ou intermédiaires durant le cycle d'usinage.",
            "Dérive découverte après usinage de toute la série.",
            13, 7, 6, 7, "Ajouter des contrôles en cours de fabrication", "Qualité", "À faire", 30, (7, 3, 3),
        ),
        _risk(
            "Perte de traçabilité", "Production", "Qualité",
            "Dossiers de production incomplets.",
            "Impossible de reconstituer l'historique d'une pièce en cas d'alerte.",
            12, 7, 4, 8, "Compléter les dossiers de production", "Production", "À faire", 28, (7, 2, 4),
        ),
        _risk(
            "Conformité matière non démontrée", "Achats", "Matière",
            "Certificat matière absent du dossier consulté lors de l'audit.",
            "Conformité de l'aluminium utilisé impossible à prouver au client.",
            12, 9, 3, 7, "Vérifier les certificats avant utilisation", "Achats / Qualité", "En cours", 10, (9, 2, 3),
        ),
    ]


def portefeuille_etendu() -> list[dict]:
    """Les 12 risques atelier, avec actions, une échéance dépassée et réévaluations."""
    lignes = [
        ("Erreur de programme CNC (mauvaise version)", "Méthodes", "Technique", "Plusieurs versions de programme disponibles au poste.", "Usinage selon une définition périmée.", 60, 9, 5, 6, "Gestion de versions et validation des programmes", "Responsable Méthodes", "Terminé", -20, (9, 2, 3)),
        ("Usure d'outil non détectée", "Production", "Machine", "Durée de vie des outils non suivie.", "Dérive de cote et état de surface dégradé.", 55, 7, 6, 7, "Suivi de la durée de vie des outils", "Chef d'atelier", "En cours", 12, (7, 3, 4)),
        ("Dérive dimensionnelle de la pièce", "Qualité", "Qualité", "Contrôle réalisé uniquement en fin de série.", "Lot complet hors tolérance.", 50, 9, 4, 6, "Contrôle MMT en cours de série", "Responsable Qualité", "Terminé", -10, (9, 2, 3)),
        ("Défaut de bridage de la pièce", "Méthodes", "Technique", "Montage variable selon l'opérateur.", "Déformation et vibrations pendant l'usinage.", 47, 8, 4, 5, "Gamme de montage standardisée", "Technicien Méthodes", "À faire", 25, (8, 2, 3)),
        ("Matière non conforme (certificat manquant)", "Achats", "Matière", "Réception sans vérification du certificat.", "Matière non démontrée engagée en production.", 44, 10, 3, 5, "Contrôle réception renforcé", "Responsable Achats", "Terminé", -15, (10, 1, 3)),
        ("Panne machine imprévue", "Maintenance", "Machine", "Maintenance uniquement curative.", "Arrêt de production et retard.", 40, 6, 5, 4, "Plan de maintenance préventive", "Responsable Maintenance", "En cours", -6, (6, 2, 3)),
        ("Mauvais état de surface", "Méthodes", "Technique", "Paramètres de coupe inadaptés à l'alliage.", "Rugosité hors spécification, retouche.", 36, 6, 5, 5, "Optimisation des paramètres de coupe", "Technicien Méthodes", "À faire", 35, (6, 2, 3)),
        ("Traçabilité incomplète du lot", "Qualité", "Qualité", "Enregistrements papier non consolidés.", "Rappel de lot impossible à circonscrire.", 32, 8, 4, 6, "Mise en place d'une traçabilité numérique", "Responsable Qualité", "En cours", 40, (8, 2, 3)),
        ("Collision machine (programme non simulé)", "Méthodes", "Technique", "Programme lancé sans simulation.", "Casse de broche et pièce détruite.", 28, 9, 3, 7, "Simulation obligatoire avant lancement", "Responsable Méthodes", "Terminé", -5, (9, 1, 3)),
        ("Retard de livraison", "Logistique", "Logistique", "Charge atelier mal anticipée.", "Pénalités et insatisfaction client.", 24, 5, 6, 3, "Planification et suivi des délais", "Responsable Production", "Terminé", -3, (5, 3, 3)),
        ("Non-respect de la gamme de fabrication", "Production", "Humain", "Opérations réalisées de mémoire.", "Étape omise ou réalisée hors séquence.", 20, 7, 4, 6, "Audit de poste régulier", "Responsable Qualité", "En cours", 18, (7, 2, 4)),
        ("Contamination ou corps étrangers (FOD)", "Production", "Sécurité produit", "Rangement du poste insuffisant.", "Corps étranger présent dans une pièce livrée.", 16, 8, 2, 6, "Procédure 5S / FOD", "Chef d'atelier", "Terminé", -8, (8, 1, 4)),
    ]
    return [_risk(*ligne) for ligne in lignes]

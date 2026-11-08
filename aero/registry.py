"""Registre historique des risques : chargement, nettoyage, indicateurs et conclusions."""
from __future__ import annotations

import io
import unicodedata
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import pandas as pd

from .config import DATA_DIR

FICHIER_OFFICIEL = DATA_DIR / "guihini_abakar_youssouf.csv"
FICHIER_SIMULE = DATA_DIR / "registre_demo_simule.csv"

COLONNES = [
    "id_risque", "date_identification", "site", "programme", "processus", "clause_EN9100",
    "categorie_risque", "risque", "cause", "consequence", "source_identification",
    "technique_ISO31010", "gravite", "probabilite", "detectabilite", "criticite_inherente",
    "RPN", "niveau_risque_inherent", "seuil_appetence", "option_traitement_ISO31000",
    "action_maitrise", "proprietaire_risque", "cout_action_mad", "statut_action",
    "efficacite_action_pct", "criticite_residuelle", "niveau_risque_residuel",
    "reduction_criticite_pct", "risque_acceptable", "risque_materialise",
    "impact_financier_reel_mad",
]
OPTIONNELLES = ["date_echeance", "date_realisation"]
NUMERIQUES = [
    "gravite", "probabilite", "detectabilite", "criticite_inherente", "RPN", "seuil_appetence",
    "cout_action_mad", "efficacite_action_pct", "criticite_residuelle",
    "reduction_criticite_pct", "impact_financier_reel_mad",
]
DIMENSIONS = [
    "site", "programme", "processus", "clause_EN9100", "categorie_risque", "source_identification",
    "technique_ISO31010", "option_traitement_ISO31000", "proprietaire_risque", "statut_action",
    "niveau_risque_inherent", "niveau_risque_residuel",
]


class RegistreInvalide(ValueError):
    """Le fichier ne peut pas être exploité. Le message indique quoi corriger."""


@dataclass
class Rapport:
    lignes_lues: int = 0
    doublons_exacts: int = 0
    doublons_id: int = 0
    lignes_invalides: int = 0
    residuels_completes: int = 0
    ecarts_rpn: int = 0
    ecarts_criticite: int = 0
    valeurs_manquantes: dict[str, int] = field(default_factory=dict)
    lignes_finales: int = 0


def _sans_accent(texte: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", texte) if not unicodedata.combining(c))


def _cle(nom: str) -> str:
    return _sans_accent(str(nom)).strip().lower().replace(" ", "_").replace("-", "_")


def lire_csv(contenu: bytes) -> pd.DataFrame:
    for encodage in ("utf-8-sig", "cp1252"):
        try:
            texte = contenu.decode(encodage)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise RegistreInvalide("Encodage non reconnu. Enregistrez le fichier en CSV UTF-8.")
    try:
        brut = pd.read_csv(io.StringIO(texte), sep=None, engine="python", dtype=str)
    except Exception as exc:
        raise RegistreInvalide(f"Le fichier n'a pas pu être lu comme un CSV : {exc}") from exc
    correspondance = {_cle(c): c for c in COLONNES + OPTIONNELLES}
    return brut.rename(columns=lambda c: correspondance.get(_cle(c), str(c).strip()))


def _dates(serie: pd.Series) -> pd.Series:
    resultat = pd.to_datetime(serie, errors="coerce", format="ISO8601")
    restants = resultat.isna() & serie.notna()
    if restants.any():
        resultat = resultat.mask(
            restants, pd.to_datetime(serie[restants], errors="coerce", dayfirst=True, format="mixed")
        )
    return resultat


def _nombres(serie: pd.Series) -> pd.Series:
    texte = serie.astype("string").str.replace(r"[\s %]", "", regex=True).str.replace(",", ".", regex=False)
    return pd.to_numeric(texte, errors="coerce").astype(float)


def _booleen(serie: pd.Series) -> pd.Series:
    valeurs = serie.astype("string").str.strip().str.lower().map(_sans_accent, na_action="ignore")
    return valeurs.map(
        lambda v: True if v in {"oui", "o", "yes", "y", "true", "vrai", "1", "1.0"}
        else (False if v in {"non", "n", "no", "false", "faux", "0", "0.0"} else pd.NA),
        na_action="ignore",
    ).astype("boolean")


def _statut_normalise(valeur) -> str:
    if pd.isna(valeur):
        return "Sans objet"
    v = _sans_accent(str(valeur)).lower()
    if "retard" in v:
        return "En retard"
    if any(m in v for m in ("termin", "realis", "clotur", "clos")):
        return "Terminée"
    if "cours" in v:
        return "En cours"
    if any(m in v for m in ("sans objet", "non requis", "accept", "n/a", "aucun", "non renseigne")):
        return "Sans objet"
    return "À lancer"


def nettoyer(brut: pd.DataFrame) -> tuple[pd.DataFrame, Rapport]:
    manquantes = [c for c in COLONNES if c not in brut.columns]
    if manquantes:
        raise RegistreInvalide("Colonnes absentes du fichier : " + ", ".join(manquantes))

    rapport = Rapport(lignes_lues=len(brut))
    df = brut.copy()
    for colonne in OPTIONNELLES:
        if colonne not in df:
            df[colonne] = pd.NA
    df = df[COLONNES + OPTIONNELLES]

    for colonne in df.columns:
        df[colonne] = df[colonne].astype("string").str.replace(r"\s+", " ", regex=True).str.strip().replace("", pd.NA)

    avant = len(df)
    df = df.drop_duplicates()
    rapport.doublons_exacts = avant - len(df)
    avant = len(df)
    df = df.drop_duplicates(subset="id_risque", keep="first")
    rapport.doublons_id = avant - len(df)

    rapport.valeurs_manquantes = {c: int(n) for c, n in df.isna().sum().items() if n}

    for colonne in ("date_identification", *OPTIONNELLES):
        df[colonne] = _dates(df[colonne])
    for colonne in NUMERIQUES:
        df[colonne] = _nombres(df[colonne])
    for colonne in ("risque_acceptable", "risque_materialise"):
        df[colonne] = _booleen(df[colonne])

    valides = df["date_identification"].notna() & df["criticite_inherente"].notna()
    rapport.lignes_invalides = int((~valides).sum())
    df = df[valides].copy()

    manque_residuel = df["criticite_residuelle"].isna()
    rapport.residuels_completes = int(manque_residuel.sum())
    df.loc[manque_residuel, "criticite_residuelle"] = df.loc[manque_residuel, "criticite_inherente"]

    for colonne in ("cout_action_mad", "impact_financier_reel_mad"):
        df[colonne] = df[colonne].fillna(0.0)
    for colonne in DIMENSIONS:
        df[colonne] = df[colonne].fillna("Non renseigné")

    gpd = df["gravite"] * df["probabilite"] * df["detectabilite"]
    rapport.ecarts_rpn = int(((gpd != df["RPN"]) & gpd.notna() & df["RPN"].notna()).sum())
    gp = df["gravite"] * df["probabilite"]
    rapport.ecarts_criticite = int(((gp != df["criticite_inherente"]) & gp.notna()).sum())

    df["statut_normalise"] = df["statut_action"].map(_statut_normalise)
    df["annee"] = df["date_identification"].dt.year
    df["trimestre"] = df["date_identification"].dt.to_period("Q").astype(str)
    df["reduction_points"] = df["criticite_inherente"] - df["criticite_residuelle"]
    df["au_dessus_seuil"] = df["criticite_residuelle"] > df["seuil_appetence"]
    aucune_seuil = df["seuil_appetence"].isna()
    df.loc[aucune_seuil, "au_dessus_seuil"] = df.loc[aucune_seuil, "risque_acceptable"].eq(False).fillna(False).astype(bool)

    aujourd_hui = pd.Timestamp(date.today())
    echeance_passee = df["date_echeance"].notna() & (df["date_echeance"] < aujourd_hui)
    ouverte = ~df["statut_normalise"].isin(["Terminée", "Sans objet"])
    df["action_en_retard"] = (df["statut_normalise"].eq("En retard") | (echeance_passee & ouverte)).astype(bool)
    df["realisee_en_retard"] = (df["date_realisation"] > df["date_echeance"]).fillna(False).astype(bool)

    rapport.lignes_finales = len(df)
    if df.empty:
        raise RegistreInvalide("Aucune ligne exploitable : vérifiez date_identification et criticite_inherente.")
    return df.reset_index(drop=True), rapport


def charger(contenu: bytes) -> tuple[pd.DataFrame, Rapport]:
    return nettoyer(lire_csv(contenu))


def source_par_defaut() -> tuple[Path, bool]:
    """Renvoie le fichier à charger et indique s'il s'agit de données simulées."""
    if FICHIER_OFFICIEL.exists():
        return FICHIER_OFFICIEL, False
    return FICHIER_SIMULE, True


def indicateurs(df: pd.DataFrame) -> dict:
    inherente = df["criticite_inherente"].mean()
    residuelle = df["criticite_residuelle"].mean()
    return {
        "total": len(df),
        "criticite_inherente": inherente,
        "criticite_residuelle": residuelle,
        "reduction_pct": (inherente - residuelle) / inherente * 100 if inherente else 0.0,
        "au_dessus_seuil": int(df["au_dessus_seuil"].sum()),
        "actions_retard": int(df["action_en_retard"].sum()),
        "efficacite": df["efficacite_action_pct"].mean(),
        "cout": df["cout_action_mad"].sum(),
        "pertes": df["impact_financier_reel_mad"].sum(),
        "materialises": int(df["risque_materialise"].fillna(False).sum()),
    }


def pareto(df: pd.DataFrame, dimension: str, mesure: str = "RPN") -> pd.DataFrame:
    table = df.groupby(dimension, as_index=False)[mesure].sum().sort_values(mesure, ascending=False)
    total = table[mesure].sum()
    table["part"] = table[mesure] / total * 100 if total else 0.0
    table["cumul"] = table["part"].cumsum()
    return table


def _fr(valeur: float, decimales: int = 1) -> str:
    return f"{valeur:.{decimales}f}".replace(".", ",")


def format_mad(valeur: float) -> str:
    if abs(valeur) >= 1_000_000:
        return f"{valeur / 1_000_000:.1f} M MAD".replace(".", ",")
    if abs(valeur) >= 1_000:
        return f"{valeur / 1_000:.0f} k MAD"
    return f"{valeur:.0f} MAD"


def profils_categories(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby("categorie_risque").agg(
        nombre=("id_risque", "size"),
        gravite=("gravite", "mean"),
        probabilite=("probabilite", "mean"),
        residuelle=("criticite_residuelle", "mean"),
        au_dessus=("au_dessus_seuil", "sum"),
    )


def conclusions(df: pd.DataFrame) -> list[tuple[str, str]]:
    """Constats et recommandations, recalculés sur la sélection en cours."""
    k = indicateurs(df)
    profils = profils_categories(df)
    constats: list[tuple[str, str]] = [
        (
            "Effet des traitements",
            f"La criticité moyenne passe de {_fr(k['criticite_inherente'])} à {_fr(k['criticite_residuelle'])} "
            f"après traitement, soit {k['reduction_pct']:.0f} % de réduction. "
            f"Conserver les plans d'action dont l'efficacité dépasse la moyenne de {k['efficacite']:.0f} %.",
        )
    ]

    gravite_seuil = profils["gravite"].quantile(0.75)
    rares = profils[(profils["gravite"] >= gravite_seuil) & (profils["nombre"] <= profils["nombre"].median())]
    if not rares.empty:
        noms = ", ".join(rares.sort_values("gravite", ascending=False).index[:3])
        constats.append(
            (
                "Risques rares mais graves",
                f"{noms} : peu d'occurrences, gravité moyenne très élevée. "
                "Le faible volume ne justifie pas une surveillance allégée : garder une revue individuelle de chaque cas.",
            )
        )

    frequents = profils.sort_values("nombre", ascending=False).head(2)
    part = frequents["nombre"].sum() / len(df) * 100
    constats.append(
        (
            "Risques fréquents",
            f"{' et '.join(frequents.index)} concentrent {part:.0f} % des risques. "
            "Agir à la source avec des audits ciblés et des standards de poste aura le plus fort effet de volume.",
        )
    )

    if k["au_dessus_seuil"]:
        par_processus = df[df["au_dessus_seuil"]].groupby("processus").size().sort_values(ascending=False)
        constats.append(
            (
                "Seuil d'appétence",
                f"{k['au_dessus_seuil']} risques restent au-dessus du seuil après traitement, "
                f"dont {int(par_processus.iloc[0])} sur le processus {par_processus.index[0]}. "
                "Ces dossiers doivent recevoir un traitement complémentaire ou une acceptation formelle.",
            )
        )

    if k["actions_retard"]:
        constats.append(
            (
                "Actions en retard",
                f"{k['actions_retard']} actions sont en retard ({k['actions_retard'] / len(df) * 100:.0f} % du registre). "
                "Inscrire ces actions au point de pilotage et réaffecter les ressources sur les plus critiques.",
            )
        )

    if k["cout"] > 0 and k["pertes"] > 0:
        ratio = k["pertes"] / k["cout"]
        lecture = (
            "Les pertes réelles dépassent l'investissement préventif : le budget d'actions mérite d'être renforcé."
            if ratio > 1
            else "L'investissement préventif dépasse les pertes constatées : vérifier que les actions les plus coûteuses portent sur les risques les plus graves."
        )
        constats.append(
            (
                "Coûts et pertes",
                f"{format_mad(k['cout'])} engagés en actions pour {format_mad(k['pertes'])} de pertes réelles, "
                f"soit un ratio pertes / coûts de {_fr(ratio, 2)}. {lecture}",
            )
        )
    return constats


def niveau_croise(df: pd.DataFrame) -> pd.DataFrame:
    ordre = ["Faible", "Modéré", "Élevé", "Critique"]
    table = pd.crosstab(df["niveau_risque_inherent"], df["niveau_risque_residuel"])
    lignes = [n for n in ordre if n in table.index] + [n for n in table.index if n not in ordre]
    colonnes = [n for n in ordre if n in table.columns] + [n for n in table.columns if n not in ordre]
    return table.loc[lignes, colonnes]


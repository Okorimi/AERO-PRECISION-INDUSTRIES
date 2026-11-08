"""Stockage unique de l'application (SQLite). Toutes les pages lisent cette source."""
from __future__ import annotations

import secrets
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import pandas as pd

from . import config, scoring, seed

REVISION_DEMO = 2

_SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (cle TEXT PRIMARY KEY, valeur TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS risks (
    id TEXT PRIMARY KEY,
    titre TEXT NOT NULL,
    processus TEXT NOT NULL,
    categorie TEXT NOT NULL,
    cause TEXT NOT NULL,
    effet TEXT NOT NULL,
    date_identification TEXT NOT NULL,
    gravite INTEGER, occurrence INTEGER, detection INTEGER,
    g_res INTEGER, o_res INTEGER, d_res INTEGER
);
CREATE TABLE IF NOT EXISTS actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    risk_id TEXT NOT NULL REFERENCES risks(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    responsable TEXT NOT NULL,
    echeance TEXT,
    statut TEXT NOT NULL
);
"""


@dataclass
class Action:
    id: int
    risk_id: str
    description: str
    responsable: str
    echeance: date | None
    statut: str

    @property
    def en_retard(self) -> bool:
        return self.echeance is not None and self.echeance < date.today() and self.statut != config.STATUT_TERMINE


@dataclass
class Risk:
    id: str
    titre: str
    processus: str
    categorie: str
    cause: str
    effet: str
    date_identification: date
    gravite: int | None = None
    occurrence: int | None = None
    detection: int | None = None
    g_res: int | None = None
    o_res: int | None = None
    d_res: int | None = None
    actions: list[Action] = field(default_factory=list)

    @property
    def evalue(self) -> bool:
        return None not in (self.gravite, self.occurrence, self.detection)

    @property
    def reevalue(self) -> bool:
        return None not in (self.g_res, self.o_res, self.d_res)

    @property
    def npr(self) -> int | None:
        return scoring.calc_npr(self.gravite, self.occurrence, self.detection) if self.evalue else None

    @property
    def npr_res(self) -> int | None:
        return scoring.calc_npr(self.g_res, self.o_res, self.d_res) if self.reevalue else None

    @property
    def niveau(self) -> str | None:
        return scoring.niveau_npr(self.npr) if self.evalue else None

    @property
    def niveau_res(self) -> str | None:
        return scoring.niveau_npr(self.npr_res) if self.reevalue else None

    @property
    def delta(self) -> int | None:
        return scoring.delta_npr(self.npr, self.npr_res) if self.evalue and self.reevalue else None

    @property
    def reduction(self) -> float | None:
        return scoring.reduction_pct(self.npr, self.npr_res) if self.evalue and self.reevalue else None

    @property
    def maitrise(self) -> bool:
        return scoring.est_maitrise([a.statut for a in self.actions], self.npr_res)

    @property
    def libelle(self) -> str:
        return f"{self.id} · {self.titre}"


@contextmanager
def _db(path: Path | None = None):
    path = path or config.DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def _date(valeur: str | None) -> date | None:
    return date.fromisoformat(valeur) if valeur else None


def _iso(valeur: date | None) -> str | None:
    return valeur.isoformat() if valeur else None


def _meta(conn, cle: str) -> str | None:
    ligne = conn.execute("SELECT valeur FROM meta WHERE cle = ?", (cle,)).fetchone()
    return ligne["valeur"] if ligne else None


def _set_meta(conn, cle: str, valeur) -> None:
    conn.execute(
        "INSERT INTO meta(cle, valeur) VALUES(?, ?) ON CONFLICT(cle) DO UPDATE SET valeur = excluded.valeur",
        (cle, str(valeur)),
    )


def _next_id(conn) -> str:
    # Le compteur ne recule jamais : un identifiant supprimé n'est pas réattribué.
    numero = int(_meta(conn, "prochain_id") or 1)
    _set_meta(conn, "prochain_id", numero + 1)
    return f"R{numero:02d}"


def ensure_ready() -> None:
    """Crée le schéma, charge l'étude de cas au premier lancement, sinon met la démo à niveau."""
    with _db() as conn:
        conn.executescript(_SCHEMA)
        premier_lancement = _meta(conn, "scenario") is None
        if not premier_lancement:
            _migrer_demo(conn)
    if premier_lancement:
        load_scenario(config.SCENARIO_CAS)


def _migrer_demo(conn) -> None:
    """Ajoute les NPR′ cibles aux anciennes bases sans écraser une saisie de l'utilisateur."""
    if int(_meta(conn, "revision_demo") or 1) >= REVISION_DEMO:
        return
    for d in seed.cas_etude():
        conn.execute(
            """UPDATE risks SET g_res = ?, o_res = ?, d_res = ?
               WHERE titre = ? AND gravite = ? AND occurrence = ? AND detection = ?
                 AND g_res IS NULL AND o_res IS NULL AND d_res IS NULL""",
            (*d["residuel"], d["titre"], d["gravite"], d["occurrence"], d["detection"]),
        )
    for titre in ("Panne machine imprévue", "Mauvais état de surface"):
        conn.execute("UPDATE risks SET o_res = 2 WHERE titre = ? AND g_res = 6 AND o_res = 3 AND d_res = 3", (titre,))
    _set_meta(conn, "revision_demo", REVISION_DEMO)


def secret_local() -> str:
    """Secret propre à cette installation, utilisé pour signer « Se souvenir de moi »."""
    with _db() as conn:
        conn.executescript(_SCHEMA)
        valeur = _meta(conn, "secret_session")
        if valeur is None:
            valeur = secrets.token_hex(32)
            _set_meta(conn, "secret_session", valeur)
        return valeur


def scenario() -> str:
    with _db() as conn:
        return _meta(conn, "scenario") or config.SCENARIO_CAS


def load_scenario(nom: str) -> None:
    donnees = seed.cas_etude() if nom == config.SCENARIO_CAS else seed.portefeuille_etendu()
    with _db() as conn:
        conn.execute("DELETE FROM risks")
        conn.execute("DELETE FROM actions")
        conn.execute("DELETE FROM sqlite_sequence WHERE name = 'actions'")
        _set_meta(conn, "prochain_id", 1)
        _set_meta(conn, "scenario", nom)
        _set_meta(conn, "revision_demo", REVISION_DEMO)
        for ligne in donnees:
            _insert(conn, ligne)


def _insert(conn, d: dict) -> str:
    risk_id = _next_id(conn)
    res = d.get("residuel") or (None, None, None)
    conn.execute(
        """INSERT INTO risks(id, titre, processus, categorie, cause, effet, date_identification,
                             gravite, occurrence, detection, g_res, o_res, d_res)
           VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            risk_id, d["titre"], d["processus"], d["categorie"], d["cause"], d["effet"],
            _iso(d["date_identification"]), d.get("gravite"), d.get("occurrence"), d.get("detection"), *res,
        ),
    )
    for action in d.get("actions", []):
        _insert_action(conn, risk_id, action)
    return risk_id


def _insert_action(conn, risk_id: str, a: dict) -> int:
    curseur = conn.execute(
        "INSERT INTO actions(risk_id, description, responsable, echeance, statut) VALUES(?, ?, ?, ?, ?)",
        (risk_id, a["description"], a["responsable"], _iso(a.get("echeance")), a.get("statut", config.STATUT_A_FAIRE)),
    )
    return curseur.lastrowid


def list_risks() -> list[Risk]:
    with _db() as conn:
        lignes = conn.execute("SELECT * FROM risks").fetchall()
        lignes_actions = conn.execute("SELECT * FROM actions ORDER BY id").fetchall()
    actions: dict[str, list[Action]] = {}
    for a in lignes_actions:
        actions.setdefault(a["risk_id"], []).append(
            Action(a["id"], a["risk_id"], a["description"], a["responsable"], _date(a["echeance"]), a["statut"])
        )
    risques = []
    for r in lignes:
        donnees = dict(r)
        donnees["date_identification"] = _date(donnees["date_identification"])
        risques.append(Risk(**donnees, actions=actions.get(r["id"], [])))
    return sorted(risques, key=lambda r: int(r.id[1:]))


def get_risk(risk_id: str) -> Risk | None:
    return next((r for r in list_risks() if r.id == risk_id), None)


def add_risk(data: dict) -> str:
    with _db() as conn:
        return _insert(conn, data)


def update_identity(risk_id: str, titre, processus, categorie, cause, effet, date_identification) -> None:
    with _db() as conn:
        conn.execute(
            """UPDATE risks SET titre = ?, processus = ?, categorie = ?, cause = ?, effet = ?,
               date_identification = ? WHERE id = ?""",
            (titre, processus, categorie, cause, effet, _iso(date_identification), risk_id),
        )


def set_cotation(risk_id: str, g: int, o: int, d: int) -> None:
    scoring.calc_npr(g, o, d)
    with _db() as conn:
        conn.execute("UPDATE risks SET gravite = ?, occurrence = ?, detection = ? WHERE id = ?", (g, o, d, risk_id))


def set_residuel(risk_id: str, g: int, o: int, d: int) -> None:
    scoring.calc_npr(g, o, d)
    with _db() as conn:
        conn.execute("UPDATE risks SET g_res = ?, o_res = ?, d_res = ? WHERE id = ?", (g, o, d, risk_id))


def delete_risk(risk_id: str) -> None:
    with _db() as conn:
        conn.execute("DELETE FROM risks WHERE id = ?", (risk_id,))


def add_action(risk_id: str, description: str, responsable: str, echeance: date | None, statut: str) -> int:
    with _db() as conn:
        return _insert_action(
            conn, risk_id, {"description": description, "responsable": responsable, "echeance": echeance, "statut": statut}
        )


def update_action(action_id: int, **champs) -> None:
    autorises = {"description", "responsable", "echeance", "statut"}
    champs = {k: (_iso(v) if k == "echeance" else v) for k, v in champs.items() if k in autorises}
    if not champs:
        return
    colonnes = ", ".join(f"{c} = ?" for c in champs)
    with _db() as conn:
        conn.execute(f"UPDATE actions SET {colonnes} WHERE id = ?", (*champs.values(), action_id))


def delete_action(action_id: int) -> None:
    with _db() as conn:
        conn.execute("DELETE FROM actions WHERE id = ?", (action_id,))


def all_actions(risques: list[Risk]) -> list[tuple[Risk, Action]]:
    return [(r, a) for r in risques for a in r.actions]


def export_csv(risques: list[Risk]) -> bytes:
    """Export compatible Excel français : point-virgule et UTF-8 avec BOM."""
    lignes = [
        {
            "ID": r.id,
            "Risque": r.titre,
            "Processus": r.processus,
            "Catégorie": r.categorie,
            "Cause": r.cause,
            "Effet": r.effet,
            "Date d'identification": _iso(r.date_identification),
            "G": r.gravite,
            "O": r.occurrence,
            "D": r.detection,
            "NPR": r.npr,
            "Niveau": r.niveau,
            "Actions": " | ".join(a.description for a in r.actions),
            "Responsables": " | ".join(a.responsable for a in r.actions),
            "Statuts": " | ".join(a.statut for a in r.actions),
            "G'": r.g_res,
            "O'": r.o_res,
            "D'": r.d_res,
            "NPR résiduel": r.npr_res,
            "Niveau résiduel": r.niveau_res,
            "Delta NPR": r.delta,
            "Maîtrisé": "Oui" if r.maitrise else "Non",
        }
        for r in risques
    ]
    return pd.DataFrame(lignes).to_csv(index=False, sep=";").encode("utf-8-sig")

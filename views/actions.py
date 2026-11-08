from __future__ import annotations

import hashlib
import re
from html import escape

import pandas as pd
import streamlit as st
from streamlit_sortables import sort_items

from aero import config, store, ui

STYLE_KANBAN = """
.sortable-component { display: flex; flex-wrap: wrap; align-items: flex-start !important; gap: 12px; border: 0; padding: 0; background: transparent; }
.sortable-container { flex: 1 1 240px; min-width: 240px; margin: 0 !important; align-self: flex-start !important; background: #F3F5FE; border-radius: 14px; padding: 6px; counter-reset: none; }
.sortable-container-header { background: transparent; color: #0B1F3A; font-weight: 700; font-size: 15px; padding: 8px 10px; }
.sortable-container-body { background: transparent; min-height: 90px; }
.sortable-item, .sortable-item:hover {
  background: #FFFFFF; color: #0B1F3A; border: 1px solid #E2E7F3; border-radius: 10px;
  padding: 10px 12px; margin: 6px 2px; font-size: 13px; line-height: 1.35; height: auto; white-space: normal; cursor: grab;
  box-shadow: 0 6px 14px -10px rgba(11,31,58,.35); text-align: left;
}
"""


def _etiquette(risque: store.Risk, action: store.Action) -> str:
    echeance = action.echeance.strftime("%d/%m/%Y") if action.echeance else "sans date"
    alerte = "🔴 EN RETARD · " if action.en_retard else ""
    return f"#{action.id} · {risque.id} · {action.description} | {action.responsable} | {alerte}{echeance}"


def _kanban(paires: list[tuple[store.Risk, store.Action]]) -> None:
    colonnes = [
        {"header": statut, "items": [_etiquette(r, a) for r, a in paires if a.statut == statut]}
        for statut in config.STATUTS
    ]
    empreinte = hashlib.md5(repr([(a.id, a.statut, a.description) for _, a in paires]).encode()).hexdigest()[:10]
    resultat = sort_items(colonnes, multi_containers=True, custom_style=STYLE_KANBAN, key=f"kanban_{empreinte}")
    actuels = {a.id: a.statut for _, a in paires}
    changements = 0
    for colonne in resultat:
        for libelle in colonne["items"]:
            trouve = re.match(r"#(\d+) ", libelle)
            if trouve and actuels.get(int(trouve[1])) != colonne["header"]:
                store.update_action(int(trouve[1]), statut=colonne["header"])
                changements += 1
    if changements:
        ui.annoncer("Statut de l'action mis à jour.")
        st.rerun()


def _liste(paires: list[tuple[store.Risk, store.Action]]) -> None:
    table = pd.DataFrame(
        [
            {
                "_id": a.id,
                "Alerte": "🔴 En retard" if a.en_retard else "",
                "Risque": r.libelle,
                "Action": a.description,
                "Responsable": a.responsable,
                "Échéance": a.echeance,
                "Statut": a.statut,
            }
            for r, a in paires
        ]
    )
    version = st.session_state.get("act_v", 0)
    edition = st.data_editor(
        table,
        hide_index=True,
        width="stretch",
        key=f"act_edit_{version}",
        disabled=["_id", "Alerte", "Risque"],
        column_order=["Alerte", "Risque", "Action", "Responsable", "Échéance", "Statut"],
        column_config={
            "Alerte": st.column_config.TextColumn(width="small"),
            "Risque": st.column_config.TextColumn(width="medium"),
            "Action": st.column_config.TextColumn(width="large", required=True),
            "Responsable": st.column_config.TextColumn(width="medium", required=True),
            "Échéance": st.column_config.DateColumn(format="DD/MM/YYYY", width="small"),
            "Statut": st.column_config.SelectboxColumn(options=config.STATUTS, required=True, width="small"),
        },
    )
    modifie = False
    for avant, apres in zip(table.to_dict("records"), edition.to_dict("records")):
        champs = {}
        for colonne, champ in (("Action", "description"), ("Responsable", "responsable"), ("Statut", "statut")):
            if avant[colonne] != apres[colonne] and str(apres[colonne]).strip():
                champs[champ] = apres[colonne]
        if pd.notna(apres["Échéance"]) and avant["Échéance"] != apres["Échéance"]:
            champs["echeance"] = pd.Timestamp(apres["Échéance"]).date()
        if champs:
            store.update_action(int(avant["_id"]), **champs)
            modifie = True
    if modifie:
        st.session_state["act_v"] = version + 1
        ui.annoncer("Actions enregistrées.")
        st.rerun()


def render() -> None:
    ui.en_tete("Gestion des actions", "ISO 31000, traitement du risque. Faites glisser une carte pour changer son statut.")
    risques = store.list_risks()
    paires = store.all_actions(risques)
    retards = [(r, a) for r, a in paires if a.en_retard]
    terminees = sum(a.statut == config.STATUT_TERMINE for _, a in paires)
    ui.grille_kpi(
        [
            ("Actions totales", str(len(paires)), "Tous risques confondus", ""),
            ("En retard", str(len(retards)), "Échéance dépassée, action non terminée", "crit"),
            ("Terminées", str(terminees), "Réévaluez ensuite le risque", "ok"),
            ("En cours", str(sum(a.statut == config.STATUT_EN_COURS for _, a in paires)), "Actions lancées", ""),
        ]
    )
    for r, a in retards:
        st.markdown(
            f'<div class="late"><b>{r.id}</b> {escape(a.description)} ({escape(a.responsable)}), '
            f"échéance dépassée le {a.echeance.strftime('%d/%m/%Y')}.</div>",
            unsafe_allow_html=True,
        )

    with st.expander("Nouvelle action corrective", icon=":material/add:"):
        if risques:
            cible = ui.choix_risque("Risque associé", risques, "act_risk")
            ui.formulaire_ajout_action(cible, "act_add")
        else:
            st.info("Ajoutez d'abord un risque depuis la page Identification.")

    if not paires:
        st.info("Aucune action enregistrée. Ajoutez la première action ci-dessus.")
        return
    onglet_kanban, onglet_liste = st.tabs(["Kanban", "Liste"])
    with onglet_kanban:
        _kanban(paires)
    with onglet_liste:
        _liste(paires)

from __future__ import annotations

import pandas as pd
import streamlit as st

from aero import config, store, ui


def render() -> None:
    ui.en_tete("Identification des risques", "ISO 31000, étape d'identification. Enregistrez un risque puis retrouvez-le dans le registre.")
    with st.expander("Nouveau risque", expanded=False, icon=":material/add:"):
        ui.formulaire_risque("page_add")

    risques = store.list_risks()
    carte = ui.carte("table", "Registre des risques", "Cliquez sur l'en-tête d'une colonne pour trier, puis sélectionnez une ligne pour agir.")
    with carte:
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
        recherche = c1.text_input("Recherche", placeholder="Titre, cause ou effet", key="id_q")
        processus = c2.multiselect("Processus", config.PROCESSUS, key="id_p", placeholder="Tous")
        categories = c3.multiselect("Catégorie", config.CATEGORIES, key="id_c", placeholder="Toutes")
        niveaux = c4.multiselect("Niveau", config.NIVEAUX, key="id_n", placeholder="Tous")

        selection = risques
        if recherche.strip():
            q = recherche.strip().lower()
            selection = [r for r in selection if q in f"{r.titre} {r.cause} {r.effet}".lower()]
        if processus:
            selection = [r for r in selection if r.processus in processus]
        if categories:
            selection = [r for r in selection if r.categorie in categories]
        if niveaux:
            selection = [r for r in selection if r.niveau in niveaux]

        if not selection:
            st.info("Aucun risque ne correspond à ces critères.")
            return

        table = pd.DataFrame(
            [
                {
                    "ID": r.id, "Risque": r.titre, "Processus": r.processus, "Catégorie": r.categorie,
                    "Cause": r.cause, "Effet": r.effet, "Date": r.date_identification, "NPR": r.npr,
                    "Niveau": r.niveau or "Non évalué",
                }
                for r in selection
            ]
        )
        evenement = st.dataframe(
            table,
            hide_index=True,
            width="stretch",
            on_select="rerun",
            selection_mode="single-row",
            key="id_table",
            column_order=["ID", "Risque", "NPR", "Niveau", "Processus", "Catégorie", "Date", "Cause", "Effet"],
            column_config={
                "ID": st.column_config.TextColumn(width="small"),
                "Risque": st.column_config.TextColumn(width="medium"),
                "Cause": st.column_config.TextColumn(width="medium"),
                "Effet": st.column_config.TextColumn(width="medium"),
                "Date": st.column_config.DateColumn(format="DD/MM/YYYY", width="small"),
                "NPR": st.column_config.NumberColumn(width="small"),
                "Niveau": st.column_config.TextColumn(width="small"),
            },
        )
        lignes = evenement.selection.rows
        cible = selection[lignes[0]] if lignes and lignes[0] < len(selection) else None
        if st.button("Modifier ou supprimer le risque sélectionné", disabled=cible is None, key="id_open", type="primary"):
            ui.fiche_risque(cible.id)

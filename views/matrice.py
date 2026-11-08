from __future__ import annotations

import streamlit as st

from aero import charts, config, store, ui
from aero.ui import badge


def render() -> None:
    ui.en_tete("Matrice de criticité", "ISO 31010. Survolez une pastille pour le détail, cliquez dessus pour ouvrir la fiche du risque.")
    risques = store.list_risks()
    vue = st.segmented_control("Vue", ["Avant actions", "Après actions"], default="Avant actions", key="mx_vue", label_visibility="collapsed") or "Avant actions"
    residuel = vue == "Après actions"

    gauche, droite = st.columns([2.6, 1], gap="medium")
    with gauche:
        with ui.carte("mx"):
            evenement = st.plotly_chart(
                charts.matrice(risques, residuel), width="stretch", config=charts.CONFIG,
                on_select="rerun", selection_mode="points", key=f"mx_chart_{vue}",
            )
    points = evenement.selection.points if evenement and evenement.selection else []
    choisi = next((p["customdata"][0] for p in points if p.get("customdata")), None)
    if choisi and choisi != st.session_state.get("mx_dernier"):
        st.session_state["mx_dernier"] = choisi
        ui.fiche_risque(choisi)
    elif not choisi:
        st.session_state["mx_dernier"] = None

    with droite:
        with ui.carte("mxleg", "Légende"):
            st.markdown("<br>".join(badge(n) for n in config.NIVEAUX), unsafe_allow_html=True)
            st.markdown(
                '<p class="card-note" style="margin-top:.7rem">Le fond de la case dépend du produit G × O ramené sur 5. '
                "Le contour de la pastille indique le niveau selon le NPR, qui intègre aussi la détection.</p>",
                unsafe_allow_html=True,
            )
        st.write("")
        with ui.carte("mxopen", "Ouvrir une fiche"):
            evalues = [r for r in risques if r.evalue]
            if evalues:
                cible = ui.choix_risque("Risque", evalues, "mx_sel", visible=False)
                if st.button("Ouvrir la fiche", key="mx_open", width="stretch"):
                    ui.fiche_risque(cible.id)
        non_places = sum((r.gravite is None) if not residuel else (r.g_res is None) for r in risques)
        if non_places:
            st.caption(f"{non_places} risque(s) sans cotation n'apparaissent pas dans cette vue.")

from __future__ import annotations

import streamlit as st

from aero import store, ui


def render() -> None:
    ui.en_tete("Évaluation des risques", "ISO 31010, AMDEC. Le NPR et le niveau sont recalculés à chaque mouvement de curseur.")
    risques = store.list_risks()
    if not risques:
        st.info("Le registre est vide. Ajoutez un risque depuis la page Identification.")
        return
    carte = ui.carte("eval")
    with carte:
        risque = ui.choix_risque("Risque à évaluer", risques, "eval_sel")
        st.caption(f"Cause : {risque.cause}")
        ui.editeur_cotation(risque, "page_eval")
        ui.comparatif_avant_apres(risque)

from __future__ import annotations

import pandas as pd
import streamlit as st

from aero import charts, store, ui


def render() -> None:
    ui.en_tete("Suivi avant / après", "ISO 31000, surveillance et revue. Réévaluez chaque risque une fois son action mise en place.")
    risques = [r for r in store.list_risks() if r.evalue]
    if not risques:
        st.info("Aucun risque évalué. Commencez par la page Évaluation.")
        return

    carte = ui.carte("reeval", "Module de réévaluation AMDEC", "Le NPR′ et le gain de sécurité sont recalculés en direct. Un risque devient maîtrisé quand ses actions sont terminées et que son NPR′ passe sous 100.")
    with carte:
        risque = ui.choix_risque("Risque à réévaluer", risques, "sv_sel")
        en_cours = [a for a in risque.actions if a.statut != "Terminé"]
        if en_cours:
            st.caption(f"{len(en_cours)} action(s) encore ouverte(s) : ce risque ne pourra pas être compté comme maîtrisé tant qu'elles ne sont pas terminées.")
        ui.editeur_reevaluation(risque, "page_res")

    st.write("")
    reevalues = [r for r in risques if r.reevalue]
    moyenne = sum(r.reduction for r in reevalues) / len(reevalues) if reevalues else 0.0
    gauche, droite = st.columns([2.2, 1], gap="medium")
    with gauche:
        with ui.carte("sv_ba", "NPR avant et après actions"):
            st.plotly_chart(charts.avant_apres(risques), width="stretch", config=charts.CONFIG, key="sv_chart")
    with droite:
        note = f"Moyenne sur {len(reevalues)} risque(s) réévalué(s)." if reevalues else "Aucune réévaluation enregistrée pour le moment."
        with ui.carte("sv_gauge", "Réduction globale moyenne", note):
            st.plotly_chart(charts.jauge_reduction(moyenne), width="stretch", config=charts.CONFIG, key="sv_gauge_chart")

    st.write("")
    table = pd.DataFrame(
        [
            {
                "ID": r.id, "Risque": r.titre, "NPR initial": r.npr, "Niveau avant": r.niveau, "NPR′": r.npr_res,
                "Niveau après": r.niveau_res or "À réévaluer", "Δ NPR": r.delta, "Réduction": r.reduction,
                "Maîtrisé": "Oui" if r.maitrise else "Non",
            }
            for r in risques
        ]
    )
    with ui.carte("sv_table", "Détail par risque"):
        st.dataframe(
            table, hide_index=True, width="stretch",
            column_config={"Réduction": st.column_config.NumberColumn(format="%.0f %%")},
        )

from __future__ import annotations

from html import escape

import streamlit as st

from aero import charts, config, store, ui
from aero.ui import badge, fr


def _contexte() -> None:
    bas, haut = 19.90, 20.25
    pos = lambda v: (v - bas) / (haut - bas) * 100
    gauche, largeur = pos(19.95), pos(20.05) - pos(19.95)
    ticks = "".join(
        f'<div class="tick" style="left:{pos(v):.2f}%">{libelle}</div>'
        for v, libelle in ((19.95, "19,95"), (20.05, "20,05"))
    )
    carte = ui.carte("contexte", "Contexte projet")
    carte.markdown(
        f"""<div class="ctx">
        <dl>
          <dt>Entreprise</dt><dd>AERO PRECISION INDUSTRIES</dd>
          <dt>Activité</dt><dd>Usinage de pièces aéronautiques de précision</dd>
          <dt>Produit étudié</dt><dd>Support de fixation en aluminium (usinage CNC)</dd>
          <dt>Diamètre nominal</dt><dd>20,00 mm, tolérance ±0,05 mm</dd>
        </dl>
        <div>
          <div class="tol" role="img" aria-label="Diamètre mesuré 20,18 mm, hors de la zone de tolérance 19,95 à 20,05 mm">
            <div class="rail"></div>
            <div class="band" style="left:{gauche:.2f}%;width:{largeur:.2f}%"></div>
            {ticks}
            <div class="pin" style="left:{pos(20.18):.2f}%"></div>
            <div class="pin-lab" style="left:{pos(20.18):.2f}%">20,18 mm</div>
          </div>
          <p class="tol-note">Diamètre mesuré à l'audit : <b>écart critique de +0,13 mm</b> au-delà de la limite haute (+0,18 mm par rapport au nominal).</p>
        </div>
        </div>""",
        unsafe_allow_html=True,
    )


def _indicateurs(risques: list[store.Risk]) -> None:
    evalues = [r for r in risques if r.evalue]
    critiques = sum(r.npr >= 200 for r in evalues)
    maitrises = sum(r.maitrise for r in risques)
    moyenne = sum(r.npr for r in evalues) / len(evalues) if evalues else 0
    ui.grille_kpi(
        [
            ("Risques identifiés", str(len(risques)), f"{len(evalues)} évalué(s)", ""),
            ("Risques critiques (NPR ≥ 200)", str(critiques), "Priorité de traitement", "crit"),
            ("Risques maîtrisés", str(maitrises), "Actions terminées et NPR′ < 100", "ok"),
            ("NPR moyen (avant actions)", fr(moyenne), f"Valeur exacte : {fr(moyenne, 1)}", ""),
        ]
    )


def _changer_statut(action_id: int, cle: str) -> None:
    store.update_action(action_id, statut=st.session_state[cle])
    ui.annoncer("Statut de l'action mis à jour.")


def _ligne_risque(r: store.Risk) -> None:
    with st.container(key=f"row_{r.id}"):
        colonnes = st.columns([3.1, 1.15, 2.5, 1.35, 1.25, 0.95], vertical_alignment="center")
        colonnes[0].markdown(
            f'<div class="rk-id">{r.id} · {escape(r.processus)}</div><div class="rk-title">{escape(r.titre)}</div>'
            f'<div class="rk-desc">{escape(r.cause)}</div>',
            unsafe_allow_html=True,
        )
        if r.evalue:
            colonnes[1].markdown(
                f'<div class="rk-npr">{r.npr}</div><div class="rk-formula">{r.gravite} × {r.occurrence} × {r.detection}</div>{badge(r.niveau)}',
                unsafe_allow_html=True,
            )
        else:
            colonnes[1].markdown(badge(None), unsafe_allow_html=True)

        action = r.actions[0] if r.actions else None
        if action:
            suite = f" (+{len(r.actions) - 1})" if len(r.actions) > 1 else ""
            alerte = ' <span class="badge bad">En retard</span>' if action.en_retard else ""
            colonnes[2].markdown(
                f'<div class="rk-small">{escape(action.description)}{suite}<br><span>{escape(action.responsable)}</span>{alerte}</div>',
                unsafe_allow_html=True,
            )
            cle = f"st_{action.id}"
            st.session_state[cle] = action.statut
            colonnes[3].selectbox(
                "Statut", config.STATUTS, key=cle, label_visibility="collapsed",
                on_change=_changer_statut, args=(action.id, cle),
            )
        else:
            colonnes[2].caption("Aucune action")

        if r.reevalue:
            signe = "+" if r.delta > 0 else ""
            maitrise = '<br><span class="badge good">Maîtrisé</span>' if r.maitrise else ""
            colonnes[4].markdown(
                f'<div class="rk-small"><b>NPR′ {r.npr_res}</b><br><span>Δ NPR {signe}{r.delta}</span>{maitrise}</div>',
                unsafe_allow_html=True,
            )
        else:
            colonnes[4].markdown('<div class="rk-small"><span>À réévaluer</span></div>', unsafe_allow_html=True)

        if colonnes[5].button("Gérer", key=f"open_{r.id}", width="stretch"):
            ui.fiche_risque(r.id)


def _registre(risques: list[store.Risk]) -> None:
    carte = ui.carte("registre", "Base AMDEC", "NPR = G × O × D. Changez un statut ici, ou ouvrez un risque pour le coter, le réévaluer, le modifier ou le supprimer.")
    with carte:
        if st.button("Ajouter un risque", type="primary", icon=":material/add:", key="add_risk"):
            ui.dialogue_ajout()
        entetes = st.columns([3.1, 1.15, 2.5, 1.35, 1.25, 0.95])
        for colonne, texte in zip(entetes, ["Risque", "NPR", "Action et responsable", "Statut", "Réévaluation", ""]):
            colonne.markdown(f'<div class="rk-head">{texte}</div>', unsafe_allow_html=True)
        if not risques:
            st.info("Aucun risque sur ce périmètre. Ajoutez-en un ou changez le filtre.")
        for risque in risques:
            _ligne_risque(risque)


def _classement(risques: list[store.Risk]) -> str:
    top = sorted((r for r in risques if r.evalue), key=lambda r: r.npr, reverse=True)[:5]
    maximum = top[0].npr if top else 1
    return "".join(
        f'<div class="rank"><small>{r.id}</small><div>{escape(r.titre)}</div>'
        f'<div class="bar"><i style="width:{r.npr / maximum * 100:.0f}%;background:{config.COULEURS_NIVEAU[r.niveau]}"></i></div>'
        f"<b>{r.npr}</b></div>"
        for r in top
    )


def render() -> None:
    ui.en_tete(config.HEADER_TITLE, config.HEADER_SUBTITLE, normes=True)

    tous = store.list_risks()
    _contexte()
    st.write("")
    filtre = st.pills("Filtrer par processus", ["Tous"] + config.PROCESSUS, default="Tous", key="dash_proc")
    risques = tous if filtre in (None, "Tous") else [r for r in tous if r.processus == filtre]

    _indicateurs(risques)
    _registre(risques)
    st.write("")

    if not any(r.evalue for r in risques):
        st.info("Aucun risque évalué sur ce périmètre : les graphiques apparaîtront après une première évaluation.")
        return

    gauche, droite = st.columns(2, gap="medium")
    with gauche:
        with ui.carte("donut", "Répartition par niveau de criticité"):
            st.plotly_chart(charts.donut_niveaux(risques), width="stretch", config=charts.CONFIG, key="dash_donut")
    with droite:
        with ui.carte("procbar", "NPR moyen par processus"):
            st.plotly_chart(charts.bar_npr_processus(risques), width="stretch", config=charts.CONFIG, key="dash_proc_chart")

    st.write("")
    gauche, droite = st.columns([1, 1.25], gap="medium")
    with gauche:
        with ui.carte("top", "Les 5 risques les plus critiques"):
            st.markdown(_classement(risques), unsafe_allow_html=True)
    with droite:
        reste = sum(r.evalue and not r.reevalue for r in risques)
        reevalues = [r for r in risques if r.reevalue]
        note = (
            f"Réduction globale moyenne : {fr(sum(r.reduction for r in reevalues) / len(reevalues))} %."
            if reevalues
            else "Aucune réévaluation enregistrée."
        )
        if reste:
            note += f" {reste} risque(s) en attente de réévaluation."
        with ui.carte("ba", "NPR avant et après actions", note):
            st.plotly_chart(charts.avant_apres(risques), width="stretch", config=charts.CONFIG, key="dash_ba")

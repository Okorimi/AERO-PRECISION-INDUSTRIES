"""Composants d'interface partagés entre les pages."""
from __future__ import annotations

from datetime import date
from html import escape

import streamlit as st

from . import config, scoring, store
from .store import Action, Risk


def fr(valeur: float, decimales: int = 0) -> str:
    return f"{valeur:.{decimales}f}".replace(".", ",")


def annoncer(message: str) -> None:
    """Conserve un message pour l'afficher après le prochain rechargement."""
    st.session_state["_annonce"] = message


def afficher_annonce() -> None:
    message = st.session_state.pop("_annonce", None)
    if message:
        st.toast(message, icon=":material/check_circle:")


def en_tete(titre: str, sous_titre: str = "", normes: bool = False) -> None:
    classe = ' class="norms"' if normes else ""
    bloc = f"<p{classe}>{escape(sous_titre)}</p>" if sous_titre else ""
    st.markdown(f'<div class="page-head"><h1>{escape(titre)}</h1>{bloc}</div>', unsafe_allow_html=True)


def badge(niveau: str | None) -> str:
    if not niveau:
        return '<span class="badge muted">Non évalué</span>'
    return (
        f'<span class="badge" style="background:{config.TEINTES_NIVEAU[niveau]}">'
        f'<i style="background:{config.COULEURS_NIVEAU[niveau]}"></i>{niveau}</span>'
    )


def carte(cle: str, titre: str | None = None, note: str | None = None):
    conteneur = st.container(key=f"card_{cle}")
    if titre:
        conteneur.markdown(f"### {titre}")
    if note:
        conteneur.markdown(f'<p class="card-note">{escape(note)}</p>', unsafe_allow_html=True)
    return conteneur


def grille_kpi(indicateurs: list[tuple[str, str, str, str]]) -> None:
    """Chaque indicateur : (libellé, valeur, précision, classe)."""
    cartes = "".join(
        f'<div class="kpi {classe}"><div class="lab">{escape(lab)}</div>'
        f'<div class="val">{escape(val)}</div><div class="sub">{escape(sub)}</div></div>'
        for lab, val, sub, classe in indicateurs
    )
    st.markdown(f'<div class="kpi-grid">{cartes}</div>', unsafe_allow_html=True)


def choix_risque(libelle: str, risques: list[Risk], cle: str, visible: bool = True) -> Risk:
    """Liste déroulante fondée sur les identifiants, stable si un risque change ou disparaît."""
    index = {r.id: r for r in risques}
    if st.session_state.get(cle) not in index:
        st.session_state.pop(cle, None)
    choisi = st.selectbox(
        libelle,
        list(index),
        format_func=lambda i: index[i].libelle,
        key=cle,
        label_visibility="visible" if visible else "collapsed",
    )
    return index[choisi]


def _rappel_echelle(code: str) -> None:
    e = config.ECHELLES[code]
    st.markdown(
        f'<div class="scale"><b>1</b> {escape(e[1])}<br><b>5</b> {escape(e[5])}<br><b>10</b> {escape(e[10])}</div>',
        unsafe_allow_html=True,
    )


def _curseurs(prefixe: str, defauts: tuple[int, int, int], suffixe: str = "", rappel: bool = False) -> tuple[int, int, int]:
    colonnes = st.columns(3)
    notes = []
    for colonne, code, defaut in zip(colonnes, "GOD", defauts):
        with colonne:
            notes.append(
                st.slider(f"{config.ECHELLES[code]['nom']} ({code}{suffixe})", 1, 10, int(defaut), key=f"{prefixe}_{code}")
            )
            if rappel:
                _rappel_echelle(code)
    return tuple(notes)


def editeur_cotation(risque: Risk, prefixe: str, rappel: bool = True) -> None:
    defauts = (risque.gravite or 5, risque.occurrence or 5, risque.detection or 5)
    g, o, d = _curseurs(f"{prefixe}_{risque.id}", defauts, rappel=rappel)
    npr = scoring.calc_npr(g, o, d)
    st.markdown(
        f'<div class="live"><div><div class="n">{npr}</div><div class="cap">NPR = {g} × {o} × {d}</div></div>'
        f"{badge(scoring.niveau_npr(npr))}</div>",
        unsafe_allow_html=True,
    )
    if st.button("Enregistrer l'évaluation", key=f"{prefixe}_{risque.id}_save", type="primary"):
        store.set_cotation(risque.id, g, o, d)
        annoncer(f"Évaluation de {risque.id} enregistrée : NPR {npr}.")
        st.rerun()


def editeur_reevaluation(risque: Risk, prefixe: str) -> None:
    if not risque.evalue:
        st.info("Évaluez d'abord ce risque pour pouvoir le réévaluer.")
        return
    defauts = (
        risque.g_res or risque.gravite,
        risque.o_res or risque.occurrence,
        risque.d_res or risque.detection,
    )
    g, o, d = _curseurs(f"{prefixe}_{risque.id}", defauts, suffixe="′")
    apres = scoring.calc_npr(g, o, d)
    delta = scoring.delta_npr(risque.npr, apres)
    signe = "+" if delta > 0 else ""
    st.markdown(
        f'<div class="live">'
        f'<div><div class="n">{risque.npr}</div><div class="cap">NPR initial</div></div>'
        f'<div><div class="n">{apres}</div><div class="cap">NPR′ = {g} × {o} × {d}</div></div>'
        f'<div><div class="n">{signe}{delta}</div><div class="cap">Gain de sécurité (Δ NPR), {fr(scoring.reduction_pct(risque.npr, apres))} %</div></div>'
        f"{badge(scoring.niveau_npr(apres))}</div>",
        unsafe_allow_html=True,
    )
    if st.button("Enregistrer la réévaluation", key=f"{prefixe}_{risque.id}_save", type="primary"):
        store.set_residuel(risque.id, g, o, d)
        annoncer(f"Réévaluation de {risque.id} enregistrée : NPR′ {apres}, Δ NPR {signe}{delta}.")
        st.rerun()


def comparatif_avant_apres(risque: Risk) -> None:
    if not (risque.evalue and risque.reevalue):
        st.caption("Ce risque n'a pas encore de NPR′ après actions.")
        return
    st.markdown(
        f'<div class="compare">'
        f'<div><div class="n">{risque.npr}</div><div class="cap">Avant actions</div></div>{badge(risque.niveau)}'
        f'<div class="arrow" aria-hidden="true">→</div>'
        f'<div><div class="n">{risque.npr_res}</div><div class="cap">Après actions</div></div>{badge(risque.niveau_res)}'
        f'<div><div class="n">{fr(risque.reduction)} %</div><div class="cap">Réduction du NPR</div></div></div>',
        unsafe_allow_html=True,
    )


def options_responsables(valeur: str = "") -> tuple[list[str], list[str]]:
    selection = [v.strip() for v in valeur.split("/") if v.strip()]
    options = config.RESPONSABLES + [v for v in selection if v not in config.RESPONSABLES]
    return options, selection


def _champs_action(cle: str, action: Action | None = None) -> tuple[str, str, date | None, str]:
    description = st.text_input("Action corrective", value=action.description if action else "", key=f"{cle}_desc")
    options, selection = options_responsables(action.responsable if action else "")
    responsables = st.multiselect("Responsable", options, default=selection, key=f"{cle}_resp", placeholder="Choisir un ou plusieurs responsables")
    c1, c2 = st.columns(2)
    echeance = c1.date_input("Échéance", value=action.echeance if action else date.today(), key=f"{cle}_date", format="DD/MM/YYYY")
    statut = c2.selectbox("Statut", config.STATUTS, index=config.STATUTS.index(action.statut) if action else 0, key=f"{cle}_statut")
    return description.strip(), " / ".join(responsables), echeance, statut


def formulaire_ajout_action(risque: Risk, prefixe: str) -> None:
    compteur = st.session_state.get(f"{prefixe}_n", 0)
    with st.form(f"{prefixe}_{risque.id}_{compteur}"):
        description, responsable, echeance, statut = _champs_action(f"{prefixe}_{risque.id}_{compteur}")
        if st.form_submit_button("Ajouter l'action", type="primary"):
            if not description or not responsable:
                st.error("Renseignez l'action et au moins un responsable.")
            else:
                store.add_action(risque.id, description, responsable, echeance, statut)
                st.session_state[f"{prefixe}_n"] = compteur + 1
                annoncer(f"Action ajoutée au risque {risque.id}.")
                st.rerun()


def editeur_actions(risque: Risk, prefixe: str) -> None:
    for action in risque.actions:
        retard = " · en retard" if action.en_retard else ""
        with st.expander(f"{action.description} ({action.statut}{retard})"):
            with st.form(f"{prefixe}_a{action.id}"):
                description, responsable, echeance, statut = _champs_action(f"{prefixe}_a{action.id}", action)
                if st.form_submit_button("Enregistrer l'action", type="primary"):
                    if not description or not responsable:
                        st.error("Renseignez l'action et au moins un responsable.")
                    else:
                        store.update_action(action.id, description=description, responsable=responsable, echeance=echeance, statut=statut)
                        annoncer("Action enregistrée.")
                        st.rerun()
            if st.button("Supprimer cette action", key=f"{prefixe}_del{action.id}"):
                store.delete_action(action.id)
                annoncer("Action supprimée.")
                st.rerun()
    st.markdown("**Nouvelle action**")
    formulaire_ajout_action(risque, f"{prefixe}_new")


def editeur_identite(risque: Risk, prefixe: str) -> None:
    def index(liste, valeur):
        return liste.index(valeur) if valeur in liste else 0

    with st.form(f"{prefixe}_{risque.id}_identite"):
        titre = st.text_input("Titre du risque", value=risque.titre)
        c1, c2, c3 = st.columns(3)
        processus = c1.selectbox("Processus", config.PROCESSUS, index=index(config.PROCESSUS, risque.processus))
        categorie = c2.selectbox("Catégorie", config.CATEGORIES, index=index(config.CATEGORIES, risque.categorie))
        jour = c3.date_input("Date d'identification", value=risque.date_identification, format="DD/MM/YYYY")
        cause = st.text_area("Cause / description", value=risque.cause, height=80)
        effet = st.text_area("Effet", value=risque.effet, height=80)
        if st.form_submit_button("Enregistrer les modifications", type="primary"):
            if not all(v.strip() for v in (titre, cause, effet)):
                st.error("Le titre, la cause et l'effet sont obligatoires.")
            else:
                store.update_identity(risque.id, titre.strip(), processus, categorie, cause.strip(), effet.strip(), jour)
                annoncer(f"Risque {risque.id} modifié.")
                st.rerun()


def zone_suppression(risque: Risk, prefixe: str) -> None:
    confirme = st.checkbox(f"Confirmer la suppression définitive de {risque.id}", key=f"{prefixe}_{risque.id}_conf")
    if st.button("Supprimer le risque", key=f"{prefixe}_{risque.id}_del", disabled=not confirme):
        store.delete_risk(risque.id)
        annoncer(f"Risque {risque.id} supprimé.")
        st.rerun()


@st.dialog("Fiche risque", width="large")
def fiche_risque(risk_id: str) -> None:
    risque = store.get_risk(risk_id)
    if risque is None:
        st.warning("Ce risque n'existe plus.")
        return
    maitrise = '<span class="badge good">Maîtrisé</span>' if risque.maitrise else ""
    st.markdown(
        f'<div class="rk-id">{risque.id} · {escape(risque.processus)} · {escape(risque.categorie)}</div>'
        f'<div class="rk-title">{escape(risque.titre)}</div>'
        f'<div style="margin:.35rem 0 .2rem">{badge(risque.niveau)} {maitrise}</div>',
        unsafe_allow_html=True,
    )
    cotation, reevaluation, actions, identite = st.tabs(["Cotation", "Réévaluation", "Actions", "Identification"])
    with cotation:
        editeur_cotation(risque, "dlg_cot", rappel=False)
    with reevaluation:
        editeur_reevaluation(risque, "dlg_res")
    with actions:
        editeur_actions(risque, "dlg_act")
    with identite:
        editeur_identite(risque, "dlg_id")
        zone_suppression(risque, "dlg_sup")


@st.dialog("Ajouter un risque", width="large")
def dialogue_ajout() -> None:
    formulaire_risque("dlg_add")


def formulaire_risque(prefixe: str) -> None:
    """Saisie complète d'un risque. La cotation et l'action sont facultatives."""
    coter = st.toggle("Coter ce risque dès maintenant", key=f"{prefixe}_coter", value=True)
    compteur = st.session_state.get(f"{prefixe}_n", 0)
    with st.form(f"{prefixe}_{compteur}"):
        titre = st.text_input("Titre du risque *")
        c1, c2, c3 = st.columns(3)
        processus = c1.selectbox("Processus *", config.PROCESSUS)
        categorie = c2.selectbox("Catégorie *", config.CATEGORIES)
        jour = c3.date_input("Date d'identification *", value=date.today(), format="DD/MM/YYYY")
        cause = st.text_area("Cause / description *", height=78)
        effet = st.text_area("Effet *", height=78)
        g = o = d = None
        if coter:
            c1, c2, c3 = st.columns(3)
            g = c1.slider("Gravité (G)", 1, 10, 5)
            o = c2.slider("Occurrence (O)", 1, 10, 5)
            d = c3.slider("Détection (D)", 1, 10, 5)
        st.markdown("**Action proposée** (facultatif)")
        description = st.text_input("Action corrective")
        c1, c2, c3 = st.columns([2, 1, 1])
        responsables = c1.multiselect("Responsable", config.RESPONSABLES, placeholder="Choisir")
        echeance = c2.date_input("Échéance", value=date.today(), format="DD/MM/YYYY")
        statut = c3.selectbox("Statut", config.STATUTS)

        if st.form_submit_button("Ajouter le risque", type="primary"):
            erreurs = []
            if not all(v.strip() for v in (titre, cause, effet)):
                erreurs.append("Le titre, la cause et l'effet sont obligatoires.")
            if description.strip() and not responsables:
                erreurs.append("Choisissez un responsable pour l'action.")
            if erreurs:
                for erreur in erreurs:
                    st.error(erreur)
            else:
                actions = (
                    [{"description": description.strip(), "responsable": " / ".join(responsables), "echeance": echeance, "statut": statut}]
                    if description.strip()
                    else []
                )
                nouveau = store.add_risk(
                    {
                        "titre": titre.strip(), "processus": processus, "categorie": categorie, "cause": cause.strip(),
                        "effet": effet.strip(), "date_identification": jour, "gravite": g, "occurrence": o, "detection": d,
                        "actions": actions,
                    }
                )
                st.session_state[f"{prefixe}_n"] = compteur + 1
                annoncer(f"Risque {nouveau} ajouté.")
                st.rerun()

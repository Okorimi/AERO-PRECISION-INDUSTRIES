"""Point d'entrée Streamlit : contrôle d'accès, navigation et barre latérale."""
from __future__ import annotations

from html import escape

import streamlit as st

from aero import auth, config, store, ui
from aero.config import ROOT
from views import actions, dashboard, evaluation, identification, landing, matrice, referentiels, registre, suivi

st.set_page_config(
    page_title=config.APP_NAME,
    page_icon=str(ROOT / "assets" / "logo.svg"),
    layout="wide",
    initial_sidebar_state="expanded",
)
st.html(ROOT / "aero" / "style.css")


@st.cache_resource
def _initialiser_base() -> bool:
    store.ensure_ready()
    return True


_initialiser_base()
auth.restaurer_session()
auth.appliquer_cookie()


def _charger_demo(scenario: str) -> None:
    store.load_scenario(scenario)
    conserves = {k: st.session_state[k] for k in ("authentifie", "utilisateur") if k in st.session_state}
    st.session_state.clear()
    st.session_state.update(conserves)
    ui.annoncer("Données de démonstration réinitialisées.")


def _bouton_menu() -> None:
    """Trois barres en haut à gauche : le menu s'ouvre au survol, au clic ou au toucher."""
    st.markdown(
        '<div class="burger" tabindex="0" role="button" aria-label="Ouvrir le menu"><i></i><i></i><i></i></div>',
        unsafe_allow_html=True,
    )


def _profil() -> None:
    with st.container(key="profil"):
        with st.popover("Profil", icon=":material/account_circle:"):
            st.markdown(f"Connecté : **{escape(st.session_state.get('utilisateur', ''))}**")
            if st.button("Se déconnecter", width="stretch", icon=":material/logout:", key="deconnexion"):
                auth.deconnecter()
                st.rerun()


def _barre_laterale() -> None:
    with st.sidebar:
        st.download_button(
            "Exporter en CSV",
            data=store.export_csv(store.list_risks()),
            file_name="risques_amdec_aero_precision.csv",
            mime="text/csv",
            width="stretch",
            icon=":material/download:",
        )
        with st.popover("Données de démo", width="stretch", icon=":material/restart_alt:"):
            with st.container(key="demo_pop"):
                scenarios = list(config.SCENARIOS)
                choix = st.radio(
                    "Jeu de données",
                    scenarios,
                    index=scenarios.index(store.scenario()),
                    format_func=config.SCENARIOS.get,
                )
                st.caption("Toutes les modifications en cours seront remplacées.")
                if st.button("Réinitialiser les données de démo", type="primary", width="stretch"):
                    _charger_demo(choix)
                    st.rerun()


if not auth.connecte():
    page = st.navigation([st.Page(landing.render, title="Accueil", url_path="accueil", default=True)], position="hidden")
    page.run()
    st.stop()

st.logo(str(ROOT / "assets" / "logo.svg"), size="large")
page = st.navigation(
    {
        "Pilotage": [
            st.Page(dashboard.render, title="Tableau de bord", url_path="tableau-de-bord", icon=":material/space_dashboard:", default=True),
        ],
        "Processus ISO 31000 - ISO 31010": [
            st.Page(identification.render, title="Identification", url_path="identification", icon=":material/search:"),
            st.Page(evaluation.render, title="Évaluation", url_path="evaluation", icon=":material/tune:"),
            st.Page(matrice.render, title="Matrice de criticité", url_path="matrice", icon=":material/grid_on:"),
            st.Page(actions.render, title="Actions", url_path="actions", icon=":material/task_alt:"),
            st.Page(suivi.render, title="Suivi avant / après", url_path="suivi", icon=":material/trending_down:"),
        ],
        "Analyse et cadre": [
            st.Page(registre.render, title="Registre 2023-2026", url_path="registre", icon=":material/analytics:"),
            st.Page(referentiels.render, title="Référentiels", url_path="referentiels", icon=":material/menu_book:"),
        ],
    }
)
_bouton_menu()
_barre_laterale()
_profil()
ui.afficher_annonce()
page.run()

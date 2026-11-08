from __future__ import annotations

from html import escape

import streamlit as st

from aero import art, auth, config


@st.dialog("Connexion")
def _connexion() -> None:
    with st.form("connexion", border=False):
        utilisateur = st.text_input("Identifiant", autocomplete="username")
        mot_de_passe = st.text_input("Mot de passe", type="password", autocomplete="current-password")
        souvenir = st.checkbox("Se souvenir de moi", help="Reste connecté 30 jours sur ce navigateur.")
        if st.form_submit_button("Valider la connexion", type="primary", width="stretch"):
            if auth.verifier(utilisateur, mot_de_passe):
                auth.connecter(utilisateur, souvenir)
                st.rerun()
            else:
                st.error("Identifiant ou mot de passe incorrect.")


def _source_fond() -> str:
    for extension in ("jpg", "jpeg", "png", "webp"):
        if (config.ROOT / "static" / f"fond_accueil.{extension}").exists():
            return f"app/static/fond_accueil.{extension}"
    return config.FOND_ACCUEIL_URL


def render() -> None:
    st.markdown(
        "<style>[data-testid='stSidebar'],[data-testid='stSidebarCollapsedControl']{display:none}</style>"
        f'<img class="bg-landing" src="{escape(_source_fond())}" alt="" referrerpolicy="no-referrer" '
        f'style="opacity:{config.OPACITE_FOND_ACCUEIL}">',
        unsafe_allow_html=True,
    )
    with st.container(key="landing"):
        st.markdown(
            f"""<div class="hero">
            <div class="halo"><img src="{art.data_uri(art.turbine_svg())}" alt="Soufflante de turboréacteur"></div>
            <h1>{config.APP_NAME}</h1>
            <p>{config.WELCOME}</p>
            </div>""",
            unsafe_allow_html=True,
        )
        st.write("")
        if st.button("Se connecter", key="cta_login"):
            _connexion()

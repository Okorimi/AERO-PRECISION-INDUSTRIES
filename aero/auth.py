"""Connexion de démonstration et option « Se souvenir de moi »."""
from __future__ import annotations

import base64
import hashlib
import hmac
import time

import streamlit as st

from . import config, store

COOKIE = "aero_session"
DUREE_SECONDES = 30 * 24 * 3600


def _reglages() -> dict:
    try:
        return dict(st.secrets.get("auth", {}))
    except Exception:  # Aucun fichier secrets.toml : on reste sur la démonstration.
        return {}


def identifiants() -> tuple[str, str]:
    r = _reglages()
    return str(r.get("username", config.DEMO_USERNAME)), str(r.get("password", config.DEMO_PASSWORD))


def verifier(utilisateur: str, mot_de_passe: str) -> bool:
    attendu_u, attendu_p = identifiants()
    # L'évaluation est complète et à temps constant, quel que soit le champ erroné.
    ok_u = hmac.compare_digest(utilisateur.strip().encode(), attendu_u.encode())
    ok_p = hmac.compare_digest(mot_de_passe.encode(), attendu_p.encode())
    return ok_u and ok_p


def _signature(message: str) -> str:
    # Le mot de passe entre dans la clé : le modifier invalide les sessions mémorisées.
    secret = str(_reglages().get("cookie_secret") or store.secret_local())
    cle = hmac.new(secret.encode(), identifiants()[1].encode(), hashlib.sha256).digest()
    return hmac.new(cle, message.encode(), hashlib.sha256).hexdigest()


def creer_jeton(utilisateur: str, maintenant: float | None = None) -> str:
    expiration = int((maintenant if maintenant is not None else time.time()) + DUREE_SECONDES)
    nom = base64.urlsafe_b64encode(utilisateur.encode()).decode().rstrip("=")
    message = f"{nom}.{expiration}"
    return f"{message}.{_signature(message)}"


def verifier_jeton(jeton: str | None, maintenant: float | None = None) -> str | None:
    """Renvoie l'utilisateur si le jeton est intact, non expiré et toujours autorisé."""
    if not jeton or jeton.count(".") != 2:
        return None
    nom, expiration, signature = jeton.split(".")
    if not hmac.compare_digest(signature, _signature(f"{nom}.{expiration}")):
        return None
    if not expiration.isdigit() or int(expiration) < (maintenant if maintenant is not None else time.time()):
        return None
    try:
        utilisateur = base64.urlsafe_b64decode(nom + "=" * (-len(nom) % 4)).decode()
    except ValueError:
        return None
    return utilisateur if utilisateur == identifiants()[0] else None


def connecte() -> bool:
    return bool(st.session_state.get("authentifie"))


def connecter(utilisateur: str, souvenir: bool = False) -> None:
    st.session_state["authentifie"] = True
    st.session_state["utilisateur"] = utilisateur.strip()
    st.session_state.pop("_deconnecte", None)
    if souvenir:
        st.session_state["_cookie"] = creer_jeton(utilisateur.strip())


def deconnecter() -> None:
    st.session_state.clear()
    # Les cookies lus par Streamlit restent ceux de l'ouverture de la session :
    # ce repère empêche une reconnexion automatique juste après la déconnexion.
    st.session_state["_deconnecte"] = True
    st.session_state["_cookie"] = ""


def restaurer_session() -> None:
    if connecte() or st.session_state.get("_deconnecte"):
        return
    try:
        jeton = st.context.cookies.get(COOKIE)
    except Exception:
        return
    utilisateur = verifier_jeton(jeton)
    if utilisateur:
        connecter(utilisateur)


def appliquer_cookie() -> None:
    """Pose ou efface le cookie dans le navigateur, seul endroit où cela est possible."""
    valeur = st.session_state.pop("_cookie", None)
    if valeur is None:
        return
    duree = DUREE_SECONDES if valeur else 0
    with st.container(key="cookie_js"):
        st.html(
            f"""<script>
            document.cookie = "{COOKIE}={valeur}; Max-Age={duree}; Path=/; SameSite=Lax"
              + (location.protocol === "https:" ? "; Secure" : "");
            </script>""",
            unsafe_allow_javascript=True,
        )

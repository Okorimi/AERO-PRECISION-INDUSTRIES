from __future__ import annotations

from html import escape

import pandas as pd
import streamlit as st

from aero import charts, registry, ui
from aero.registry import format_mad
from aero.ui import fr


@st.cache_data(show_spinner="Nettoyage du registre…")
def _charger(contenu: bytes):
    return registry.charger(contenu)


def _memoriser_fichier() -> None:
    # Le fichier est conservé en session : il reste actif quand on change de page.
    televerse = st.session_state.get("reg_upload")
    if televerse is not None:
        st.session_state["reg_fichier"] = (televerse.name, televerse.getvalue())


def _source() -> tuple[pd.DataFrame, registry.Rapport, str, bool] | None:
    fichier = st.session_state.get("reg_fichier")
    if fichier is not None:
        nom, contenu = fichier
        try:
            df, rapport = _charger(contenu)
            return df, rapport, nom, False
        except registry.RegistreInvalide as erreur:
            st.session_state.pop("reg_fichier")
            st.error(f"{nom} n'est pas exploitable. {erreur} Le registre par défaut reste affiché.")
    chemin, simule = registry.source_par_defaut()
    if not chemin.exists():
        st.error("Aucun registre trouvé. Importez un fichier CSV ci-dessous.")
        return None
    try:
        df, rapport = _charger(chemin.read_bytes())
    except registry.RegistreInvalide as erreur:
        st.error(f"Le fichier {chemin.name} n'est pas exploitable. {erreur}")
        return None
    return df, rapport, chemin.name, simule


def _filtres(df: pd.DataFrame) -> pd.DataFrame:
    with ui.carte("rg_filtres"):
        c1, c2, c3, c4 = st.columns([1.4, 1, 1, 1])
        mini, maxi = df["date_identification"].min().date(), df["date_identification"].max().date()
        periode = c1.date_input("Période", value=(mini, maxi), min_value=mini, max_value=maxi, format="DD/MM/YYYY", key="rg_date")
        sites = c2.multiselect("Site", sorted(df["site"].unique()), placeholder="Tous", key="rg_site")
        categories = c3.multiselect("Catégorie", sorted(df["categorie_risque"].unique()), placeholder="Toutes", key="rg_cat")
        techniques = c4.multiselect("Technique ISO 31010", sorted(df["technique_ISO31010"].unique()), placeholder="Toutes", key="rg_tech")
    resultat = df
    if isinstance(periode, tuple) and len(periode) == 2:
        debut, fin = pd.Timestamp(periode[0]), pd.Timestamp(periode[1])
        resultat = resultat[resultat["date_identification"].between(debut, fin)]
    if sites:
        resultat = resultat[resultat["site"].isin(sites)]
    if categories:
        resultat = resultat[resultat["categorie_risque"].isin(categories)]
    if techniques:
        resultat = resultat[resultat["technique_ISO31010"].isin(techniques)]
    return resultat


def _graphique(figure, cle: str) -> None:
    st.plotly_chart(figure, width="stretch", config=charts.CONFIG, key=cle)


def _onglet_tendances(df: pd.DataFrame) -> None:
    gauche, droite = st.columns(2, gap="medium")
    with gauche, ui.carte("rg_trend", "Criticité moyenne par trimestre"):
        _graphique(charts.tendance_criticite(df), "rg_c1")
    with droite, ui.carte("rg_vol", "Risques identifiés par trimestre"):
        _graphique(charts.volume_trimestre(df), "rg_c2")
    st.write("")
    with ui.carte("rg_pareto", "Pareto", "Quels postes concentrent l'essentiel du risque ?"):
        c1, c2 = st.columns(2)
        dimension = c1.selectbox("Analyser par", ["processus", "categorie_risque", "site"], format_func=lambda v: {"processus": "Processus", "categorie_risque": "Catégorie", "site": "Site"}[v], key="rg_pd")
        mesure = c2.selectbox("Mesure", ["RPN", "criticite_inherente", "impact_financier_reel_mad"], format_func=lambda v: {"RPN": "NPR (RPN) cumulé", "criticite_inherente": "Criticité inhérente cumulée", "impact_financier_reel_mad": "Pertes réelles (MAD)"}[v], key="rg_pm")
        table = registry.pareto(df, dimension, mesure)
        if table[mesure].sum() == 0:
            st.info("Aucune valeur à analyser sur cette sélection.")
        else:
            _graphique(charts.pareto_chart(table, dimension, mesure), "rg_c3")


def _onglet_matrices(df: pd.DataFrame) -> None:
    gauche, droite = st.columns(2, gap="medium")
    with gauche, ui.carte("rg_m1", "Inhérente : nombre de risques", "Gravité × probabilité avant traitement."):
        _graphique(charts.heatmap_gp(df), "rg_c4")
    with droite, ui.carte("rg_m2", "Résiduelle : criticité moyenne", "Par case d'origine, après traitement."):
        _graphique(charts.heatmap_gp(df, "criticite_residuelle"), "rg_c5")
    st.write("")
    with ui.carte("rg_m3", "Passage des niveaux inhérents aux niveaux résiduels"):
        _graphique(charts.niveaux_flux(registry.niveau_croise(df)), "rg_c6")


def _onglet_cartographie(df: pd.DataFrame) -> None:
    with ui.carte("rg_map", "Cartographie par clause EN 9100 et processus"):
        _graphique(charts.clause_criticite(df), "rg_c7")
    st.write("")
    gauche, droite = st.columns(2, gap="medium")
    with gauche, ui.carte("rg_cat", "Répartition par catégorie"):
        _graphique(charts.repartition(df, "categorie_risque"), "rg_c8")
    with droite, ui.carte("rg_tech", "Techniques ISO 31010 utilisées"):
        _graphique(charts.repartition(df, "technique_ISO31010"), "rg_c9")


def _onglet_traitements(df: pd.DataFrame) -> None:
    gauche, droite = st.columns(2, gap="medium")
    with gauche, ui.carte("rg_e1", "Efficacité par option de traitement ISO 31000", "Actions dont l'efficacité est renseignée."):
        _graphique(charts.efficacite(df, "option_traitement_ISO31000"), "rg_c10")
    with droite, ui.carte("rg_e2", "Efficacité par technique"):
        _graphique(charts.efficacite(df, "technique_ISO31010"), "rg_c11")
    st.write("")
    gauche, droite = st.columns(2, gap="medium")
    colonnes = ["id_risque", "processus", "risque", "proprietaire_risque", "criticite_residuelle", "seuil_appetence"]
    with gauche, ui.carte("rg_s1", f"Au-dessus du seuil d'appétence ({int(df['au_dessus_seuil'].sum())})"):
        st.dataframe(df[df["au_dessus_seuil"]].sort_values("criticite_residuelle", ascending=False)[colonnes], hide_index=True, width="stretch", height=320)
    colonnes = ["id_risque", "processus", "action_maitrise", "proprietaire_risque", "statut_action"]
    with droite, ui.carte("rg_s2", f"Actions en retard ({int(df['action_en_retard'].sum())})"):
        st.dataframe(df[df["action_en_retard"]][colonnes], hide_index=True, width="stretch", height=320)


def _court(valeur: float) -> str:
    return format_mad(valeur).replace(" MAD", "")


def _onglet_finance(df: pd.DataFrame) -> None:
    k = registry.indicateurs(df)
    ratio = k["pertes"] / k["cout"] if k["cout"] else 0
    ui.grille_kpi(
        [
            ("Coût des actions (MAD)", _court(k["cout"]), "Budget engagé", ""),
            ("Pertes réelles (MAD)", _court(k["pertes"]), f"{k['materialises']} risques matérialisés", "crit"),
            ("Ratio pertes / coûts", fr(ratio, 2), "Sous 1, le préventif dépasse les pertes", ""),
            ("Perte moyenne (MAD)", _court(k["pertes"] / k["materialises"]) if k["materialises"] else "0", "Par risque matérialisé", ""),
        ]
    )
    with ui.carte("rg_fin", "Coût des actions et pertes réelles par catégorie"):
        _graphique(charts.cout_pertes(df), "rg_c12")


def _onglet_donnees(df: pd.DataFrame, rapport: registry.Rapport) -> None:
    with ui.carte("rg_q", "Exploration et nettoyage"):
        lignes = pd.DataFrame(
            [
                ("Lignes lues dans le fichier", rapport.lignes_lues),
                ("Doublons exacts supprimés", rapport.doublons_exacts),
                ("Identifiants en double supprimés", rapport.doublons_id),
                ("Lignes écartées (date ou criticité absente)", rapport.lignes_invalides),
                ("Criticités résiduelles complétées par l'inhérente", rapport.residuels_completes),
                ("Écarts de contrôle RPN ≠ G × P × D", rapport.ecarts_rpn),
                ("Écarts de contrôle criticité ≠ G × P", rapport.ecarts_criticite),
                ("Lignes conservées", rapport.lignes_finales),
            ],
            columns=["Contrôle", "Résultat"],
        )
        st.dataframe(lignes, hide_index=True, width="stretch")
        if rapport.valeurs_manquantes:
            manques = ", ".join(f"{c} ({n})" for c, n in rapport.valeurs_manquantes.items())
            st.caption(f"Valeurs vides avant traitement : {manques}.")
    st.write("")
    with ui.carte("rg_d", f"Données filtrées ({len(df)} lignes)"):
        internes = ["statut_normalise", "annee", "trimestre", "reduction_points", "au_dessus_seuil", "action_en_retard", "realisee_en_retard"]
        visibles = df.drop(columns=internes)
        st.dataframe(visibles, hide_index=True, width="stretch", height=380)
        st.download_button(
            "Télécharger la sélection (CSV)",
            visibles.to_csv(index=False, sep=";").encode("utf-8-sig"),
            "registre_filtre.csv",
            "text/csv",
            icon=":material/download:",
        )


def _onglet_conclusion(df: pd.DataFrame, simule: bool) -> None:
    note = "Texte recalculé selon vos filtres." + (" Il décrit des données simulées et ne doit pas être présenté comme un résultat réel." if simule else "")
    with ui.carte("rg_cc", "Conclusion et recommandations", note):
        st.markdown(
            "".join(f'<div class="reco"><b>{escape(t)}</b><div>{escape(x)}</div></div>' for t, x in registry.conclusions(df)),
            unsafe_allow_html=True,
        )


def render() -> None:
    ui.en_tete("Registre des risques 2023-2026", "Analyse par processus EN 9100, techniques ISO 31010 et traitements ISO 31000.")
    source = _source()
    if source is None:
        st.file_uploader("Importer le registre CSV", type="csv", key="reg_upload", on_change=_memoriser_fichier)
        return
    donnees, rapport, nom, simule = source

    if simule:
        st.markdown(
            '<div class="simu"><b>Données simulées.</b> Le fichier guihini_abakar_youssouf.csv n\'est pas encore présent. '
            "Importez-le ci-dessous ou placez-le dans le dossier data/.</div>",
            unsafe_allow_html=True,
        )
    with st.expander(f"Source : {nom}", icon=":material/upload_file:", expanded=False):
        st.file_uploader("Importer un autre registre CSV", type="csv", key="reg_upload", on_change=_memoriser_fichier)
        if "reg_fichier" in st.session_state and st.button("Revenir au fichier par défaut", key="reg_reset"):
            del st.session_state["reg_fichier"]
            st.rerun()

    df = _filtres(donnees)
    if df.empty:
        st.info("Aucun risque sur cette sélection. Élargissez les filtres.")
        return

    st.write("")
    k = registry.indicateurs(df)
    ui.grille_kpi(
        [
            ("Risques au registre", str(k["total"]), f"{df['processus'].nunique()} processus EN 9100", ""),
            ("Criticité moyenne", f"{fr(k['criticite_inherente'], 1)} → {fr(k['criticite_residuelle'], 1)}", f"Réduction de {fr(k['reduction_pct'])} %", "ok"),
            ("Au-delà du seuil", str(k["au_dessus_seuil"]), "Résiduelle > seuil d'appétence", "crit"),
            ("Actions en retard", str(k["actions_retard"]), f"Efficacité moyenne {fr(k['efficacite'])} %", ""),
        ]
    )

    onglets = st.tabs(["Tendances et Pareto", "Matrices", "Cartographie", "Traitements", "Coûts et pertes", "Conclusion", "Données"])
    with onglets[0]:
        _onglet_tendances(df)
    with onglets[1]:
        _onglet_matrices(df)
    with onglets[2]:
        _onglet_cartographie(df)
    with onglets[3]:
        _onglet_traitements(df)
    with onglets[4]:
        _onglet_finance(df)
    with onglets[5]:
        _onglet_conclusion(df, simule)
    with onglets[6]:
        _onglet_donnees(df, rapport)

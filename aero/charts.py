"""Graphiques Plotly. Un seul axe par graphique, marques fines, infobulles systématiques."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from . import config, scoring
from .store import Risk

AVANT = "#3558A8"
APRES = "#12A594"
NEUTRE = "#7C8DA8"
FONT = "Inter, Segoe UI, sans-serif"
DISPLAY = "Space Grotesk, Segoe UI, sans-serif"

CONFIG = {"displayModeBar": False, "responsive": True}


def _style(fig: go.Figure, hauteur: int = 320, legende: bool = False, marges: dict | None = None) -> go.Figure:
    fig.update_layout(
        height=hauteur,
        margin=marges or dict(l=8, r=12, t=8, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, size=12, color=config.INK),
        hoverlabel=dict(bgcolor="#FFFFFF", bordercolor=config.LINE, font=dict(family=FONT, size=12, color=config.INK)),
        showlegend=legende,
        legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0, title_text=""),
        transition=dict(duration=350, easing="cubic-in-out"),
        separators=", ",
        bargap=0.42,
        bargroupgap=0.08,
    )
    fig.update_xaxes(showgrid=False, linecolor=config.LINE, tickfont=dict(color=config.STEEL), automargin=True, zeroline=False)
    fig.update_yaxes(gridcolor="#EDF0F8", linecolor="rgba(0,0,0,0)", tickfont=dict(color=config.STEEL), automargin=True, zeroline=False)
    return fig


def donut_niveaux(risques: list[Risk]) -> go.Figure:
    comptes = pd.Series([r.niveau for r in risques if r.evalue]).value_counts()
    niveaux = [n for n in config.NIVEAUX if comptes.get(n, 0)]
    valeurs = [int(comptes[n]) for n in niveaux]
    fig = go.Figure(
        go.Pie(
            labels=niveaux,
            values=valeurs,
            hole=0.68,
            sort=False,
            direction="clockwise",
            marker=dict(colors=[config.COULEURS_NIVEAU[n] for n in niveaux], line=dict(color="#FFFFFF", width=3)),
            texttemplate="%{label}<br>%{value}",
            textposition="outside",
            hovertemplate="<b>%{label}</b><br>%{value} risque(s), %{percent}<extra></extra>",
        )
    )
    fig.add_annotation(text=f"<b>{sum(valeurs)}</b>", showarrow=False, font=dict(family=DISPLAY, size=32, color=config.INK), y=0.54)
    fig.add_annotation(text="risques évalués", showarrow=False, font=dict(size=11, color=config.STEEL), y=0.41)
    return _style(fig, 300, marges=dict(l=30, r=30, t=26, b=26))


def bar_npr_processus(risques: list[Risk]) -> go.Figure:
    df = pd.DataFrame([{"p": r.processus, "npr": r.npr} for r in risques if r.evalue])
    table = df.groupby("p")["npr"].agg(["mean", "size"]).sort_values("mean")
    fig = go.Figure(
        go.Bar(
            y=table.index,
            x=table["mean"],
            orientation="h",
            marker=dict(color=AVANT, cornerradius=4),
            text=[f"{v:.0f}" for v in table["mean"]],
            textposition="outside",
            cliponaxis=False,
            customdata=table["size"],
            hovertemplate="<b>%{y}</b><br>NPR moyen : %{x:.1f}<br>%{customdata} risque(s)<extra></extra>",
        )
    )
    fig.update_xaxes(title_text="NPR moyen", title_font=dict(size=11, color=config.STEEL), rangemode="tozero", showgrid=True, gridcolor="#EDF0F8")
    fig.update_yaxes(gridcolor="rgba(0,0,0,0)")
    return _style(fig, max(230, 70 + 46 * len(table)))


def avant_apres(risques: list[Risk]) -> go.Figure:
    evalues = [r for r in risques if r.evalue]
    ids = [r.id for r in evalues]
    fig = go.Figure()
    fig.add_bar(
        x=ids, y=[r.npr for r in evalues], name="NPR avant actions", marker=dict(color=AVANT, cornerradius=4),
        customdata=[r.titre for r in evalues], hovertemplate="<b>%{x}</b> %{customdata}<br>NPR : %{y}<extra></extra>",
    )
    fig.add_bar(
        x=ids, y=[r.npr_res for r in evalues], name="NPR' après actions", marker=dict(color=APRES, cornerradius=4),
        customdata=[r.titre for r in evalues], hovertemplate="<b>%{x}</b> %{customdata}<br>NPR' : %{y}<extra></extra>",
    )
    trait = dict(color=config.STEEL, width=1, dash="dot")
    fig.add_hline(y=100, line=trait)
    fig.add_scatter(x=[None], y=[None], mode="lines", line=trait, name="Seuil de maîtrise (100)", hoverinfo="skip")
    fig.update_layout(barmode="group", bargap=0.34)
    fig.update_yaxes(title_text="NPR", title_font=dict(size=11, color=config.STEEL), rangemode="tozero")
    fig.update_xaxes(type="category")
    return _style(fig, 330, legende=True, marges=dict(l=8, r=12, t=34, b=8))


def matrice(risques: list[Risk], residuel: bool = False) -> go.Figure:
    zones = {"Faible": 0, "Modéré": 1, "Élevé": 2, "Critique": 3}
    z = [[zones[scoring.zone_matrice(g, o)] for o in range(1, 6)] for g in range(1, 6)]
    echelle = [
        [0.0, config.TEINTES_NIVEAU["Faible"]], [0.25, config.TEINTES_NIVEAU["Faible"]],
        [0.25, "#FDF0A6"], [0.5, "#FDF0A6"],
        [0.5, "#FED7AA"], [0.75, "#FED7AA"],
        [0.75, "#FCA5A5"], [1.0, "#FCA5A5"],
    ]
    fig = go.Figure(
        go.Heatmap(
            x=[1, 2, 3, 4, 5], y=[1, 2, 3, 4, 5], z=z, zmin=-0.5, zmax=3.5, colorscale=echelle,
            showscale=False, xgap=4, ygap=4, hoverinfo="skip",
        )
    )

    cases: dict[tuple[int, int], list[Risk]] = {}
    for r in risques:
        g, o = (r.g_res, r.o_res) if residuel else (r.gravite, r.occurrence)
        if g is None or o is None:
            continue
        cases.setdefault((scoring.niveau5(g), scoring.niveau5(o)), []).append(r)

    xs, ys, textes, couleurs, donnees = [], [], [], [], []
    for (g5, o5), contenu in cases.items():
        for i, r in enumerate(contenu):
            colonnes = min(len(contenu), 3)
            ligne, colonne = divmod(i, 3)
            lignes_total = (len(contenu) - 1) // 3 + 1
            xs.append(o5 + (colonne - (colonnes - 1) / 2) * 0.29)
            ys.append(g5 - (ligne - (lignes_total - 1) / 2) * 0.3)
            textes.append(r.id)
            npr = r.npr_res if residuel else r.npr
            niveau = r.niveau_res if residuel else r.niveau
            couleurs.append(config.COULEURS_NIVEAU[niveau])
            g, o, d = (r.g_res, r.o_res, r.d_res) if residuel else (r.gravite, r.occurrence, r.detection)
            donnees.append([r.id, r.titre, g, o, d, npr, niveau])

    if xs:
        fig.add_trace(
            go.Scatter(
                x=xs, y=ys, mode="markers+text", text=textes, textposition="middle center",
                textfont=dict(family=DISPLAY, size=10, color=config.INK),
                marker=dict(size=31, color="#FFFFFF", line=dict(color=couleurs, width=3)),
                customdata=donnees,
                hovertemplate="<b>%{customdata[0]} · %{customdata[1]}</b><br>G %{customdata[2]} · O %{customdata[3]} · D %{customdata[4]}<br>NPR %{customdata[5]} (%{customdata[6]})<extra></extra>",
            )
        )
    fig.update_xaxes(title_text="Occurrence (1 à 5)", tickmode="array", tickvals=[1, 2, 3, 4, 5], range=[0.5, 5.5], showline=False, fixedrange=True)
    fig.update_yaxes(title_text="Gravité (1 à 5)", tickmode="array", tickvals=[1, 2, 3, 4, 5], range=[0.5, 5.5], showgrid=False, fixedrange=True)
    fig.update_layout(clickmode="event+select", dragmode=False)
    return _style(fig, 540)


def jauge_reduction(valeur: float) -> go.Figure:
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=valeur,
            number=dict(suffix=" %", font=dict(family=DISPLAY, size=40, color=config.INK), valueformat=".0f"),
            gauge=dict(
                axis=dict(range=[0, 100], tickcolor=config.LINE, tickfont=dict(color=config.STEEL, size=11)),
                bar=dict(color=APRES, thickness=0.42),
                bgcolor="#EEF1F8",
                borderwidth=0,
            ),
        )
    )
    return _style(fig, 250, marges=dict(l=26, r=26, t=26, b=6))


# Registre historique

def tendance_criticite(df: pd.DataFrame) -> go.Figure:
    table = df.groupby("trimestre")[["criticite_inherente", "criticite_residuelle"]].mean().sort_index()
    fig = go.Figure()
    for colonne, nom, couleur in (("criticite_inherente", "Inhérente", AVANT), ("criticite_residuelle", "Résiduelle", APRES)):
        fig.add_scatter(
            x=table.index, y=table[colonne], name=nom, mode="lines+markers", line=dict(color=couleur, width=2),
            marker=dict(size=8, line=dict(color="#FFFFFF", width=2)), hovertemplate=f"{nom} : %{{y:.1f}}<extra></extra>",
        )
    fig.update_layout(hovermode="x unified")
    fig.update_yaxes(title_text="Criticité moyenne", title_font=dict(size=11, color=config.STEEL), rangemode="tozero")
    return _style(fig, 320, legende=True, marges=dict(l=8, r=12, t=34, b=8))


def volume_trimestre(df: pd.DataFrame) -> go.Figure:
    table = df.groupby("trimestre").size().sort_index()
    fig = go.Figure(go.Bar(x=table.index, y=table.values, marker=dict(color=NEUTRE, cornerradius=4), hovertemplate="%{x}<br>%{y} risques identifiés<extra></extra>"))
    fig.update_yaxes(title_text="Risques identifiés", title_font=dict(size=11, color=config.STEEL), rangemode="tozero")
    return _style(fig, 320)


def repartition(df: pd.DataFrame, colonne: str, hauteur_ligne: int = 30) -> go.Figure:
    table = df[colonne].value_counts().sort_values()
    fig = go.Figure(
        go.Bar(
            y=table.index, x=table.values, orientation="h", marker=dict(color=AVANT, cornerradius=4), text=table.values,
            textposition="outside", cliponaxis=False, hovertemplate="<b>%{y}</b><br>%{x} risques<extra></extra>",
        )
    )
    fig.update_yaxes(gridcolor="rgba(0,0,0,0)", type="category")
    fig.update_xaxes(rangemode="tozero")
    return _style(fig, max(220, 60 + hauteur_ligne * len(table)))


def pareto_chart(table: pd.DataFrame, dimension: str, mesure: str) -> go.Figure:
    """Les barres et le cumul sont en pourcentage : ils partagent le même axe."""
    fig = go.Figure()
    fig.add_bar(
        x=table[dimension], y=table["part"], name="Part du total", marker=dict(color=AVANT, cornerradius=4),
        customdata=table[mesure], hovertemplate="<b>%{x}</b><br>Part : %{y:.1f} %<br>Cumul " + mesure + " : %{customdata:,.0f}<extra></extra>",
    )
    fig.add_scatter(
        x=table[dimension], y=table["cumul"], name="Cumul", mode="lines+markers", line=dict(color=APRES, width=2),
        marker=dict(size=8, line=dict(color="#FFFFFF", width=2)), hovertemplate="Cumul : %{y:.1f} %<extra></extra>",
    )
    fig.add_hline(y=80, line=dict(color=config.STEEL, width=1, dash="dot"), annotation_text="80 %", annotation_position="top left", annotation_font=dict(size=11, color=config.STEEL))
    fig.update_yaxes(range=[0, 105], ticksuffix=" %")
    fig.update_xaxes(tickangle=-30, type="category")
    return _style(fig, 430, legende=True, marges=dict(l=8, r=12, t=34, b=8))


def heatmap_gp(df: pd.DataFrame, valeur: str | None = None) -> go.Figure:
    plage = list(range(1, max(5, int(df["gravite"].max()), int(df["probabilite"].max())) + 1))
    if valeur is None:
        pivot = df.pivot_table(index="gravite", columns="probabilite", values="id_risque", aggfunc="count")
        bleu, format_txt, libelle = "Blues", ".0f", "Risques"
    else:
        pivot = df.pivot_table(index="gravite", columns="probabilite", values=valeur, aggfunc="mean")
        bleu, format_txt, libelle = "Teal", ".1f", "Criticité résiduelle moyenne"
    pivot = pivot.reindex(index=plage, columns=plage)
    fig = go.Figure(
        go.Heatmap(
            x=plage, y=plage, z=pivot.values, colorscale=bleu, xgap=3, ygap=3, hoverongaps=False,
            texttemplate=f"%{{z:{format_txt}}}", showscale=False,
            hovertemplate="Gravité %{y} · Probabilité %{x}<br>" + libelle + " : %{z:" + format_txt + "}<extra></extra>",
        )
    )
    fig.update_xaxes(title_text="Probabilité", tickvals=plage, showline=False)
    fig.update_yaxes(title_text="Gravité", tickvals=plage, showgrid=False)
    return _style(fig, 390)


def clause_criticite(df: pd.DataFrame) -> go.Figure:
    table = (
        df.groupby(["clause_EN9100", "processus"], as_index=False)
        .agg(inh=("criticite_inherente", "mean"), res=("criticite_residuelle", "mean"), n=("id_risque", "size"))
        .sort_values("inh")
    )
    libelles = "§" + table["clause_EN9100"].astype(str) + " " + table["processus"].astype(str)
    fig = go.Figure()
    fig.add_bar(y=libelles, x=table["res"], name="Résiduelle", orientation="h", marker=dict(color=APRES, cornerradius=3), hovertemplate="%{y}<br>Résiduelle : %{x:.1f}<extra></extra>")
    fig.add_bar(y=libelles, x=table["inh"], name="Inhérente", orientation="h", marker=dict(color=AVANT, cornerradius=3), hovertemplate="%{y}<br>Inhérente : %{x:.1f}<extra></extra>")
    fig.update_layout(barmode="group", bargap=0.26, legend_traceorder="reversed")
    fig.update_yaxes(gridcolor="rgba(0,0,0,0)", type="category")
    fig.update_xaxes(title_text="Criticité moyenne", title_font=dict(size=11, color=config.STEEL), rangemode="tozero", showgrid=True, gridcolor="#EDF0F8")
    return _style(fig, max(320, 60 + 44 * len(table)), legende=True, marges=dict(l=8, r=12, t=34, b=8))


def niveaux_flux(table: pd.DataFrame) -> go.Figure:
    fig = go.Figure(
        go.Heatmap(
            x=list(table.columns), y=list(table.index), z=table.values, colorscale="Blues", xgap=3, ygap=3,
            texttemplate="%{z}", showscale=False,
            hovertemplate="Inhérent %{y} → résiduel %{x}<br>%{z} risques<extra></extra>",
        )
    )
    fig.update_xaxes(title_text="Niveau résiduel", side="bottom", showline=False, type="category")
    fig.update_yaxes(title_text="Niveau inhérent", showgrid=False, type="category")
    return _style(fig, 390)


def efficacite(df: pd.DataFrame, colonne: str) -> go.Figure:
    sous = df[df["efficacite_action_pct"].gt(0)]
    table = sous.groupby(colonne)["efficacite_action_pct"].mean().sort_values()
    fig = go.Figure(
        go.Bar(
            y=table.index, x=table.values, orientation="h", marker=dict(color=APRES, cornerradius=4),
            text=[f"{v:.0f} %" for v in table.values], textposition="outside", cliponaxis=False,
            hovertemplate="<b>%{y}</b><br>Efficacité moyenne : %{x:.1f} %<extra></extra>",
        )
    )
    fig.update_xaxes(range=[0, 105], ticksuffix=" %", showgrid=True, gridcolor="#EDF0F8")
    fig.update_yaxes(gridcolor="rgba(0,0,0,0)", type="category")
    return _style(fig, max(220, 60 + 34 * len(table)))


def cout_pertes(df: pd.DataFrame) -> go.Figure:
    table = df.groupby("categorie_risque")[["cout_action_mad", "impact_financier_reel_mad"]].sum()
    table = table.sort_values("cout_action_mad", ascending=False)
    fig = go.Figure()
    fig.add_bar(x=table.index, y=table["cout_action_mad"], name="Coût des actions", marker=dict(color=AVANT, cornerradius=4), hovertemplate="%{x}<br>Coût : %{y:,.0f} MAD<extra></extra>")
    fig.add_bar(x=table.index, y=table["impact_financier_reel_mad"], name="Pertes réelles", marker=dict(color="#D9822B", cornerradius=4), hovertemplate="%{x}<br>Pertes : %{y:,.0f} MAD<extra></extra>")
    fig.update_layout(barmode="group", bargap=0.3)
    fig.update_yaxes(title_text="MAD", title_font=dict(size=11, color=config.STEEL), rangemode="tozero")
    fig.update_xaxes(tickangle=-30, type="category")
    return _style(fig, 420, legende=True, marges=dict(l=8, r=12, t=34, b=8))

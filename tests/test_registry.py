import pytest

from aero import registry


@pytest.fixture
def contenu():
    return registry.FICHIER_SIMULE.read_bytes()


def test_nettoyage_doublons(contenu):
    df, rapport = registry.charger(contenu)
    assert rapport.doublons_exacts + rapport.doublons_id == 6 and len(df) == 640 and df["id_risque"].is_unique
    assert not df["site"].str.contains("  ").any() and "Casablanca" in set(df["site"])


def test_csv_francais_desordonne(contenu):
    df, _ = registry.charger(contenu)
    brut = registry.lire_csv(contenu).drop_duplicates(subset="id_risque")
    brut["date_identification"] = df["date_identification"].dt.strftime("%d/%m/%Y").values
    brut["cout_action_mad"] = brut["cout_action_mad"].str.replace(".", ",", regex=False)
    brut = brut.rename(columns={"categorie_risque": "Catégorie Risque"})
    autre, _ = registry.charger(brut.to_csv(index=False, sep=";").encode("cp1252", "replace"))
    assert len(autre) == 640
    assert (autre["date_identification"].values == df["date_identification"].values).all()
    assert autre["cout_action_mad"].sum() == pytest.approx(df["cout_action_mad"].sum())


def test_colonnes_manquantes(contenu):
    brut = registry.lire_csv(contenu).drop(columns=["RPN"])
    with pytest.raises(registry.RegistreInvalide, match="RPN"):
        registry.nettoyer(brut)


def test_indicateurs_et_pareto(contenu):
    df, _ = registry.charger(contenu)
    k = registry.indicateurs(df)
    assert k["criticite_residuelle"] < k["criticite_inherente"]
    p = registry.pareto(df, "processus")
    assert p["cumul"].iloc[-1] == pytest.approx(100)
    assert registry.conclusions(df)


def test_actions_retard_sans_echeance(contenu):
    # Dans le sujet, l'échéance est vide tant que l'action n'est pas terminée.
    df, _ = registry.charger(contenu)
    retard = df[df["statut_normalise"] == "En retard"]
    assert retard["date_echeance"].isna().all() and retard["action_en_retard"].all()

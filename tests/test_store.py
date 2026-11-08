from datetime import date

import pytest

from aero import config, store


@pytest.fixture(autouse=True)
def base(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "t.db")
    store.ensure_ready()


def test_kpi_initiaux():
    r = store.list_risks()
    assert len(r) == 5
    assert sum(x.npr >= 200 for x in r) == 3
    assert sum(x.maitrise for x in r) == 0
    assert sum(x.npr for x in r) / 5 == pytest.approx(213.4)


def test_passage_en_maitrise():
    r = store.get_risk("R01")
    assert not r.maitrise
    store.update_action(r.actions[0].id, statut="Terminé")
    r = store.get_risk("R01")
    assert r.maitrise and r.npr_res == 48 and r.delta == 152
    store.set_residuel("R01", 8, 5, 5)
    assert not store.get_risk("R01").maitrise


@pytest.mark.parametrize("scenario", [config.SCENARIO_CAS, config.SCENARIO_ETENDU])
def test_reduction_globale_et_niveaux(scenario):
    store.load_scenario(scenario)
    risques = store.list_risks()
    assert all(r.niveau_res in ("Modéré", "Faible") for r in risques)
    moyenne = sum(r.reduction for r in risques) / len(risques)
    cumul = (1 - sum(r.npr_res for r in risques) / sum(r.npr for r in risques)) * 100
    assert 70 <= moyenne <= 80 and 70 <= cumul <= 80


def test_migration_conserve_les_saisies():
    store.load_scenario(config.SCENARIO_CAS)
    with store._db() as conn:
        conn.execute("UPDATE risks SET g_res = NULL, o_res = NULL, d_res = NULL WHERE id != 'R01'")
        conn.execute("UPDATE risks SET g_res = 8, o_res = 4, d_res = 4 WHERE id = 'R01'")
        conn.execute("UPDATE meta SET valeur = '1' WHERE cle = 'revision_demo'")
    store.ensure_ready()
    assert store.get_risk("R01").npr_res == 128
    assert store.get_risk("R02").npr_res == 48


def test_identifiant_jamais_reutilise():
    nouveau = {"titre": "T", "processus": "Qualité", "categorie": "Qualité", "cause": "C", "effet": "E", "date_identification": date.today()}
    premier = store.add_risk(nouveau)
    store.delete_risk(premier)
    assert store.add_risk(nouveau) != premier


def test_suppression_en_cascade():
    store.delete_risk("R01")
    assert all(a.risk_id != "R01" for _, a in store.all_actions(store.list_risks()))


def test_portefeuille_etendu():
    store.load_scenario(config.SCENARIO_ETENDU)
    r = store.list_risks()
    assert len(r) == 12 and all(x.reevalue for x in r)
    assert sum(a.en_retard for _, a in store.all_actions(r)) == 1
    assert sum(x.maitrise for x in r) == 6


def test_export_csv():
    contenu = store.export_csv(store.list_risks()).decode("utf-8-sig")
    assert "NPR résiduel" in contenu and len(contenu.strip().splitlines()) == 6


def test_jeton_souvenir():
    from aero import auth

    jeton = auth.creer_jeton("youssouf_aero", maintenant=1000)
    assert auth.verifier_jeton(jeton, maintenant=2000) == "youssouf_aero"
    assert auth.verifier_jeton(jeton, maintenant=1000 + auth.DUREE_SECONDES + 1) is None
    assert auth.verifier_jeton(jeton[:-1] + ("0" if jeton[-1] != "0" else "1"), maintenant=2000) is None
    assert auth.verifier_jeton(auth.creer_jeton("intrus", maintenant=1000), maintenant=2000) is None
    assert auth.verifier_jeton("n'importe quoi") is None

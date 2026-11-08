import pytest

from aero import scoring


@pytest.mark.parametrize("g,o,d,attendu", [(8, 5, 5, 200), (8, 4, 5, 160), (7, 6, 7, 294), (7, 4, 8, 224), (9, 3, 7, 189)])
def test_npr_etude_de_cas(g, o, d, attendu):
    assert scoring.calc_npr(g, o, d) == attendu


@pytest.mark.parametrize("npr,niveau", [(1, "Faible"), (49, "Faible"), (50, "Modéré"), (99, "Modéré"), (100, "Élevé"), (199, "Élevé"), (200, "Critique"), (1000, "Critique")])
def test_seuils(npr, niveau):
    assert scoring.niveau_npr(npr) == niveau


def test_note_hors_echelle():
    with pytest.raises(ValueError):
        scoring.calc_npr(11, 1, 1)


@pytest.mark.parametrize("v,attendu", [(1, 1), (2, 1), (3, 2), (9, 5), (10, 5)])
def test_echelle_cinq(v, attendu):
    assert scoring.niveau5(v) == attendu


def test_maitrise():
    assert scoring.est_maitrise(["Terminé"], 99)
    assert not scoring.est_maitrise(["Terminé"], 100)
    assert not scoring.est_maitrise(["Terminé", "En cours"], 40)
    assert not scoring.est_maitrise([], 40)
    assert not scoring.est_maitrise(["Terminé"], None)

import pytest
from streamlit.testing.v1 import AppTest

from aero import config

APP = str(config.ROOT / "app.py")


@pytest.fixture(autouse=True)
def base(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "t.db")
    import streamlit as st
    st.cache_resource.clear()


def test_accueil():
    at = AppTest.from_file(APP, default_timeout=60).run()
    assert not at.exception
    assert [b.label for b in at.button] == ["Se connecter"]
    assert any("bg-landing" in m.value for m in at.markdown)


def test_tableau_de_bord():
    at = AppTest.from_file(APP, default_timeout=60)
    at.session_state["authentifie"] = True
    at.session_state["utilisateur"] = "test"
    at.run()
    assert not at.exception
    assert any('class="val">213<' in m.value for m in at.markdown)
    assert not any("<h1>AERO PRECISION" in m.value for m in at.markdown)

"""Keep every test away from Luke's real dashboard state (archive and folders)."""

import pytest


@pytest.fixture(autouse=True)
def private_dashboard_state(tmp_path, monkeypatch):
    monkeypatch.setenv("GPP_ARCHIVE", str(tmp_path / "archive.json"))
    monkeypatch.setenv("GPP_GROUPS", str(tmp_path / "groups.json"))

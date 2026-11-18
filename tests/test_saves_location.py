"""Where the save database lives: the user-data folder in the packaged build, the
cwd-relative `databases/` from source (ADR 0003)."""

import sys
from pathlib import Path

import pytest

import pygamine
from app.game import Game
from pygamine import user_data_dir
from util.paths import packaged_databases_dir


def test_from_source_there_is_no_packaged_folder(monkeypatch):
    monkeypatch.delattr(sys, "_MEIPASS", raising=False)
    assert packaged_databases_dir() is None


def test_frozen_database_goes_to_the_user_data_folder(monkeypatch):
    monkeypatch.setattr(sys, "_MEIPASS", str(Path.cwd()), raising=False)
    assert packaged_databases_dir() == user_data_dir("highrise") / "databases"
    assert packaged_databases_dir().parts[-3:] == (
        "VectorViolet",
        "highrise",
        "databases",
    )


@pytest.fixture
def quiet_game(monkeypatch):
    monkeypatch.setattr(pygamine.Application, "run", lambda self: None)
    monkeypatch.setattr(Game, "show_splash", lambda self: None)


def test_frozen_game_stores_in_the_user_data_folder(monkeypatch, tmp_path, quiet_game):
    for variable in ("APPDATA", "XDG_DATA_HOME"):
        monkeypatch.setenv(variable, str(tmp_path / "appdata"))
    for variable in ("HOME", "USERPROFILE"):
        monkeypatch.setenv(variable, str(tmp_path / "home"))
    monkeypatch.setattr(sys, "_MEIPASS", str(Path.cwd()), raising=False)
    game = Game()
    expected = packaged_databases_dir()
    assert expected is not None
    assert game.database.directory == expected
    assert tmp_path in expected.parents  # never the real user folder in tests
    game.init_database()
    assert (expected / "database.db").exists()


def test_source_game_keeps_the_default_folder(monkeypatch, tmp_path, quiet_game):
    monkeypatch.delattr(sys, "_MEIPASS", raising=False)
    game = Game()  # conftest's saves_in_tmp moved Database's default into tmp_path
    assert game.database.directory == tmp_path / "databases"

"""Background music. config/assets.yaml declares the `bg` sound (Sakura Girl -
Day Off): a real Game() plays it from run() and shows the music volume
control. Music is optional in the engine, so a Game() built from a manifest
with `bg` left out boots and runs cleanly, plays no music and hides the
control that would control nothing."""

from __future__ import annotations

import warnings
from pathlib import Path

import pygame
import pytest
import yaml

import pygamine
from app.game import MUSIC_KEY, MUSIC_VOLUME_OBJECTS, Game, format_volume, has_sound

MANIFEST = "config/assets.yaml"


@pytest.fixture(autouse=True)
def headless_run(monkeypatch) -> None:
    # The real window loop and splash don't apply headlessly; everything
    # else in run() does.
    monkeypatch.setattr(pygamine.Application, "run", lambda self: None)
    monkeypatch.setattr(Game, "show_splash", lambda self: None)


@pytest.fixture
def with_music() -> Game:
    return Game()


@pytest.fixture
def game(monkeypatch, tmp_path: Path) -> Game:
    """A Game loaded from the real manifest with the `bg` sound removed."""
    manifest = yaml.safe_load(Path(MANIFEST).read_text(encoding="utf-8"))
    del manifest["sounds"][MUSIC_KEY]
    trimmed = tmp_path / "assets.yaml"
    trimmed.write_text(yaml.safe_dump(manifest), encoding="utf-8")
    real_load = pygamine.AssetManager.load_manifest
    monkeypatch.setattr(
        pygamine.AssetManager,
        "load_manifest",
        lambda self, path: real_load(self, trimmed),
    )
    return Game()


def click(game: Game, button) -> None:
    game.mouse.position = button.rect.center
    for kind in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
        game.handle_audio_settings_events(
            pygame.event.Event(kind, button=1, pos=button.rect.center)
        )


def test_the_manifest_has_the_music_file(with_music):
    assert has_sound(with_music.assets, MUSIC_KEY)
    assert with_music.assets.validate() == []


def test_the_music_plays_and_its_volume_control_is_shown(with_music, monkeypatch):
    played = []
    monkeypatch.setattr(
        with_music.audio, "play_music", lambda *a, **k: played.append(a)
    )

    with_music.run()

    assert played == [(str(with_music.assets.sound_path(MUSIC_KEY)),)]
    panel = with_music.panel_manager["audio_settings"]
    assert all(panel[name].active for name in MUSIC_VOLUME_OBJECTS)


def test_clicking_the_music_buttons_changes_the_volume_and_its_label(with_music):
    with_music.run()
    with_music.open_panel("audio_settings")
    panel = with_music.panel_manager["audio_settings"]
    volume = with_music.audio.music_volume()

    click(with_music, panel["music_volume_minus_button"])
    lowered = with_music.audio.music_volume()
    assert lowered == pytest.approx(volume - 0.1)
    assert panel["music_volume_entry_text"].text == format_volume(lowered)

    click(with_music, panel["music_volume_plus_button"])
    assert with_music.audio.music_volume() == pytest.approx(volume)
    assert panel["music_volume_entry_text"].text == format_volume(volume)


def test_the_manifest_without_bg_has_no_music(game):
    assert not has_sound(game.assets, MUSIC_KEY)
    with pytest.raises(KeyError):
        game.assets.sound_path(MUSIC_KEY)
    assert game.assets.validate() == []


def test_the_game_runs_cleanly_and_plays_no_music(game, monkeypatch, capsys):
    played = []
    monkeypatch.setattr(game.audio, "play_music", lambda *a, **k: played.append(a))

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        game.run()
        for panel in ("menu", "audio_settings", "game"):
            game.open_panel(panel)
            game.update()
            game.draw()

    assert played == []
    assert capsys.readouterr().err == ""


def test_the_music_volume_control_is_hidden(game):
    game.run()
    panel = game.panel_manager["audio_settings"]

    assert all(not panel[name].active for name in MUSIC_VOLUME_OBJECTS)
    assert panel["sfx_volume_plus_button"].active


def test_clicks_where_the_hidden_music_buttons_sit_change_nothing(game):
    game.run()
    game.open_panel("audio_settings")
    button = game.panel_manager["audio_settings"]["music_volume_plus_button"]
    volume = game.audio.music_volume()

    click(game, button)

    assert game.audio.music_volume() == volume


def test_has_sound_finds_a_declared_sound(game):
    assert has_sound(game.assets, "click")

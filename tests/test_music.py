"""Background music. config/assets.yaml declares the `bg` sound (Sakura Girl -
Day Off): a real Game() plays it from run() and shows the music volume
control. Music is optional in the engine, so the same Game() with `bg` left
out boots and runs cleanly, plays no music and hides the control that would
control nothing."""

from __future__ import annotations

import warnings

import pygame
import pytest

import pygamine
from app.game import MUSIC_KEY, MUSIC_VOLUME_OBJECTS, Game, has_sound


@pytest.fixture
def with_music(monkeypatch) -> Game:
    # The real window loop and splash don't apply headlessly; everything
    # else in run() does.
    monkeypatch.setattr(pygamine.Application, "run", lambda self: None)
    monkeypatch.setattr(Game, "show_splash", lambda self: None)
    return Game()


@pytest.fixture
def game(monkeypatch) -> Game:
    """A Game whose manifest lacks `bg`."""
    monkeypatch.setattr(pygamine.Application, "run", lambda self: None)
    monkeypatch.setattr(Game, "show_splash", lambda self: None)
    monkeypatch.setattr(
        "app.game.has_sound",
        lambda assets, key: key != MUSIC_KEY and has_sound(assets, key),
    )
    return Game()


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


def test_stepping_the_music_volume_changes_the_music_volume(with_music):
    with_music.run()
    with_music.open_panel("audio_settings")
    volume = with_music.audio.music_volume()

    with_music._step_volume("music", -0.1)

    assert with_music.audio.music_volume() == pytest.approx(volume - 0.1)


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


def test_clicks_where_the_hidden_music_buttons_sit_change_nothing(game, monkeypatch):
    game.run()
    game.open_panel("audio_settings")
    button = game.panel_manager["audio_settings"]["music_volume_plus_button"]
    volume = game.audio.music_volume()
    monkeypatch.setattr(game.mouse, "position", button.rect.center, raising=False)

    for kind in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
        game.handle_audio_settings_events(
            pygame.event.Event(kind, button=1, pos=button.rect.center)
        )

    assert game.audio.music_volume() == volume


def test_has_sound_finds_a_declared_sound(game):
    assert has_sound(game.assets, "click")

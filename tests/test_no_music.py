"""The game without background music: config/assets.yaml has no `bg` sound
(the previous track was unlicensed and removed). A real Game() boots and runs
through run() cleanly -- no crash, no warnings, no missing asset -- plays no
music, and hides the music volume control that would control nothing."""
from __future__ import annotations

import warnings

import pygame
import pytest

import pygamine
from app.game import MUSIC_KEY, MUSIC_VOLUME_OBJECTS, Game


@pytest.fixture
def game(monkeypatch):
    # The real window loop and splash don't apply headlessly; everything
    # else in run() does.
    monkeypatch.setattr(pygamine.Application, "run", lambda self: None)
    monkeypatch.setattr(Game, "show_splash", lambda self: None)
    return Game()


def test_the_manifest_has_no_music(game):
    assert not Game.has_music_asset(game.assets)
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


def test_clicks_where_the_hidden_music_buttons_sit_change_nothing(game, monkeypatch):
    game.run()
    game.open_panel("audio_settings")
    button = game.panel_manager["audio_settings"]["music_volume_plus_button"]
    volume = game.audio.music_volume()
    monkeypatch.setattr(game.mouse, "position", button.rect.center, raising=False)

    for kind in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
        game.handle_audio_settings_events(pygame.event.Event(kind, button=1, pos=button.rect.center))

    assert game.audio.music_volume() == volume

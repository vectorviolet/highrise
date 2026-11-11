from collections.abc import Callable
from pathlib import Path
from random import choice

import pygame
import yaml

from app.game_events import GameEventsMixin
from app.game_persistence import (
    DEFAULT_MASTER_VOLUME,
    GamePersistenceMixin,
    GameSettings,
)
from domain.player import Player
from gameplay.buildings.building import Building, Buildings
from gameplay.clouds.cloud_container import OneShotCloudAnimation, LoopingCloudAnimation
from gameplay.tile_selector import TileSelector
from gameplay.tilemap import Tilemap
from pygamine import Application
from pygamine import clamp01
from pygamine import AssetManager
from pygamine import Database
from pygamine import PanelLoaderExt
from pygamine import PanelManager
from pygamine import SplashScreen, standard_splash_media
from pygamine import Transform
from pygamine import GameAudio
from pygamine import StateObject
from pygamine import (
    make_animated_factory,
    make_factory,
    make_scrolling_panel_factory,
    make_text_factory,
)
from pygamine import MenuController
from pygamine.util.localization import DEFAULT_LANGUAGE, localization, tr
from ui.cash_display import apply_cash_display
from ui.floating_text import FloatingTextConfig, FloatingTexts
from ui.info_panel import InfoPanel
from ui.money_format import format_money
from ui.odometer import Odometer
from ui.ui_scale import DEFAULT_UI_SCALE, UI_SCALES, step_ui_scale
from util.paths import LANG_FOLDER

# Manifest key of the background music. Optional: without it the game plays
# no music and hides the music volume control (it would control nothing --
# the splash plays before the saved volumes are applied).
MUSIC_KEY = "bg"
MUSIC_VOLUME_OBJECTS = (
    "music_volume_text",
    "music_volume_minus_button",
    "music_volume_plus_button",
    "music_volume_entry",
    "music_volume_entry_text",
    "music_volume_minus_icon",
    "music_volume_plus_icon",
    "audio_settings_panel",
)
# What sits below the music row on the AUDIO page: with no music it moves up
# into the music row's place, under the shorter panel.
BELOW_MUSIC_OBJECTS = (
    "sfx_volume_text",
    "sfx_volume_minus_button",
    "sfx_volume_plus_button",
    "sfx_volume_entry",
    "sfx_volume_entry_text",
    "sfx_volume_minus_icon",
    "sfx_volume_plus_icon",
    "cancel_button",
    "cancel_button_text",
    "save_button",
    "save_button_text",
)

# The game-panel objects that make up the info panel: children of its root.
INFO_PANEL_OBJECTS = (
    "info_panel",
    "level_text",
    "speed_text",
    "cooldown_text",
    "sell_price_text",
    "close_button",
    "sell_button",
    "sell_button_text",
    "info_panel_building_image",
)

# Escape (or the window's close request) on these panels goes back to the
# panel given; "menu", "audio_settings" and "game" are handled separately.
BACK_TARGETS = {
    "play": "menu",
    "settings": "menu",
    "display_settings": "settings",
    "game_settings": "settings",
    "credits": "menu",
}

# Localization keys (config/lang/*.yaml) of the window-mode labels.
WINDOW_MODE_KEYS = {
    "fullscreen": "display_settings.modes.fullscreen",
    "borderless": "display_settings.modes.borderless",
    "windowed": "display_settings.modes.windowed",
}


def has_sound(assets: AssetManager, key: str) -> bool:
    """Whether the asset manifest declares the sound `key`."""
    try:
        assets.sound_path(key)
    except KeyError:
        return False
    return True


def format_volume(volume: float) -> str:
    """A volume in [0, 1] as the settings label text, e.g. 0.5 -> "%50".
    Values outside [0, 1] are clamped first."""
    return "%" + str(round(clamp01(volume) * 100))


class Game(GameEventsMixin, GamePersistenceMixin, Application):
    def __init__(self) -> None:
        self.settings = yaml.safe_load(Path("config/settings.yaml").read_text())
        localization.load(LANG_FOLDER)
        window = self.settings["window"]
        gameplay = self.settings["gameplay"]
        audio = self.settings["audio"]
        ui = self.settings["ui"]

        self.cursor_size = tuple(ui["cursor_size"])
        self.odometer = Odometer(ui["cash_roll_ms"])
        self.shown_money = 0
        self.floating_text_config = FloatingTextConfig.from_dict(
            self.settings["floating_text"]
        )

        # Every panel position in config/panels.yaml is an absolute pixel
        # coordinate authored against this size -- set before super().__init__()
        # since on_canvas_resized() (see below) can fire during construction
        # (set_fullscreen() there triggers the first _rebuild_window_surface()).
        self._authored_size = tuple(window["size"])
        # on_canvas_resized() rebuilds the panels only once they exist.
        self._panels_built = False

        super().__init__(tuple(window["size"]), window["title"], window["fps"])

        self.assets = AssetManager()
        self.assets.load_manifest("config/assets.yaml")
        missing = self.assets.validate()
        if missing:
            raise RuntimeError("Missing assets:\n" + "\n".join(missing))

        self.tilemap: Tilemap | None = None
        self.window_transform = Transform((0, 0), self.size)
        self.panel_manager = PanelManager(ui["background_colors"])
        self.database = Database("database")

        self.buildings = Buildings(
            on_merge=self._on_buildings_merged, on_payout=self._on_building_payout
        )
        self.cloud_count = gameplay["cloud_count"]
        self.max_size = gameplay["max_map_size"]
        self.max_building_level = gameplay["max_building_level"]
        self.starting_money = gameplay["starting_money"]

        self.audio = GameAudio()
        self.player = Player()
        # The font of the coin's dollar sign and of the floating money text.
        self.money_font_path = str(self.assets.font_path("titillium_black"))
        self.floating_texts = FloatingTexts(
            self.floating_text_config, self.money_font_path
        )
        # The listener add_objects() registered last; replaced on every
        # rebuild so new games don't pile up listeners on the same player.
        self.money_listener: Callable[[int], None] | None = None
        self.default_music_volume = audio["default_music_volume"]
        self.default_sfx_volume = audio["default_sfx_volume"]
        self.old_master_volume = DEFAULT_MASTER_VOLUME
        self.old_music_volume = self.default_music_volume
        self.old_sfx_volume = self.default_sfx_volume

        self.background_music_sound_path = (
            self.assets.sound_path(MUSIC_KEY)
            if has_sound(self.assets, MUSIC_KEY)
            else None
        )
        self.click_sound_path = self.assets.sound_path("click")
        self.go_back_sound_path = self.assets.sound_path("back")
        self.merge_sound_path = self.assets.sound_path("merge")

        self.info_panel = InfoPanel(self.panel_manager)
        self.tile_selector = TileSelector(self.tilemap, self.mouse, self.buildings)
        self.cloud_animation = OneShotCloudAnimation(self.size)
        self.splash = SplashScreen(
            standard_splash_media(self.audio), skip_completely=True
        )

        self.handlers = {
            "menu": self.handle_menu_events,
            "play": self.handle_play_events,
            "settings": self.handle_settings_events,
            "display_settings": self.handle_display_settings_events,
            "audio_settings": self.handle_audio_settings_events,
            "game_settings": self.handle_game_settings_events,
            "credits": self.handle_credits_events,
            "game": self.handle_game_events,
        }
        self.menu_controllers: dict = {}

        # Saved in the database (the Game settings page); the real value is
        # loaded in run().
        self.skip_intro = False
        self.ui_scale = DEFAULT_UI_SCALE

    def on_canvas_resized(self, new_size: tuple[int, int]) -> None:
        # Every panel in config/panels.yaml is positioned with absolute pixel
        # coordinates authored against self._authored_size (1920x1080) -- the
        # old (pre dynamic-canvas) engine always rendered internally at that
        # fixed size and let _present() bitmap-stretch it onto whatever the
        # real window was, which is what gave the UI "free" scaling on
        # resize. The new engine instead makes self.window track the real
        # display exactly by default, so without this override the UI would
        # stay pinned at its authored pixel positions and visibly shrink
        # into a corner as the real window gets smaller.
        #
        # Recreate the old behavior with render_scale: keep self.window
        # pinned at >= self._authored_size on both axes (never smaller, so
        # nothing authored near the edges gets clipped) regardless of the
        # real window/display size, and let _present()'s existing
        # non-uniform pygame.transform.scale() do the same bitmap stretch
        # the old engine did. max(), not min(), so a non-16:9 pick (e.g. a
        # 16:10 resolution) only ever gains extra canvas on one axis rather
        # than losing it on the other.
        display_w, display_h = self.display_surface.get_size()
        target_scale = max(
            self._authored_size[0] / display_w, self._authored_size[1] / display_h
        )
        if abs(target_scale - self.render_scale) > 1e-9:
            self.set_render_scale(
                target_scale
            )  # re-enters this method with the corrected size
        elif self._panels_built and tuple(new_size) != tuple(
            self.window_transform.size
        ):
            # The panels were laid out against the old canvas (a 16:10 window has
            # more height than 16:9): lay them out again against this one.
            self.rebuild_panels()

    def run(self) -> None:
        # Application.run() would call this itself, but this project needs
        # menu/panel/audio setup interleaved between the splash and the
        # main loop, so it keeps its own run() override for that -- just
        # delegating the splash part instead of duplicating it.
        # The settings come first: the language applies before any panel is
        # built, and "skip intro" decides whether the splash runs at all.
        self.init_database()
        self._apply_settings(self.load_settings())
        if self.skip_intro:
            self.splash = None
        self.show_splash()
        self.mouse.set_cursor_visible(False)
        self.mouse.set_cursor_image(
            StateObject(
                pos=(0, 0),
                size=self.cursor_size,
                image_path=self.assets.image_path("cursor"),
            )
        )

        self.load_data()
        self.tile_selector.tilemap = self.tilemap
        self.add_objects()

        self._reset_session_ui()
        self.open_panel("menu")
        if self.background_music_sound_path is not None:
            self.audio.play_music(str(self.background_music_sound_path))

        self.watch_language()
        try:
            super().run()
        finally:
            self.unwatch_language()

    def _show_music_controls(self, shown: bool) -> None:
        panel = self.panel_manager["audio_settings"]
        for name in MUSIC_VOLUME_OBJECTS:
            panel[name].active = shown
        panel["audio_settings_panel_no_music"].active = not shown
        if not shown:
            step = panel["sfx_volume_text"].rect.y - panel["music_volume_text"].rect.y
            for name in BELOW_MUSIC_OBJECTS:
                panel[name].rect.y -= step

    def add_objects(self) -> None:
        """Builds everything: the game world, then the panels."""
        self.add_world_objects()
        self.build_panels()

    def rebuild_panels(self) -> None:
        """Rebuilds the panels at the current UI scale and canvas size and re-texts
        what the YAML cannot. The world (buildings, payouts, the tile selection)
        is not touched; an open info panel closes, since its widgets are new and
        empty."""
        self.build_panels()
        self.info_panel.close()
        self._refresh_ui_texts()

    def add_world_objects(self) -> None:
        """Puts the clouds, tiles and buildings in the game panel. The UI scale
        never reaches them."""
        self.panel_manager.add_object(
            "game", "clouds", LoopingCloudAnimation(self.cloud_count, self.size)
        )
        self.panel_manager.add_object("game", "tiles", self.tilemap)
        self.panel_manager.add_object("game", "buildings", self.buildings)

    def build_panels(self) -> None:
        """Loads config/panels.yaml into the panel manager and wires up what the
        YAML cannot: the info panel's parent, the menu controllers, the money text."""
        # The widgets about to be replaced must not stay children of the long-lived
        # info panel root.
        if "game" in self.panel_manager and "info_panel" in self.panel_manager["game"]:
            for name in INFO_PANEL_OBJECTS:
                self.panel_manager["game"][name].set_parent(None)

        # Panels are laid out against the canvas as it is now, not the one the
        # Game started with.
        self.window_transform.size = self.size
        loader = PanelLoaderExt(self.panel_manager, self.window_transform, self.assets)
        # The UI scale reaches every panel object (size, font size, offsets) through
        # the loader; the game world above is not loaded through it, so it stays put.
        loader.scale = self.ui_scale / 100
        # Positions in panels.yaml are authored against this canvas; on a taller or
        # wider one they scale about the authored center and are re-centered.
        loader.authored_size = self._authored_size
        loader.register("object", make_factory(self.assets), default=True)
        loader.register("text", make_text_factory(self.assets))
        loader.register("animated", make_animated_factory(self.assets))
        loader.register("scrolling_panel", make_scrolling_panel_factory(self.assets))
        loader.load("config/panels.yaml")
        self._show_music_controls(self.background_music_sound_path is not None)

        panel = self.panel_manager["game"]
        for name in INFO_PANEL_OBJECTS:
            panel[name].set_parent(self.info_panel.root)

        panel["selection_mode_button"].set_base_state(
            "on" if self.tile_selector.is_active else "off"
        )
        close_button = panel["close_button"]
        # The cross scales with the button and sits in the middle of it.
        for images, key in (
            (close_button.images, "cross_white"),
            (close_button._hover_images, "cross_grey"),
        ):
            image = self.assets.get_image(key)
            icon = pygame.transform.scale(
                image,
                (
                    round(image.get_width() * self.ui_scale / 100),
                    round(image.get_height() * self.ui_scale / 100),
                ),
            )
            button_image = images[None]
            button_image.blit(
                icon,
                (
                    (button_image.get_width() - icon.get_width()) // 2,
                    (button_image.get_height() - icon.get_height()) // 2,
                ),
            )

        switch_up = self.assets.sound_path("switch_up")
        switch_down = self.assets.sound_path("switch_down")
        menu_buttons = [
            self.panel_manager["menu"][n]
            for n in (
                "play_button",
                "settings_button",
                "credits_button",
                "exit_button",
            )
        ]
        play_buttons = [
            self.panel_manager["play"][n]
            for n in ("new_game_button", "continue_button", "play_back_button")
        ]
        settings_buttons = [
            self.panel_manager["settings"][n]
            for n in (
                "display_settings_button",
                "audio_settings_button",
                "game_settings_button",
                "settings_back_button",
            )
        ]
        self.menu_controllers = {
            "menu": MenuController(menu_buttons, self.audio, switch_up, switch_down),
            "play": MenuController(play_buttons, self.audio, switch_up, switch_down),
            "settings": MenuController(
                settings_buttons, self.audio, switch_up, switch_down
            ),
        }

        apply_cash_display(
            panel["money_panel"],
            panel["money_icon"],
            panel["money_text"],
            self.assets,
            self.money_font_path,
        )
        self.floating_texts.scale = self.ui_scale / 100
        money_text = panel["money_text"]
        if self.money_listener is not None:
            self.player.remove_money_listener(self.money_listener)
        # money_text is only the layout (its anchored rectangle, font and color): the
        # odometer owns the text and draws it, rolling.
        money_text.active = False
        money_text.set_text("0")
        gap = round(6 * self.ui_scale / 100)
        self.odometer.bind(
            money_text.rect,
            money_text.font,
            money_text.color,
            panel["money_panel"].rect,
            panel["money_icon"].rect.right + gap,
        )
        self.shown_money = self.player.money
        self.money_listener = self._on_money_changed
        self.player.add_money_listener(self.money_listener)
        self.odometer.snap(format_money(self.player.money))
        self._panels_built = True

    def _on_money_changed(self, money: int) -> None:
        direction = 1 if money > self.shown_money else -1
        self.odometer.set_target(
            format_money(money), direction, pygame.time.get_ticks()
        )
        self.shown_money = money

    @property
    def _tilemap(self) -> Tilemap:
        assert self.tilemap is not None, "tilemap not loaded yet"
        return self.tilemap

    def update_button_texts(self) -> None:
        panel = self.panel_manager["game"]
        tilemap = self._tilemap

        if tilemap.is_max_size():
            panel["expand_button_text"].set_text(tr("game.max_size"), state="hover")
        else:
            panel["expand_button_text"].set_text(
                format_money(tilemap.get_expand_cost()), state="hover"
            )

        if len(self.buildings) == tilemap.row_count * tilemap.column_count:
            panel["build_button_text"].set_text(tr("game.tiles_full"), state="hover")
        else:
            panel["build_button_text"].set_text(
                format_money(self.buildings.get_build_cost()), state="hover"
            )

        if self.buildings.age_number == self.buildings.max_age_number:
            panel["next_age_button_text"].set_text(tr("game.max_age"), state="hover")
        else:
            panel["next_age_button_text"].set_text(
                format_money(self.buildings.get_age_cost()), state="hover"
            )

    def handle_event(self, event: pygame.Event) -> None:
        super().handle_event(event)
        self.panel_manager.handle_event(event, self.mouse.position)

        if controller := self.menu_controllers.get(self.panel_manager.current_panel):
            controller.handle_event(event, self.mouse.position)
        if handler := self.handlers.get(self.panel_manager.current_panel):
            handler(event)

    def update(self) -> None:
        self.panel_manager.update()
        self.buildings.update()
        self.floating_texts.update(pygame.time.get_ticks())
        self._close_stale_info_panel()
        self.cloud_animation.update()

    def _close_stale_info_panel(self) -> None:
        # A finished merge replaces both buildings; don't keep showing (or
        # selling) one that's no longer on the board.
        if self.info_panel.is_active and self.info_panel.building not in self.buildings:
            self.info_panel.close()

    def _on_buildings_merged(self) -> None:
        self.audio.play_sfx(self.merge_sound_path)

    def draw(self) -> None:
        self.panel_manager.draw(self.window)
        if self.panel_manager.current_panel == "game":
            self.odometer.draw(self.window, pygame.time.get_ticks())
            # A panel open over the world (the info panel) is never covered by the
            # texts floating over the world.
            self.floating_texts.draw(
                self.window,
                pygame.time.get_ticks(),
                over_world=not self.info_panel.is_active,
            )
        self.cloud_animation.draw(self.window)
        super().draw()

    def on_exit_request(self) -> None:
        self.audio.play_sfx(self.go_back_sound_path)
        panel = self.panel_manager.current_panel

        if panel == "menu":
            self.exit()
        elif panel == "audio_settings":
            self._revert_audio_settings()
            self.open_panel("settings")
        elif panel == "game":
            if self.info_panel.is_active:
                self.info_panel.close()
            else:
                self.save_game()
                self.open_panel("menu")
        elif panel in BACK_TARGETS:
            self.open_panel(BACK_TARGETS[panel])

    # ── Game mechanics ────────────────────────────────────────────────────────

    def expand(self) -> None:
        tilemap = self._tilemap
        if tilemap.is_max_size() or not self._spend(tilemap.get_expand_cost()):
            return

        tilemap.expand()

        for building in self.buildings:
            building.tile = tilemap[building.tile.row_number - 1][
                building.tile.column_number - 1
            ]

        self.update_button_texts()
        self.audio.play_sfx(self.click_sound_path)

    def add_building(self, level, row_number, column_number) -> None:
        tilemap = self._tilemap
        new_building = self.buildings.create(
            level, tilemap[row_number - 1][column_number - 1]
        )
        self.buildings.append(new_building)
        self.buildings.sort_by_column()

        if (
            len(self.buildings) == tilemap.row_count * tilemap.column_count
            and "game" in self.panel_manager
            and "build_button_text" in self.panel_manager["game"]
        ):
            self.panel_manager["game"]["build_button_text"].set_text(
                tr("game.tiles_full"), state="hover"
            )

    def create_building(self) -> None:
        if not self.player.can_afford(self.buildings.get_build_cost()):
            return

        tilemap = self._tilemap
        all_tiles = {
            (r + 1, c + 1)
            for r in range(tilemap.row_count)
            for c in range(tilemap.column_count)
        }
        occupied = {(b.tile.row_number, b.tile.column_number) for b in self.buildings}
        empty_tiles = list(all_tiles - occupied)

        if empty_tiles:
            row_number, column_number = choice(empty_tiles)
            self.add_building(1, row_number, column_number)
            self._spend(self.buildings.get_build_cost())
            self.audio.play_sfx(self.click_sound_path)

    def set_age(self, age_number) -> None:
        if age_number <= self.buildings.max_age_number:
            self.buildings.set_age(age_number)
            self.update_button_texts()

    def next_age(self) -> None:
        if self.buildings.age_number >= self.buildings.max_age_number:
            return
        if not self._spend(self.buildings.get_age_cost()):
            return
        self.set_age(self.buildings.age_number + 1)
        self.audio.play_sfx(self.click_sound_path)

    def move_buildings(self, rotation: str) -> None:
        if self.tile_selector.is_active:
            return
        self.buildings.move(rotation, self._tilemap, self.max_building_level)

    def _on_building_payout(self, building: Building, amount: int) -> None:
        self.player.earn(amount)
        self.show_gain(building, amount)

    def show_gain(self, building: Building, amount: int) -> None:
        """A green "+amount" over `building`: a payout or a sale."""
        if amount > 0:
            self.floating_texts.gain(
                building.rect.midtop,
                amount,
                pygame.time.get_ticks(),
            )

    def _spend(self, amount: int) -> bool:
        """Pays `amount` if the player can afford it, and floats a red "-amount" down
        from the bottom of the digits, right-aligned with it (it may fall past
        the bottom of the screen). Returns whether it was paid."""
        if not self.player.spend(amount):
            return False
        if amount > 0:
            # The text's top starts at the bottom of the digits: the baseline.
            label = self.panel_manager["game"]["money_text"]
            self.floating_texts.spend(
                (label.rect.right, label.rect.top + label.font.get_ascent()),
                amount,
                pygame.time.get_ticks(),
            )
        return True

    def open_panel(self, tab: str) -> None:
        if tab == "exit":
            self.exit()
            return
        if tab == "credits":
            self.panel_manager["credits"][
                "credits_scroller"
            ].reset()  # restart the scroll
        self.panel_manager.open_panel(tab)
        self.cloud_animation.create_clouds()

    def new_game(self) -> None:
        self.delete_data()
        self.load_data()
        self.tile_selector.is_active = False
        self.add_objects()
        self._reset_session_ui()
        self.open_panel("game")

    def _reset_session_ui(self) -> None:
        """Brings the UI in line with a freshly loaded session: the age, a closed
        info panel, the toolbar hover texts and the settings labels."""
        self.floating_texts.clear()
        self.set_age(self.buildings.age_number)
        self.info_panel.close()
        self._refresh_ui_texts()

    def _refresh_ui_texts(self) -> None:
        """Re-texts what panels.yaml cannot: the toolbar hover texts and the
        labels the game sets from code. Touches nothing but texts."""
        self.odometer.snap(format_money(self.player.money))
        self.update_button_texts()
        self.set_master_label(self.audio.master_volume())
        self.set_music_label(self.audio.music_volume())
        self.set_sfx_label(self.audio.sfx_volume())
        self.set_window_size_label()
        self.set_window_mode_label()
        self.set_language_label()
        self.set_skip_intro_label()
        self.set_ui_scale_label()

    def has_save_data(self) -> bool:
        return len(self.buildings) > 0 or self.buildings.age_number > 0

    def play(self) -> None:
        if self.has_save_data():
            self.open_panel("play")
        else:
            self.new_game()

    # ── audio-settings UI labels (volume → "%NN" text on a panel widget) ──

    def set_master_label(self, volume: float) -> None:
        self.panel_manager["audio_settings"]["master_volume_entry_text"].set_text(
            format_volume(volume)
        )

    def set_music_label(self, volume: float) -> None:
        self.panel_manager["audio_settings"]["music_volume_entry_text"].set_text(
            format_volume(volume)
        )

    def set_sfx_label(self, volume: float) -> None:
        self.panel_manager["audio_settings"]["sfx_volume_entry_text"].set_text(
            format_volume(volume)
        )

    def set_window_size_label(self) -> None:
        w, h = self.resolution
        self.panel_manager["display_settings"]["window_size_entry_text"].set_text(
            f"{w}x{h}"
        )

    def set_window_mode_label(self) -> None:
        self.panel_manager["display_settings"]["window_mode_entry_text"].set_text(
            tr(WINDOW_MODE_KEYS[self._window_mode])
        )

    def set_ui_scale_label(self) -> None:
        self.panel_manager["display_settings"]["ui_scale_entry_text"].set_text(
            f"%{self.ui_scale}"
        )

    def set_ui_scale(self, ui_scale: int) -> None:
        """Saves a UI scale and applies it at once: the panels are rebuilt at the
        new scale and the panel that is open stays open."""
        if ui_scale not in UI_SCALES:
            raise ValueError(
                f"Unknown UI scale {ui_scale}; expected one of {UI_SCALES}"
            )
        if ui_scale == self.ui_scale:
            return
        self.save_ui_scale(ui_scale)
        self.ui_scale = ui_scale
        self.rebuild_panels()

    def step_ui_scale(self, delta: int) -> None:
        self.set_ui_scale(step_ui_scale(self.ui_scale, delta))

    # ── game settings: language and skip intro ──

    def _apply_settings(self, settings: GameSettings) -> None:
        """Applies the saved settings at launch; an unknown saved language
        (a language file removed since) falls back to English."""
        language = settings.language
        if language not in localization.languages():
            language = DEFAULT_LANGUAGE
        localization.set_language(language)
        self.skip_intro = settings.skip_intro
        self.ui_scale = settings.ui_scale
        self.audio.set_master_volume(settings.master_volume)

    def change_language(self, code: str) -> None:
        """Saves and applies a language at once, with no restart."""
        if code not in localization.languages():
            raise KeyError(f"Unknown language '{code}'")
        self.save_language(code)
        localization.set_language(code)

    def cycle_language(self, delta: int) -> None:
        codes = sorted(localization.languages())
        index = codes.index(localization.language)
        self.change_language(codes[(index + delta) % len(codes)])

    def set_skip_intro(self, skip_intro: bool) -> None:
        self.save_skip_intro(skip_intro)
        self.skip_intro = skip_intro
        self.set_skip_intro_label()

    def set_language_label(self) -> None:
        self.panel_manager["game_settings"]["language_entry_text"].set_text(
            localization.languages()[localization.language]
        )

    def set_skip_intro_label(self) -> None:
        key = "common.enabled" if self.skip_intro else "common.disabled"
        self.panel_manager["game_settings"]["skip_intro_entry_text"].set_text(tr(key))

    def watch_language(self) -> None:
        """Starts re-texting the code-built labels on a language change. Call
        once the panels exist; pair it with `unwatch_language()`, so a game that
        is over never reacts to the process-wide language again."""
        localization.on_language_changed(self._on_language_changed)

    def unwatch_language(self) -> None:
        localization.remove_language_changed(self._on_language_changed)

    def _on_language_changed(self, code: str) -> None:
        """Re-texts what panels.yaml cannot: the toolbar hover texts and the
        labels the game sets from code (the other labels follow their key). The cash
        amount and an open info panel's prices change their number format too."""
        self.odometer.snap(format_money(self.player.money))
        self.info_panel.relocalize()
        self.update_button_texts()
        self.set_window_mode_label()
        self.set_language_label()
        self.set_skip_intro_label()

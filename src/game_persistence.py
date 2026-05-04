from sound_manager import SoundManager
from tile import Tilemap


class GamePersistenceMixin:
    def load_data(self) -> None:
        self.init_database()
        self.load_game_data(self.get_game_data())
        self.load_buildings()

    def init_database(self) -> None:
        self.database.execute_safely("CREATE TABLE IF NOT EXISTS game(age_number INTEGER, size INTEGER, money INTEGER, music_volume INTEGER, sfx_volume INTEGER)")
        self.database.execute_safely("CREATE TABLE IF NOT EXISTS buildings(level INTEGER, row INTEGER, column INTEGER)")

    def get_game_data(self) -> list[tuple] | None:
        game_data = self.database.execute_safely("SELECT * FROM game", True)
        if game_data: return game_data

        self.database.execute_safely("INSERT INTO game(age_number, size, money, music_volume, sfx_volume) VALUES(?, ?, ?, ?, ?)",
                                     params=(0, 2, self.starting_money, self.default_music_volume, self.default_sfx_volume))
        return self.database.execute_safely("SELECT * FROM game", True)

    def load_game_data(self, game_data: list[tuple] | None) -> None:
        if not game_data: return

        age_number, size, self.money, music_volume, sfx_volume = game_data[0]
        self.set_music_volume(music_volume)
        self.set_sfx_volume(sfx_volume)
        self.tilemap = Tilemap(size, self.max_size)
        self.buildings.age_number = age_number

    def load_buildings(self) -> None:
        buildings = self.database.execute_safely("SELECT * FROM buildings", True)
        if buildings:
            for building in buildings:
                self.add_building(*building)

    def save_audio_settings(self) -> None:
        self.database.execute_safely("UPDATE game SET music_volume=?, sfx_volume=?",
                                     params=(SoundManager.get_volume(0), SoundManager.get_volume(1)))

    def save_game(self) -> None:
        self.database.execute_safely("UPDATE game SET age_number=?, size=?, money=?",
                                     params=(self.buildings.age_number, self.tilemap.row_count, self.money))
        self.database.execute_safely("DELETE FROM buildings")

        for building in self.buildings:
            self.database.execute_safely("INSERT INTO buildings(level, row, column) VALUES(?, ?, ?)",
                                         params=(building.level, building.tile.row_number, building.tile.column_number))

    def delete_data(self) -> None:
        self.database.execute_safely("DELETE FROM game")
        self.database.execute_safely("DELETE FROM buildings")
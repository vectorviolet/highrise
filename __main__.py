#!/usr/bin/env python3
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT / "src" / "pygame_core"))

from app.game import Game

if __name__ == "__main__":
    Game().run()

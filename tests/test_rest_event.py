# tests/test_rest_event.py

import sys
import importlib
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]              # …/It1_interfaces
PROJECT_ROOT = ROOT.parent                                      # …/CTD25
SERVER_DIR = ROOT / "server"
CLIENT_DIR = ROOT / "client"

for p in (SERVER_DIR, CLIENT_DIR, PROJECT_ROOT):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
sys.modules.setdefault("core", importlib.import_module("server.core"))


from pathlib import Path
PROJECT_ROOTT = Path(__file__).resolve().parents[2]  
pieces_dir   = PROJECT_ROOTT / "pieces"             



import time
import pytest
from pathlib import Path

from core.engine.Board         import Board
from core.pieces.PieceFactory   import PieceFactory
from core.engine.Command        import Command
from core.game.game            import Game
from core.engine.events         import StateChanged
from graphics.mock_img import MockImg      # ← NEW


CELL_PX = 64        


# -----------------------------------------------------------
#  Helpers
# -----------------------------------------------------------
def _make_minimal_game() -> Game:
    """לוח 8×8, רוק + מלך לבנים בלבד – מספיק כדי לרוץ בלי StopIteration."""
    board = Board(CELL_PX, CELL_PX, 8, 8, MockImg())
    factory = PieceFactory(board, pieces_dir)


    rook    = factory.create_piece("RW", (7, 0))
    w_king  = factory.create_piece("KW", (7, 4))
    b_king  = factory.create_piece("KB", (0, 4))
    game    = Game([rook, w_king, b_king], board)
    game.start()
    return game

# ---------- סימולציה ידנית ----------
def _drive_until(game: Game, ms: int, step: int = 50):
    start = game.game_time_ms()
    while game.game_time_ms() - start < ms:
        now = game.game_time_ms()
        for p in game.pieces:
            p.update(now)
        time.sleep(step / 1000)

# ---------- הטסט ----------
def test_move_generates_rest_and_idle():
    game  = _make_minimal_game()
    rook  = next(p for p in game.pieces if p.piece_id.startswith("RW"))

    events: list[StateChanged] = []
    game.bus.subscribe(StateChanged, events.append)

    # שליחת פקודת תזוזה
    now = game.game_time_ms()
    cmd = Command.create_move_command(rook.piece_id, (7, 0), (4, 0), now, "WHITE")
    rook.on_command(cmd, now, game)

    # מריצים ~7 שניות כדי לכסות move (2 s) + long_rest (3 s) + idle
    _drive_until(game, ms=7000)

    # מרוקנים את תור-האירועים → קוראים לכל המאזינים

    states = [e.new_state for e in events if e.piece_id == rook.piece_id]

    # אין אירוע 'move' - לכן לא בודקים אותו
    assert any(s.endswith("_rest") for s in states), "לא נוצר אירוע REST"
    assert states[-1] == "idle", "הכלי לא חזר ל-idle"
# tests/test_game/test_game.py

import pytest
from unittest.mock import MagicMock
from engine.Command import Command
from game.game import Game

# -------------------------
# Dummies to isolate logic
# -------------------------


class DummyPhysics:
    def __init__(self, cell):
        self.is_jumping = False
        self.start_time_ms = 0
        self._cell = cell

    def get_current_cell(self):
        return self._cell


class DummyPiece:
    def __init__(self, piece_id="P1", cell=(0, 0), color="WHITE"):
        self.piece_id = piece_id
        self._cell = cell
        self.commands = []
        self.is_captured = False
        self.color = color
        self.current_state = MagicMock()
        self.current_state.physics.get_current_cell.return_value = cell
        self.current_state.get_cell = lambda: cell
        self.can_jump_over_allies = False

    def reset(self, ms): pass
    def update(self, ms): pass
    def on_command(self, cmd, now, game): 
        self.commands.append(cmd)
        return True
    def get_cell(self): return self._cell

class DummyBoard:
    def __init__(self):
        self.H_cells = 8
        self.W_cells = 8
        self.img = MagicMock()
        self.background_img = None
    def clone(self): return self
    def get_cell_center_pixel(self, r, c): return (r * 64 + 32, c * 64 + 32)

class DummyBus:
    def __init__(self):
        self.published = []
    def publish(self, e): self.published.append(e)

@pytest.fixture
def game():
    p1 = DummyPiece("KW_7_4", (7, 4), "WHITE")
    p2 = DummyPiece("KB_0_4", (0, 4), "BLACK")
    pw = DummyPiece("PW_6_0", (6, 0), "WHITE")
    pb = DummyPiece("PB_1_7", (1, 7), "BLACK")
    board = DummyBoard()
    g = Game([p1, p2, pw, pb], board)
    g.bus = DummyBus()
    g.move_history = {"WHITE": [], "BLACK": []}
    g.game_start_ms = 10000
    return g

# -------------------------
# Core Tests
# -------------------------

def test_initialization(game):
    assert game.white_cursor == [7, 4]
    assert game.black_cursor == [0, 4]
    assert len(game.white_pieces) == 2
    assert len(game.black_pieces) == 2

def test_cursor_moves_within_bounds(game):
    game._move_cursor(game.white_cursor, -10, 20, "WHITE")
    assert game.white_cursor == [0, 7]
    game._move_cursor(game.black_cursor, 10, -5, "BLACK")
    assert game.black_cursor == [7, 0]

def test_process_input_selects_piece(game):
    game._process_input("WHITE", "ENTER")
    assert game.from_piece["WHITE"].piece_id == "KW_7_4"

def test_process_input_replaces_selected_piece(game):
    game._process_input("WHITE", "ENTER")
    game.white_cursor = [6, 0]  # PW_6_0
    game._process_input("WHITE", "ENTER")
    assert game.from_piece["WHITE"].piece_id == "PW_6_0"

def test_illegal_move_publishes_error(game):
    game._process_input("WHITE", "ENTER")
    game.white_cursor = [0, 0]  # empty
    game._process_input("WHITE", "ENTER")
    assert any(e.reason == "illegal move" for e in game.bus.published)

def test_jump_on_same_square(game):
    game._process_input("WHITE", "ENTER")
    game._process_input("WHITE", "ENTER")
    assert any("Jump" in str(cmd) for cmd in game.command_history)

def test_resolve_collision_marks_captured(game):
    white = DummyPiece("KW", (4, 4), "WHITE")
    black = DummyPiece("KB", (4, 4), "BLACK")

    white.current_state.physics = DummyPhysics((4, 4))
    black.current_state.physics = DummyPhysics((4, 4))
    white.current_state.physics.start_time_ms = 100
    black.current_state.physics.start_time_ms = 50

    game.pieces = [white, black]
    game.white_pieces = [white]
    game.black_pieces = [black]

    game._resolve_collisions()

    assert black.is_captured is True



def test_win_condition_detected(game):
    game.black_king.is_captured = True
    assert game._is_win() is False  # waits 2s
    game._win_timer_ms = game.game_time_ms() - 3000
    assert game._is_win() is True

def test_announce_draw(game):
    game.white_pieces.clear()
    game.black_pieces.clear()
    game._announce_win()
    assert True  # Just checking no crash

def test_announce_win_white(game):
    game.black_pieces.clear()
    game._announce_win()
    assert any("WHITE" in str(e) for e in game.bus.published)






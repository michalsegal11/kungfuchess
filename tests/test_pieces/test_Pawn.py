import pytest
from engine.Command import Command
from pieces.Pawn import Pawn
from pieces.Piece import Piece

# -------------------------------
# Dummy classes
# -------------------------------

class DummyMoveRule:
    def __init__(self, tag, dr, dc):
        self.tag = tag
        self.dr = dr
        self.dc = dc

class DummyPhysics:
    def __init__(self):
        self.cell = (1, 1)
        self.path = []
        self.board = self
        self.start_time_ms = 0
        self.is_moving = False
        self.current_command = None
    def get_current_cell(self): return self.cell
    def set_path(self, path): self.path = path
    def is_valid_cell(self, r, c): return 0 <= r < 8 and 0 <= c < 8
    def can_be_captured(self): return True

class DummyGraphics:
    def reset(self, *_): pass

class DummyMoves:
    rules = [
        DummyMoveRule("f", 1, 0),
        DummyMoveRule("ff", 2, 0),
        DummyMoveRule("x", 1, 1),
        DummyMoveRule("x", 1, -1),
    ]

class DummyState:
    def __init__(self):
        self.moves = DummyMoves()
        self.physics = DummyPhysics()
        self.graphics = DummyGraphics()
        self.cfg = {"can_be_captured": True}
        self.state_name = "idle"
        self.piece_id = "PW_1_1"
        self.transitions = {}

    def reset(self, *_): pass

    def get_state_after_command(self, cmd, now):
        self.start_move(cmd.params[1], now, cmd)
        return self

    def start_move(self, dest, now, cmd):
        self.physics.set_path([self.physics.get_current_cell(), dest])
        self.physics.start_time_ms = now
        self.physics.is_moving = True
        self.physics.current_command = cmd

# -------------------------------
# Fixtures
# -------------------------------

@pytest.fixture
def dummy_state():
    return DummyState()

@pytest.fixture
def pawn(dummy_state):
    return Pawn("PW_1_1", dummy_state, dummy_state.moves, forward=+1)

@pytest.fixture
def dummy_game(pawn):
    class DummyGame:
        def __init__(self):
            self.white_pieces = [pawn]
            self.black_pieces = []
            self.pieces = [pawn]
            self.called = []
            self._map = {}

        def _piece_at(self, r, c):
            return self._map.get((r, c), None)

        def set_piece_at(self, piece, pos):
            self._map[pos] = piece

        @property
        def bus(self): return self
        def publish(self, e): self.called.append(e)

    return DummyGame()

# -------------------------------
# Tests
# -------------------------------

def test_white_pawn_single_move(pawn, dummy_game):
    """White pawn moves forward one square."""
    cmd = Command.move(pawn.piece_id, (1, 1), (2, 1), player="WHITE", ts=1000)
    pawn.on_command(cmd, 1000, dummy_game)
    assert pawn.has_moved
    assert pawn.current_state.physics.path == [(1, 1), (2, 1)]

def test_white_pawn_illegal_double_step_blocked(pawn, dummy_game):
    """Pawn cannot double step if already moved."""
    pawn.has_moved = True
    cmd = Command.move(pawn.piece_id, (1, 1), (3, 1), player="WHITE", ts=1000)
    pawn.on_command(cmd, 1000, dummy_game)
    assert pawn.current_state.physics.path == []

def test_white_pawn_diagonal_capture(pawn, dummy_game):
    """Pawn captures diagonally when enemy is present."""

    enemy_state = DummyState()

    class Enemy(Piece):
        def __init__(self):
            super().__init__("PB_2_2", enemy_state)
            self.is_captured = False
            self.current_state = enemy_state

    enemy = Enemy()
    dummy_game.black_pieces.append(enemy)
    dummy_game.pieces.append(enemy)
    dummy_game.set_piece_at(enemy, (2, 2))  # ← ← ← הכי קריטי בכל הקובץ הזה

    cmd = Command.move(pawn.piece_id, (1, 1), (2, 2), player="WHITE", ts=1000)
    pawn.on_command(cmd, 1000, dummy_game)

    enemy.is_captured = True 

    assert pawn.current_state.physics.path == [(1, 1), (2, 2)]
    assert enemy.is_captured

def test_white_pawn_illegal_diagonal_without_enemy(pawn, dummy_game):
    """Pawn should not move diagonally if no enemy exists."""
    cmd = Command.move(pawn.piece_id, (1, 1), (2, 2), player="WHITE", ts=1000)
    pawn.on_command(cmd, 1000, dummy_game)
    assert pawn.current_state.physics.path == []

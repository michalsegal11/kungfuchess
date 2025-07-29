# tests/test_pieces/test_Piece.py
import pytest
import tempfile, pathlib

from pieces.Piece import Piece
from engine.State import State
from engine.Moves import Moves, MoveRule
from graphics.Graphics import Graphics
from physics.slide_physics import SlidePhysics
from engine.Command import Command
from engine.Board import Board
from graphics.img import Img


# ------------------------ Dummy setup ------------------------

class DummyGame:
    def __init__(self):
        self.bus = DummyBus()
        self.white_pieces = []
        self.black_pieces = []

    def _piece_at(self, r, c):
        return None

class DummyBus:
    def publish(self, event):
        pass

@pytest.fixture
def dummy_board():
    return Board(cell_H_pix=64, cell_W_pix=64, W_cells=8, H_cells=8, img=Img())

@pytest.fixture
def dummy_state(dummy_board):
    """Creates a State with a valid 'move' transition (no copy() call)."""
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as f:
        f.write("1,0\n")  # one simple forward move
        f.flush()
        moves_path = pathlib.Path(f.name)

    moves = Moves(txt_path=moves_path, board_size=(8, 8))
    gfx = Graphics(sprites_folder=pathlib.Path("."), cell_size=(64, 64))
    phys = SlidePhysics((0, 0), dummy_board)

    idle = State(moves, gfx, phys, {"state_name": "idle"})

    # במקום phys.copy() – צור חדש
    move_phys = SlidePhysics((0, 0), dummy_board)
    move = State(moves, gfx.copy(), move_phys, {"state_name": "move"})

    idle.set_transition("move", move)
    return idle


@pytest.fixture
def piece(dummy_state):
    return Piece("P1", dummy_state)

# ------------------------- Tests -------------------------

def test_reset_resets_piece_state(piece):
    """Check that reset() returns piece to initial state."""
    piece.current_state.state_name = "move"
    piece.reset(start_ms=12345)
    assert piece.current_state == piece.initial_state
    assert piece._last_action_ms == 0
    assert piece.current_state.state_name == piece.initial_state.state_name

def test_update_auto_transition(piece):
    """Ensure update() works and doesn't break."""
    piece._last_action_ms = 0
    piece.update(now_ms=1000)
    assert piece.current_state is not None

def test_illegal_move_blocked(piece):
    """Move to an unreachable square should be rejected."""
    cmd = Command.move("P1", (0, 0), (7, 7), player="WHITE")
    game = DummyGame()
    game.white_pieces.append(piece)
    piece.on_command(cmd, now_ms=10000, game=game)
    assert piece.current_state.state_name == "idle"

def test_jump_command(piece):
    """Jump command should execute and not crash."""
    cmd = Command.create_jump_command("P1", positions=[(0, 0)], timestamp=1000, player_id="WHITE")
    piece.on_command(cmd, now_ms=1000)
    assert piece.current_state is not None

def test_draw_on_board_does_not_crash(piece, dummy_board):
    """draw_on_board() should not crash even if image is empty."""
    piece.draw_on_board(dummy_board)

def test_get_cell_returns_current_position(piece):
    """get_cell() should return a valid (row,col) tuple."""
    cell = piece.get_cell()
    assert isinstance(cell, tuple)
    assert len(cell) == 2

def test_command_rejects_unknown_type():
    """Command should raise error on invalid type."""
    with pytest.raises(ValueError):
        Command(timestamp=1234, piece_id="P1", type="Unknown", params=[])

def test_on_command_jump_with_no_params_does_nothing(piece):
    """Jump with empty params should not break."""
    cmd = Command(timestamp=1234, piece_id="P1", type="Jump", params=[])
    piece.on_command(cmd, now_ms=1234)
    assert piece.current_state == piece.initial_state

def test_propagate_piece_id_applies_to_all_states(piece):
    """_propagate_piece_id() should reach all FSM states."""
    piece._propagate_piece_id("TEST_ID")
    visited = set()

    def dfs(state):
        if id(state) in visited:
            return
        visited.add(id(state))
        assert state.piece_id == "TEST_ID"
        for nxt in state.transitions.values():
            dfs(nxt)

    dfs(piece.current_state)

def test_on_command_valid_move_advances_state(piece):
    """Valid move should cause state transition from idle → move."""
    from_cell = (0, 0)
    to_cell   = (1, 0)
    piece.current_state.physics.current_cell = from_cell
    piece.moves.rules = [MoveRule(1, 0)]  # simulate legal move
    game = DummyGame()
    piece.on_command(Command.move("P1", from_cell, to_cell), now_ms=10000, game=game)
    assert piece.current_state.state_name == "move"

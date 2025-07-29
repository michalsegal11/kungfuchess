
import pytest
import time
from engine.State import State
from engine.Moves import Moves
from graphics.Graphics import Graphics
from physics.idle_physics import IdlePhysics
from physics.slide_physics import SlidePhysics
from engine.Command import Command
from engine.Board import Board
from graphics.img import Img

# ----------------------------- Fixtures -----------------------------

@pytest.fixture
def dummy_board():
    return Board(64, 64, 8, 8, Img())

@pytest.fixture
def idle_state(dummy_board):
    moves = Moves(None, (8, 8))
    gfx = Graphics(sprites_folder=None, cell_size=(64, 64))
    phys = IdlePhysics((1, 1), dummy_board)
    return State(moves, gfx, phys, cfg={"state_name": "idle"})

@pytest.fixture
def move_state(dummy_board):
    moves = Moves(None, (8, 8))
    gfx = Graphics(sprites_folder=None, cell_size=(64, 64))
    phys = SlidePhysics((1, 1), dummy_board)
    return State(moves, gfx, phys, cfg={"state_name": "move"})

# ----------------------------- Tests -----------------------------

def test_set_transition_and_use_command(idle_state, move_state):
    idle_state.set_transition("move", move_state)
    cmd = Command.move("P1", (1, 1), (2, 1), player="WHITE", ts=1000)
    result = idle_state.get_state_after_command(cmd, now_ms=2000)
    assert result is move_state
    assert result.current_command == cmd

def test_invalid_transition_keeps_state(idle_state):
    cmd = Command.move("P1", (1, 1), (2, 1), player="WHITE", ts=1000)
    result = idle_state.get_state_after_command(cmd, now_ms=2000)
    assert result is idle_state

def test_reset_applies_correct_fields(idle_state):
    cmd = Command.move("P1", (1, 1), (2, 1), player="WHITE", ts=1234)
    idle_state.reset(cmd)
    assert idle_state.current_command == cmd
    assert idle_state.state_start_time == 1234

def test_update_triggers_auto_transition_if_ready(dummy_board):
    s1 = SlidePhysics((0, 0), dummy_board)
    s2 = SlidePhysics((0, 0), dummy_board)

    state1 = State(Moves(None, (8, 8)), Graphics(None, (64, 64)), s1,
                   cfg={"state_name": "move", "physics": {"next_state_when_finished": "idle"}})
    state2 = State(Moves(None, (8, 8)), Graphics(None, (64, 64)), s2,
                   cfg={"state_name": "idle"})

    state1.set_transition("idle", state2)
    state1.reset(Command.move("P1", (0, 0), (0, 1), ts=1000))
    state1.state_start_time = 0
    state1.physics._moving = False

    result = state1.update(now_ms=3000)
    assert result is state2
    assert result.state_name == "idle"

def test_clone_deep_copies_state_graph(idle_state, move_state):
    idle_state.set_transition("move", move_state)
    clone = idle_state.copy()
    assert clone is not idle_state
    assert "move" in clone.transitions
    assert clone.transitions["move"] is not move_state

def test_get_cell_returns_correct_cell(idle_state):
    assert idle_state.get_cell() == (1, 1)

def test_start_move_sets_correct_command_and_path(dummy_board):
    moves = Moves(None, (8, 8))
    gfx = Graphics(None, (64, 64))
    phys = SlidePhysics((1, 1), dummy_board)
    state = State(moves, gfx, phys, cfg={"state_name": "move"})

    # Single target cell
    state.start_move((2, 1), now_ms=2000)
    assert state.physics.is_moving
    assert state.physics.current_command.params[-1] == (2, 1)

    # Full path
    path = [(1, 1), (2, 2), (3, 3)]
    state.start_move(path, now_ms=3000)
    assert state.physics.is_moving
    assert state.physics.current_command.params[-1] == (3, 3)
    assert state.physics.start_time_ms == 3000

def test_auto_transition_skips_if_moving(dummy_board):
    phys = SlidePhysics((0, 0), dummy_board)
    state = State(Moves(None, (8, 8)), Graphics(None, (64, 64)), phys,
                  cfg={"state_name": "move", "physics": {"next_state_when_finished": "idle"}})
    phys._moving = True
    result = state.update(now_ms=999999)
    assert result is state

def test_auto_transition_no_target_state(dummy_board):
    phys = SlidePhysics((0, 0), dummy_board)
    state = State(Moves(None, (8, 8)), Graphics(None, (64, 64)), phys,
                  cfg={"state_name": "move", "physics": {"next_state_when_finished": "idle"}})
    phys._moving = False
    result = state.update(now_ms=999999)
    assert result is state

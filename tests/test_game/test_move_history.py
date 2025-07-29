import pytest
from game.move_history import cell_to_sq, fmt_elapsed, notation_from_cmd, record_move
from engine.Command import Command

class DummyBus:
    def __init__(self):
        self.published = []

    def publish(self, event):
        self.published.append(event)

class DummyGame:
    def __init__(self):
        self.move_history = {"WHITE": [], "BLACK": []}
        self.bus = DummyBus()
        self.game_start_ms = 10000  # 10 seconds

# -----------------------------------------------------------------------------

def test_cell_to_sq_conversion():
    """Test conversion from board cell to chess square notation."""
    assert cell_to_sq((0, 0)) == "a1"
    assert cell_to_sq((3, 4)) == "e4"
    assert cell_to_sq((7, 7)) == "h8"

def test_fmt_elapsed_returns_correct_format():
    """Ensure elapsed time is formatted as MM:SS.ss from game start."""
    game = DummyGame()
    now_ms = 16000  # 6 seconds after start
    assert fmt_elapsed(game, now_ms) == "00:06.00"

def test_notation_from_cmd_move():
    """Test move command conversion to text notation."""
    cmd = Command.move("PW_1_1", (1, 1), (2, 1), player="WHITE", ts=12345)
    assert notation_from_cmd(cmd) == "MOVE PW_1_1: (1, 1) -> (2, 1)"

def test_notation_from_cmd_jump():
    """Test jump command conversion to text notation."""
    cmd = Command.create_jump_command("NB_2_3", [(2, 3), (4, 4)], player_id="BLACK", timestamp=12345)
    assert notation_from_cmd(cmd) == "JUMP NB_2_3: at (2, 3)"

def test_notation_from_cmd_capture():
    """Test capture command conversion to text notation."""
    cmd = Command.capture("QW_0_3", (0, 3), (1, 4), "PB_1_4", player="WHITE", ts=12345)
    assert notation_from_cmd(cmd) == "CAPTURE at (1, 4)"

def test_record_move_adds_entry_and_event():
    """Ensure a move is recorded and event is published."""
    game = DummyGame()
    cmd = Command.move("RW_0_0", (0, 0), (0, 5), player="WHITE", ts=12000)
    record_move(game, "WHITE", cmd)

    assert len(game.move_history["WHITE"]) == 1
    ts, nota = game.move_history["WHITE"][0]
    assert ts == "00:02.00"
    assert nota == "MOVE RW_0_0: (0, 0) -> (0, 5)"
    assert game.bus.published  # at least one event published

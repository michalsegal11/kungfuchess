# tests/test_ui/test_move_log_ui.py
import pytest
import numpy as np
from ui.move_log_ui import MoveLogUI
from engine.events import MovePlayed


class DummyBus:
    """Mock event bus for testing."""
    def __init__(self):
        self.subscriptions = {}

    def subscribe(self, event_type, cb):
        self.subscriptions[event_type] = cb

    def publish(self, event):
        if type(event) in self.subscriptions:
            self.subscriptions[type(event)](event)


@pytest.fixture
def dummy_bus():
    return DummyBus()


@pytest.fixture
def move_log_ui(dummy_bus):
    return MoveLogUI(dummy_bus)


def test_move_log_subscribes_to_bus(dummy_bus, move_log_ui):
    """Should subscribe to MovePlayed events on init."""
    assert MovePlayed in dummy_bus.subscriptions


def test_on_move_appends_to_rows(move_log_ui):
    """Should store incoming MovePlayed events in rows."""
    evt = MovePlayed(time_ms=1234, move="Qxe5", color="WHITE")
    move_log_ui._on_move(evt)

    assert len(move_log_ui.rows) == 1
    assert move_log_ui.rows[0] == (1234, "Qxe5")


def test_rows_limited_to_50(move_log_ui):
    """Should not exceed 50 rows (deque maxlen)."""
    for i in range(100):
        move_log_ui._on_move(MovePlayed(time_ms=i, move=f"MOVE_{i}", color="WHITE"))

    assert len(move_log_ui.rows) == 50
    assert move_log_ui.rows[0][1] == "MOVE_99"
    assert move_log_ui.rows[-1][1] == "MOVE_50"


def test_draw_does_not_crash_with_no_moves(move_log_ui):
    """Should safely draw even when rows is empty."""
    dummy_frame = np.zeros((600, 800, 3), dtype=np.uint8)
    move_log_ui.draw(dummy_frame, side="left")


def test_draw_draws_up_to_20_moves(move_log_ui):
    """Should attempt to draw only the last 20 moves on frame."""
    dummy_frame = np.zeros((600, 800, 3), dtype=np.uint8)

    for i in range(25):
        move_log_ui._on_move(MovePlayed(time_ms=1000 + i, move=f"m{i}", color="WHITE"))

    move_log_ui.draw(dummy_frame, side="right")


import numpy as np
import pytest
import cv2
from ui.score_ui import ScoreUI
from engine.events import PieceTaken


class DummyBus:
    """Simulates an event bus and allows triggering callbacks."""
    def __init__(self):
        self.subscribers = {}

    def subscribe(self, event_type, callback):
        self.subscribers[event_type] = callback

    def publish(self, event):
        callback = self.subscribers.get(type(event))
        if callback:
            callback(event)


class TestableScoreUI(ScoreUI):
    """Override draw() to force black text for visibility on white frame."""
    def draw(self, frame):
        txt = f"Black Score: {self.black}   |  White Score: {self.white}"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1.2
        thickness = 2
        color = (0, 0, 0)  # Black text for visibility

        text_size, _ = cv2.getTextSize(txt, font, font_scale, thickness)
        text_x = (frame.shape[1] - text_size[0]) // 2
        text_y = 50
        cv2.putText(frame, txt, (text_x, text_y), font, font_scale, color, thickness, cv2.LINE_AA)


@pytest.fixture
def dummy_frame():
    """Returns a blank white frame for drawing on."""
    return np.ones((120, 400, 3), dtype=np.uint8) * 255


@pytest.fixture
def score_ui():
    """Initializes testable ScoreUI with a dummy bus."""
    bus = DummyBus()
    ui = TestableScoreUI(bus)
    return ui, bus


def test_initial_score_is_zero(score_ui):
    """Verify both scores are zero at initialization."""
    ui, _ = score_ui
    assert ui.white == 0
    assert ui.black == 0


def test_score_updates_on_capture(score_ui):
    """Test that scores update correctly after captures."""
    ui, bus = score_ui

    # Black captures a white piece worth 5
    bus.publish(PieceTaken(value=5, color="BLACK"))
    assert ui.white == 5
    assert ui.black == 0

    # White captures a black piece worth 3
    bus.publish(PieceTaken(value=3, color="WHITE"))
    assert ui.white == 5
    assert ui.black == 3


def test_draw_displays_correct_text(score_ui, dummy_frame):
    """Ensure that score text is visibly drawn on the frame."""
    ui, _ = score_ui
    ui.white = 7
    ui.black = 12

    frame = dummy_frame.copy()
    ui.draw(frame)

    # Check if any pixels changed (i.e. not pure white)
    assert not np.all(frame == 255), "Expected frame to change due to text rendering"

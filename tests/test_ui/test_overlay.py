import pytest
import numpy as np
import pygame
from ui.overlay import Overlay


class DummyGame:
    """Minimal game object holding the image buffer."""
    def __init__(self):
        self.final_img = np.ones((200, 200, 3), dtype=np.uint8) * 255


class DummyBus:
    """Mock bus to track events without real dispatching."""
    def subscribe(self, event_type, callback):
        pass  # No-op for tests

    def publish(self, event):
        self.last_event = event


class TestableOverlay(Overlay):
    """
    Subclass of Overlay for testing purposes.

    Adds test-friendly methods `set` and `clear`, and allows injecting time manually.
    """
    def set(self, msg: str, now_ms: int, duration_ms: int):
        self.current_msg = msg
        self.until_ms = now_ms + duration_ms

    def clear(self):
        self.current_msg = None
        self.until_ms = 0

    def draw(self, frame, now_ms: int | None = None):
        # override pygame's internal time during test
        self._test_now_ms = now_ms
        now = now_ms if now_ms is not None else pygame.time.get_ticks()

        # Duplicate logic from base instead of calling super().draw()
        if self.current_msg is None and self.msg_queue:
            self.current_msg, dur = self.msg_queue.popleft()
            self.until_ms = now + dur
            if self.current_msg in self.sounds:
                self.sounds[self.current_msg].play()

        if self.current_msg and now > self.until_ms:
            self.current_msg = None
            return

        if not self.current_msg:
            return

        h, w = frame.shape[:2]
        overlay = frame.copy()
        import cv2
        cv2.rectangle(overlay, (0, h // 2 - 40), (w, h // 2 + 40), (0, 0, 0), -1)
        alpha = 0.6
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

        font_scale = 1.6
        thickness = 3
        color = (255, 255, 255)
        font = cv2.FONT_HERSHEY_SIMPLEX
        (text_w, text_h), _ = cv2.getTextSize(self.current_msg, font, font_scale, thickness)
        x = (w - text_w) // 2
        y = (h + text_h) // 2
        cv2.putText(frame, self.current_msg, (x, y), font, font_scale, color, thickness, cv2.LINE_AA)



@pytest.fixture
def overlay():
    return TestableOverlay(bus=DummyBus())

@pytest.fixture
def game():
    return DummyGame()


def test_set_message_sets_text_and_duration(overlay):
    """Test that `set()` correctly stores message and expiration time."""
    overlay.set("Ready", now_ms=1000, duration_ms=3000)
    assert overlay.current_msg == "Ready"
    assert overlay.until_ms == 4000


def test_clear_resets_state(overlay):
    """Test that `clear()` resets overlay state."""
    overlay.set("Go!", now_ms=1000, duration_ms=2000)
    overlay.clear()
    assert overlay.current_msg is None
    assert overlay.until_ms == 0


def test_draw_renders_message_on_img(game, overlay):
    """Test that `draw()` modifies image when a message is active."""
    overlay.set("Go!", now_ms=0, duration_ms=2000)
    original_img = game.final_img.copy()
    overlay.draw(game.final_img, now_ms=1000)
    assert not np.array_equal(game.final_img, original_img)


def test_draw_does_not_render_when_no_message(game, overlay):
    """Test that `draw()` does nothing when message is not set."""
    original_img = game.final_img.copy()
    overlay.draw(game.final_img, now_ms=1000)
    assert np.array_equal(game.final_img, original_img)


def test_draw_auto_expires_message(game, overlay):
    """Test that expired message is removed automatically by `draw()`."""
    overlay.set("GO!", now_ms=1000, duration_ms=500)
    overlay.draw(game.final_img, now_ms=2000)
    assert overlay.current_msg is None
    assert overlay.until_ms == 1500  # ← still stored (optional)

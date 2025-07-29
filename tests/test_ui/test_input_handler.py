import pytest
from ui.input_handler import InputHandler

class DummyGame:
    def __init__(self):
        self.running = True

def test_input_handler_quit_keys(monkeypatch):
    """Simulate 'q' and 'esc' key presses and verify game stops."""

    # Prevent the thread from starting
    monkeypatch.setattr("threading.Thread.start", lambda self: None)

    # Prevent keyboard.wait() from blocking forever
    monkeypatch.setattr("keyboard.wait", lambda: None)

    # Collect the callback passed to keyboard.hook
    events = []
    def fake_hook(cb):
        events.append(cb)

    monkeypatch.setattr("keyboard.hook", fake_hook)

    game = DummyGame()
    handler = InputHandler(game)

    # Run the hook manually so fake_hook gets called
    handler._hook()

    assert events, "keyboard.hook was not called"
    cb = events[0]

    class DummyEvent:
        def __init__(self, name):
            self.name = name
            self.event_type = 'down'

    cb(DummyEvent("q"))
    assert not game.running

    game.running = True
    cb(DummyEvent("esc"))
    assert not game.running

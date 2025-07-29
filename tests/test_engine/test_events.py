# tests/test_engine/test_events.py
import pytest
from engine.events import EventBus, MovePlayed, PieceTaken, GameStarted, GameEnded

@pytest.fixture
def bus():
    return EventBus()

def test_subscriber_receives_event(bus):
    received = []

    def on_move(event):
        received.append(event)

    bus.subscribe(MovePlayed, on_move)
    event = MovePlayed(time_ms=1234, move="e2e4", color="WHITE")
    bus.publish(event)

    assert received == [event]

def test_multiple_subscribers_receive_event(bus):
    received_1 = []
    received_2 = []

    bus.subscribe(MovePlayed, lambda e: received_1.append(e))
    bus.subscribe(MovePlayed, lambda e: received_2.append(e))

    event = MovePlayed(time_ms=2000, move="g1f3", color="WHITE")
    bus.publish(event)

    assert received_1 == [event]
    assert received_2 == [event]

def test_subscriber_does_not_receive_other_type(bus):
    received = []

    bus.subscribe(PieceTaken, lambda e: received.append(e))

    event = MovePlayed(time_ms=3000, move="b8c6", color="BLACK")
    bus.publish(event)

    assert received == []  # לא קיבל כי זה לא PieceTaken

def test_publish_game_started(bus):
    received = []
    bus.subscribe(GameStarted, lambda e: received.append(e))

    event = GameStarted(white="Alice", black="Bob")
    bus.publish(event)

    assert len(received) == 1
    assert received[0].white == "Alice"
    assert received[0].black == "Bob"

def test_publish_game_ended_with_winner(bus):
    received = []
    bus.subscribe(GameEnded, lambda e: received.append(e))

    event = GameEnded(winner="BLACK")
    bus.publish(event)

    assert received == [event]

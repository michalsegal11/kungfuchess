import pytest
from unittest.mock import MagicMock, patch

from ui.sound_fx import SoundFX
from engine.events import MovePlayed, PieceTaken, JumpPlayed, ErrorPlayed
from engine.events import EventBus


@pytest.fixture
def mock_mixer():
    """Patch pygame.mixer.Sound and return a mock for all sounds."""
    with patch("pygame.mixer.init"), \
         patch("pygame.mixer.Sound") as mock_sound_class:
        
        mock_move  = MagicMock()
        mock_cap   = MagicMock()
        mock_jump  = MagicMock()
        mock_error = MagicMock()
        
        # Set up the mock to return different sounds for each event
        mock_sound_class.side_effect = [mock_move, mock_cap, mock_jump, mock_error]
        
        yield {
            "mock_sound_class": mock_sound_class,
            "move": mock_move,
            "cap": mock_cap,
            "jump": mock_jump,
            "error": mock_error
        }


def test_soundfx_event_triggers_sound(mock_mixer):
    """Ensure each game event triggers the correct sound effect."""
    bus = EventBus()

    # Mock the sounds
    sfx = SoundFX(bus, "move.wav", "cap.wav", "jump.wav", "error.wav")

    # regularly check the mock mixer
    bus.publish(MovePlayed(time_ms=0, move="e2→e4", color="WHITE"))
    mock_mixer["move"].play.assert_called_once()

    #cupture
    bus.publish(PieceTaken(value=5, color="BLACK"))
    mock_mixer["cap"].play.assert_called_once()

    #jump
    bus.publish(JumpPlayed(time_ms=0, color="WHITE"))
    mock_mixer["jump"].play.assert_called_once()

    #sound error
    bus.publish(ErrorPlayed(time_ms=0, reason="illegal", piece="QW_0_3"))
    mock_mixer["error"].play.assert_called_once()


def test_soundfx_subscribes_to_all_events(mock_mixer):
    """Ensure SoundFX subscribes to all relevant event types."""
    bus = EventBus()
    sfx = SoundFX(bus, "move.wav", "cap.wav", "jump.wav", "error.wav")

    assert MovePlayed   in bus._subs
    assert PieceTaken   in bus._subs
    assert JumpPlayed   in bus._subs
    assert ErrorPlayed  in bus._subs
    assert len(bus._subs[MovePlayed]) > 0


import pytest
from unittest.mock import MagicMock
from game.game import Game
from engine.events import ErrorPlayed, MovePlayed, JumpPlayed, PieceTaken

# ==============================
# Dummy Classes for Simulation
# ==============================

class DummyPiece:
    """
    A simplified mock piece for unit tests.
    Mimics basic attributes and methods used by the Game.
    """
    def __init__(self, piece_id="KW_7_4", cell=(7, 4), color="WHITE"):
        self.piece_id = piece_id
        self._cell = cell
        self.color = color
        self.commands = []
        self.is_captured = False
        self.can_jump_over_allies = False
        self.current_state = MagicMock()
        self.current_state.physics.get_current_cell.return_value = cell
        self.current_state.moves = MagicMock()
        self.current_state.moves.get_moves = lambda *a, **k: [(6, 4)]

    def reset(self, now): pass
    def update(self, ms): pass

    def on_command(self, cmd, now, game):
        self.commands.append(cmd)

        if cmd.type == "Jump":
            from engine.events import JumpPlayed
            game.bus.publish(JumpPlayed(now, cmd.player_id))

        elif cmd.type == "Move":
            from_cell, to_cell = cmd.params
            victim = game._piece_at(*to_cell)

            # ---- capture handling -----------------------------------------
            if victim and victim is not self and not victim.is_captured:
                victim.is_captured = True
                from engine.events import PieceTaken
                game.bus.publish(
                    PieceTaken(
                        victim.piece_id,   # piece_id that was taken
                        to_cell,           # board cell
                        self.color,        # the capturing side
                        1                  # piece value (simplified)
                    )
                )

            # ---- normal move event ----------------------------------------
            from engine.events import MovePlayed
            game.bus.publish(
                MovePlayed(now,
                        f"MOVE {self.piece_id}: {from_cell} -> {to_cell}",
                        cmd.player_id)
            )

        return True






    def get_cell(self):
        return self._cell


class DummyBoard:
    """
    A simplified mock board for testing.
    """
    def __init__(self):
        self.H_cells = 8
        self.W_cells = 8
        self.img = MagicMock()
        self.background_img = None

    def clone(self): return self
    def get_cell_center_pixel(self, r, c): return (r*64+32, c*64+32)


class DummyBus:
    """
    A lightweight event bus mock that records published events.
    """
    def __init__(self):
        self.published = []

    def publish(self, e): self.published.append(e)


class FakeInputHandler:
    """
    Replaces the real keyboard input handler for test purposes.
    Delivers simulated key events from a pre-loaded queue.
    """
    def __init__(self, game):
        self.inputs = []
        self.queue = MagicMock()
        self.queue.get = self.get
        self.queue.empty = lambda: not bool(self.inputs)
        self.game = game

    def start(self): pass

    def get(self):
        if self.inputs:
            player, key = self.inputs.pop(0)
            if key.lower() in ('q', 'esc'):
                self.game.running = False
            return player, key
        self.game.running = False
        return ("WHITE", "q")

# ==============================
# Actual Unit Tests
# ==============================

def test_regular_move(monkeypatch):
    """
    Test a legal move from (7,4) to (6,4) with a white king.
    """
    p1 = DummyPiece("KW_7_4", (7, 4), "WHITE")
    p2 = DummyPiece("KB_0_4", (0, 4), "BLACK")  # king required
    board = DummyBoard()
    game = Game([p1, p2], board)

    game.input = FakeInputHandler(game)
    game.input.inputs = [
        ("WHITE", "ENTER"),
        ("WHITE", "UP"),
        ("WHITE", "ENTER"),
        ("WHITE", "q")
    ]

    import ui.ui as uiview
    monkeypatch.setattr(uiview, "draw", lambda g: None)
    monkeypatch.setattr(uiview, "show", lambda g: False)

    game.bus = DummyBus()
    game.move_history = {"WHITE": [], "BLACK": []}
    game._piece_at = lambda r, c: p1 if (r, c) == p1.get_cell() else None

    game.run()

    assert any(cmd.type == "Move" for cmd in game.command_history)
    assert not game.running


def test_jump_move(monkeypatch):
    """
    Test a jump action by selecting the same square twice.
    """
    p1 = DummyPiece("KW_7_4", (7, 4), "WHITE")
    p2 = DummyPiece("KB_0_4", (0, 4), "BLACK")
    board = DummyBoard()
    game = Game([p1, p2], board)

    game.input = FakeInputHandler(game)
    game.input.inputs = [
        ("WHITE", "ENTER"),
        ("WHITE", "ENTER"),
        ("WHITE", "q")
    ]

    import ui.ui as uiview
    monkeypatch.setattr(uiview, "draw", lambda g: None)
    monkeypatch.setattr(uiview, "show", lambda g: False)

    game.bus = DummyBus()
    game.move_history = {"WHITE": [], "BLACK": []}
    game._piece_at = lambda r, c: p1 if (r, c) == (7, 4) else None

    game.run()

    assert any(cmd.type == "Jump" for cmd in game.command_history)
    assert any(isinstance(e, JumpPlayed) for e in game.bus.published)


def test_illegal_move(monkeypatch):
    """
    Test trying to move to a non-legal square (6,4 is not allowed).
    Should trigger ErrorPlayed event.
    """
    p1 = DummyPiece("KW_7_4", (7, 4), "WHITE")
    p1.current_state.moves.get_moves = lambda *a, **k: [(5, 5)]  # only (5,5) is legal
    p2 = DummyPiece("KB_0_4", (0, 4), "BLACK")
    board = DummyBoard()
    game = Game([p1, p2], board)

    game.input = FakeInputHandler(game)
    game.input.inputs = [
        ("WHITE", "ENTER"),
        ("WHITE", "UP"),
        ("WHITE", "ENTER"),
        ("WHITE", "q")
    ]

    import ui.ui as uiview
    monkeypatch.setattr(uiview, "draw", lambda g: None)
    monkeypatch.setattr(uiview, "show", lambda g: False)

    game.bus = DummyBus()
    game.move_history = {"WHITE": [], "BLACK": []}
    game._piece_at = lambda r, c: p1 if (r, c) == (7, 4) else None

    game.run()

    assert any(isinstance(e, ErrorPlayed) and e.reason == "illegal move" for e in game.bus.published)


def test_capture_move(monkeypatch):
    """
    Test a capture move where a white pawn moves from (6,4) to (5,4)
    and captures a black pawn.
    """
    p1 = DummyPiece("PW_6_4", (6, 4), "WHITE")
    p2 = DummyPiece("PB_5_4", (5, 4), "BLACK")
    king_white = DummyPiece("KW_7_0", (7, 0), "WHITE")
    king_black = DummyPiece("KB_0_0", (0, 0), "BLACK")
    board = DummyBoard()
    game = Game([p1, p2, king_white, king_black], board)


    game.white_cursor = [6, 4]

    game.input = FakeInputHandler(game)
    game.input.inputs = [
        ("WHITE", "ENTER"),
        ("WHITE", "UP"),
        ("WHITE", "ENTER"),
        ("WHITE", "q")
    ]

    import ui.ui as uiview
    monkeypatch.setattr(uiview, "draw", lambda g: None)
    monkeypatch.setattr(uiview, "show", lambda g: False)

    game.bus = DummyBus()
    game.move_history = {"WHITE": [], "BLACK": []}
    game._piece_at = lambda r, c: (
        p1 if (r, c) == (6, 4) else
        p2 if (r, c) == (5, 4) else
        king_white if (r, c) == (7, 0) else
        king_black if (r, c) == (0, 0) else None
    )

    # allow capture as a legal destination
    p1.current_state.moves.get_moves = lambda *a, **k: [(5, 4)]

    game.run()

    assert any(cmd.type == "Move" for cmd in game.command_history)
    assert p2.is_captured is True
    assert any(isinstance(e, PieceTaken) for e in game.bus.published)

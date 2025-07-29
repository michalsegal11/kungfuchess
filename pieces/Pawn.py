# ---------------------------- Pawn.py ----------------------------
from typing import Tuple
from engine.Command import Command
from pieces.Piece import Piece

# Movement tags used in moves.txt to classify pawn movement types
TAG_FWD        = {"f", "non_capture", ""}
TAG_FWD_DOUBLE = {"ff", "1st"}
TAG_CAPTURE    = {"x", "capture"}

class Pawn(Piece):
    """
    Represents a pawn piece with unique forward movement rules.

    Attributes:
        forward (int): +1 for white pawns, -1 for black pawns
        has_moved (bool): True if pawn has already moved (affects double-step)
    """

    def __init__(self, *args, forward: int, **kwargs):
        super().__init__(*args, **kwargs)
        self.forward = forward
        self.has_moved = False

    @property
    def physics(self):
        """Returns the physics engine of the current state."""
        return self.current_state.physics

    def _legal_dests(self, game, from_cell: Tuple[int, int]) -> list[Tuple[int, int]]:
        """
        Computes all legal destination cells from a given origin cell.

        Movement logic:
        - Forward (1 step): only if empty
        - Double forward: only if it's the first move and both cells are empty
        - Capture: diagonal movement only if enemy piece present
        """
        r0, c0 = from_cell
        legal = []

        for rule in self.moves.rules:
            dr, dc, tag = rule.dr, rule.dc, rule.tag.lower()
            dest = (r0 + dr, c0 + dc)

            if not self.physics.board.is_valid_cell(*dest):
                continue

            piece = game._piece_at(*dest)
            empty = piece is None

            if self in game.white_pieces:
                is_enemy = piece in game.black_pieces and not piece.is_captured
            else:
                is_enemy = piece in game.white_pieces and not piece.is_captured

            if tag in TAG_FWD and empty and dc == 0:
                legal.append(dest)
            elif tag in TAG_FWD_DOUBLE and not self.has_moved and empty and dc == 0:
                mid = (r0 + dr // 2, c0)
                if game._piece_at(*mid) is None:
                    legal.append(dest)
            elif tag in TAG_CAPTURE and abs(dc) == 1 and dr != 0 and is_enemy:
                legal.append(dest)

        return legal

    def on_command(self, cmd: Command, now_ms: int, game=None) -> bool:
        """
        Handles a 'Move' or 'Jump' command for the pawn.

        Returns:
            True if the command was executed successfully, False otherwise.
        """
        
        if cmd.type == "Jump":
            return super().on_command(cmd, now_ms, game)

        if self.is_captured or cmd.type != "Move" or len(cmd.params) < 2:
            return False

        if now_ms - self._last_action_ms < self.COOLDOWN_MS:
            return False

        from_cell, to_cell = cmd.params

        if game is None or to_cell not in self._legal_dests(game, from_cell):
            from engine.events import ErrorPlayed
            game.bus.publish(ErrorPlayed(now_ms, "illegal pawn move", self.piece_id))
            return False

        self.has_moved = True       
        next_state = self.current_state.get_state_after_command(cmd, now_ms)

        if next_state is self.current_state:
            return False

        next_state.start_move(to_cell, now_ms)
        self.current_state = next_state
        self._last_action_ms = now_ms
        return True

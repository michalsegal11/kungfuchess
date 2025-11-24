# ---------------------------- Pawn.py ----------------------------
from __future__ import annotations
from typing import Tuple, List

from core.engine.Command import Command
from core.pieces.Piece   import Piece
from core.engine.events  import MovePlayed, ErrorPlayed, JumpPlayed
from core.game.move_history import notation_from_cmd

# Movement tags used in moves.txt to classify pawn movement types
TAG_FWD        = {"f", "non_capture", ""}
TAG_FWD_DOUBLE = {"ff", "1st"}
TAG_CAPTURE    = {"x", "capture"}


class Pawn(Piece):
    """
    Pawn piece with forward / capture rules and event publication identical
    to the base *Piece* class.

    * forward = +1  → הלבן מתקדם כלפי-מטה (לפי קואורדינטות הלוח שלך)
    * forward = -1  → השחור מתקדם כלפי-מעלה
    """

    # ───────────────────────── ctor ────────────────────────────────
    def __init__(self, *args, forward: int, **kwargs):
        super().__init__(*args, **kwargs)
        self.forward   = forward
        self.has_moved = False          # מאפשר צעד-כפול רק פעם אחת

    # ------------------------------------------------------------------
    @property
    def physics(self):
        """Shortcut to the current state's physics engine."""
        return self.current_state.physics

    # ------------------------------------------------------------------
    def _legal_dests(
        self, game, from_cell: Tuple[int, int]
    ) -> List[Tuple[int, int]]:
        """
        Calculate all legal destination cells for the pawn.

        Logic
        -----
        * **Forward 1**  – מותר רק אם המשבצת ריקה.
        * **Forward 2**  – רק במהלך הראשון + שתי משבצות ריקות.
        * **Capture**    – באלכסון ±1 עמודה אם במשבצת יש יריב חי.
        """
        r0, c0 = from_cell
        legal: List[Tuple[int, int]] = []

        for rule in self.moves.rules:
            dr, dc, tag = rule.dr, rule.dc, rule.tag.lower()
            dest = (r0 + dr, c0 + dc)

            if not self.physics.board.is_valid_cell(*dest):
                continue

            piece = game._piece_at(*dest)
            empty = piece is None

            # Determine if the piece (if any) שייך ליריב
            is_enemy = (
                piece is not None
                and (
                    (self in game.white_pieces and piece in game.black_pieces) or
                    (self in game.black_pieces and piece in game.white_pieces)
                )
                and not piece.is_captured
            )

            if tag in TAG_FWD and empty and dc == 0:
                legal.append(dest)
            elif (
                tag in TAG_FWD_DOUBLE
                and not self.has_moved
                and empty
                and dc == 0
                and game._piece_at(r0 + dr // 2, c0) is None
            ):
                legal.append(dest)
            elif tag in TAG_CAPTURE and abs(dc) == 1 and is_enemy:
                legal.append(dest)

        return legal

    # ------------------------------------------------------------------
    def on_command(self, cmd: Command, now_ms: int, game=None) -> bool:
        """
        Handle *Move* או *Jump* ומפרסם אירועים:

        * **MovePlayed** – הצלחה
        * **JumpPlayed** – הצלחת קפיצה
        * **ErrorPlayed** – מהלך לא חוקי / חסום
        """
        # Jump: נשתמש בהתנהגות הבסיסית (מפרסם JumpPlayed כבר)
        if cmd.type == "Jump":
            return super().on_command(cmd, now_ms, game)

        # Guards --------------------------------------------------------
        if (
            self.is_captured
            or cmd.type != "Move"
            or len(cmd.params) < 2
        ):
            return False

        if now_ms - self._last_action_ms < self.COOLDOWN_MS:
            return False

        from_cell, to_cell = cmd.params

        # חוקיות --------------------------------------------------------
        if game is None or to_cell not in self._legal_dests(game, from_cell):
            if game:
                game.bus.publish(
                    ErrorPlayed(now_ms, "illegal pawn move", self.piece_id)
                )
            return False

        # קבלת מצב-יעד מה-FSM -----------------------------------------
        next_state = self.current_state.get_state_after_command(cmd, now_ms)
        if next_state is self.current_state:
            if game:
                game.bus.publish(ErrorPlayed(now_ms, "blocked", self.piece_id))
            return False

        # הצלחה – פרסום MovePlayed -------------------------------------
        if game:
            nota = notation_from_cmd(cmd)
            game.bus.publish(MovePlayed(now_ms, nota, cmd.player_id))

        self.has_moved = True
        next_state.start_move(to_cell, now_ms)
        self.current_state      = next_state
        self._last_action_ms    = now_ms
        return True

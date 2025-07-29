# ==========================================
#   Piece.py
# ==========================================

from __future__ import annotations
from typing import Tuple, Optional, Set
from engine.Board import Board
from engine.Command import Command
from engine.State import State
from engine.Moves import Moves
from engine.events import MovePlayed, PieceTaken, ErrorPlayed, JumpPlayed
from game.move_history import notation_from_cmd

DEBUG_STATES = True

def _dbg(*a):
    """Conditional debug print helper."""
    if DEBUG_STATES:
        print(*a)


class Piece:
    """
    Base class representing a general game piece in KungfuChess.

    Attributes:
        piece_id (str): Unique identifier for the piece.
        current_state (State): Current active FSM state of the piece.
        initial_state (State): Initial FSM state for reset purposes.
        moves (Moves): Legal move rules for this piece.
        is_captured (bool): Whether the piece has been captured.
        _last_action_ms (int): Last timestamp the piece performed an action.
        last_move_timestamp (int): Timestamp of the last move attempted.
        can_jump_over_allies (bool): Whether the piece can jump over allied pieces (e.g., knights).
    """

    COOLDOWN_MS: int = 1_000

    def __init__(self, piece_id: str, init_state: State, moves: Moves | None = None) -> None:
        self.piece_id = piece_id
        self.current_state = init_state
        self.initial_state = init_state
        self.moves = moves if moves else init_state.moves
        self.is_captured = False
        self._last_action_ms = 0
        self.last_move_timestamp: int = 0
        self.can_jump_over_allies = piece_id.startswith("N")

    def on_command(self, cmd: Command, now_ms: int, game=None) -> bool:
        """
        Attempt to execute a move or jump command on this piece.

        Args:
            cmd (Command): The command to process.
            now_ms (int): Current timestamp.
            game: Optional reference to the game object.

        Returns:
            bool: True if the command is legal and applied, False otherwise.
        """
        self.last_move_timestamp = cmd.timestamp
        _dbg(f"[{self.piece_id}] on_command {cmd.type} {cmd.params} at {now_ms}ms")

        if self.is_captured or cmd.type not in ("Move", "Jump"):
            return False

        if cmd.type == "Move":
            src_cell, dst_cell = cmd.params
            if dst_cell not in self.moves.get_moves(*src_cell):
                _dbg(f"[{self.piece_id}] illegal move {src_cell}->{dst_cell}")
                if game:
                    game.bus.publish(ErrorPlayed(now_ms, "illegal move", self.piece_id))
                return False
        else:  # Jump
            if not cmd.params:
                return False
            src_cell = cmd.params[0]
            up_cell = (src_cell[0] - 1, src_cell[1])
            if not self.current_state.physics.board.is_valid_cell(*up_cell):
                up_cell = src_cell
            cmd.params = [src_cell, up_cell, src_cell]
            dst_cell = cmd.params

        next_state = self.current_state.get_state_after_command(cmd, now_ms)
        if next_state is self.current_state:
            _dbg(f"[{self.piece_id}] ignored – '{self.current_state.state_name}' blocks move")
            if game:
                game.bus.publish(ErrorPlayed(now_ms, "blocked", self.piece_id))
            return False

        if game:
            if cmd.type == "Jump":
                game.bus.publish(JumpPlayed(now_ms, cmd.player_id))
            elif cmd.type == "Move":
                nota = notation_from_cmd(cmd)
                game.bus.publish(MovePlayed(now_ms, nota, cmd.player_id))

        next_state.start_move(dst_cell, now_ms)
        self.current_state = next_state
        self._last_action_ms = now_ms
        _dbg(f"[{self.piece_id}] state={self.current_state.state_name} start_move {src_cell}->{dst_cell}")
        return True

    def reset(self, start_ms: int) -> None:
        """
        Reset this piece to its initial state and position.

        Args:
            start_ms (int): Timestamp for the reset event.
        """
        self.is_captured = False
        self._last_action_ms = 0
        self.current_state = self.initial_state
        self.current_state.reset(Command(start_ms, self.piece_id, "Reset", []))

    def update(self, now_ms: int) -> None:
        """
        Advance animation and handle auto-transitions if any.

        Args:
            now_ms (int): Current timestamp in milliseconds.
        """
        if not self.is_captured:
            new_state = self.current_state.update(now_ms)

            # If the piece is moving, update the future cell tracking
            if self.current_state.physics.is_movement_finished():
                cell = self.get_cell()
                board = self.current_state.physics.board
                game = getattr(board, "game", None)
                if game and isinstance(game.future_cells, dict):
                    entry = game.future_cells.get(cell)
                    if entry and entry["piece_id"] == self.piece_id:
                        del game.future_cells[cell]

            if new_state is not self.current_state:
                _dbg(f"[{self.piece_id}] auto {self.current_state.state_name} -> {new_state.state_name}")
            self.current_state = new_state

            # missing piece_id propagation
            if self.current_state.piece_id is None:
                self._propagate_piece_id(self.piece_id)


    def draw_on_board(self, board: Board) -> None:
        """
        Render this piece's image on the game board.

        Args:
            board (Board): The game board image buffer.
        """
        if self.is_captured:
            return
        img = self.current_state.get_current_image()
        cx, cy = self.current_state.get_current_position()
        if img.img is None:
            return
        h, w = img.img.shape[:2]
        img.draw_on(board.img, int(cx - w / 2), int(cy - h / 2))

    def get_cell(self) -> Tuple[int, int]:
        """
        Get the current cell coordinates of the piece.

        Returns:
            tuple[int, int]: (row, col)
        """
        return self.current_state.physics.get_current_cell()

    def _propagate_piece_id(self, pid: str) -> None:
        """
        Propagate the piece ID to all reachable states in the FSM.

        Args:
            pid (str): The piece ID to assign.
        """
        seen: Set[int] = set()
        def rec(st: State):
            if id(st) in seen:
                return
            seen.add(id(st))
            st.piece_id = pid
            for nxt in st.transitions.values():
                rec(nxt)
        rec(self.current_state)

    def debug_dump_machine(self) -> None:
        """
        Print the structure of the FSM for debugging purposes.
        """
        seen: Set[int] = set()
        def rec(st: State, indent: str = ""):
            if id(st) in seen:
                print(indent + f"{st.state_name} (…)"); return
            seen.add(id(st))
            print(indent + f"{st.state_name} auto→{st.next_state_name or '-'}")
            for ev, nxt in st.transitions.items():
                print(indent + f"  {ev} -> {nxt.state_name}")
                rec(nxt, indent + "    ")
        print(f"=== State machine for {self.piece_id} ===")
        rec(self.current_state)
        print("===")

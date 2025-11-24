"""High‑level orchestration: updates, logic, delegation to helpers."""
from __future__     import annotations

import time, cv2
from typing         import List, Optional
from core.engine.Board   import Board
from core.pieces.Piece   import Piece
from core.engine.Command import Command
from core.engine.events  import EventBus, GameStarted, GameEnded,PieceTaken,ErrorPlayed
from client.graphics.img   import Img
from pathlib        import Path
import cv2
from shared.constants import PIECE_VALUE,DIRS
from pathlib        import Path

...


# ---------------------------------------------------------------------------
class Game:
    """
    Main game controller: coordinates all game logic, input, events, and UI updates.
    """

    def __init__(self, pieces: List[Piece], board: Board):
        self.pieces  = pieces
        self.board   = board
        self.background_img = None
        self.final_img = None
        self.running = True



        self.white_cursor = [7, 4]
        self.black_cursor = [0, 4]

        self.white_last_dir = (0, 0)
        self.black_last_dir = (0, 0)
        self.from_cell  = {"WHITE": None, "BLACK": None}
        self.from_piece = {"WHITE": None, "BLACK": None}

        self.white_pieces = [p for p in pieces if self._is_white_piece(p)]
        self.black_pieces = [p for p in pieces if self._is_black_piece(p)]
        self.white_king   = next(p for p in self.white_pieces if p.piece_id.startswith("K"))
        self.black_king   = next(p for p in self.black_pieces if p.piece_id.startswith("K"))

        self.white_selected_index = 0
        self.black_selected_index = 0

        self.move_history = {"WHITE": [], "BLACK": []}
        self.command_history = []
        self.game_start_ms = int(time.time() * 1000)

        self.future_cells: dict[tuple[int,int], dict] = {}

        self.board.game = self 

        
        self.bus = EventBus()
        # from client.ui.move_log_ui import MoveLogUI

        print(f"Game initialized – {len(pieces)} total pieces")
        self.bus.publish(GameStarted("White", "Black"))


    # ─── basic helpers (unchanged) ────────────────────────────────────────

    def _is_white_piece(self, piece: Piece) -> bool:
        color = getattr(piece, "color", "").lower()
        pid   = getattr(piece, "piece_id", "").lower()
        if color == "white" or pid.startswith(("kw", "qw", "rw", "bw", "nw", "pw")):
            return True
        if color == "black" or pid.startswith(("kb", "qb", "rb", "bb", "nb", "pb")):
            return False
        return self.pieces.index(piece) < len(self.pieces) // 2


    def _is_black_piece(self, piece: Piece) -> bool:
        return not self._is_white_piece(piece)

    def game_time_ms(self) -> int:
        return int(time.monotonic() * 1000)

    def clone_board(self) -> Board:
        return self.board.clone()


    def start(self):
        """Initialize all pieces (used for tests instead of run())."""
        self.game_start_ms = self.game_time_ms()
        start_ms = self.game_time_ms()
        for p in self.pieces:
            p.reset(start_ms)


    def _is_blocked_by_ally(self, piece: Piece) -> bool:
        if getattr(piece, "can_jump_over_allies", False):
            return False 

        if not hasattr(piece.current_state.physics, "_path"):
            return False

        path = piece.current_state.physics._path
        my_team = self.white_pieces if piece in self.white_pieces else self.black_pieces
        allies_cells = {ally.get_cell() for ally in my_team if ally != piece and not ally.is_captured}

        for cell in path[1:]: 
            if cell in allies_cells:
                return True

        return False

    # ─── main loop ────────────────────────────────────────────────────────
   
   
    def run(self):
        """
        Main game loop that continuously updates the game state and processes input.
        Terminates when game is finished or window is closed.
        """

        self.game_start_ms = self.game_time_ms()
        self.input.start()
        start_ms = self.game_time_ms()
        for p in self.pieces:
            p.reset(start_ms)

        while not self._is_win() and self.running:
            now = self.game_time_ms()
            for p in self.pieces:
                
                p.update(now)

            while not self.input.queue.empty():
                player, key = self.input.queue.get()
                self._process_input(player, key)

            ui.draw(self)      
            if not ui.show(self):
                break

            self._resolve_collisions()
            time.sleep(0.016)

        self._announce_win()
        cv2.destroyAllWindows()

    def _move_cursor(self, cursor: list[int], dr: int, dc: int, player: str):
        r, c = cursor
        r = max(0, min(self.board.H_cells - 1, r + dr))
        c = max(0, min(self.board.W_cells - 1, c + dc))
        cursor[0], cursor[1] = r, c

        if player == 'WHITE':
            self.white_last_dir = (dr, dc)
        else:
            self.black_last_dir = (dr, dc)

    def _piece_at(self, r: int, c: int) -> Piece | None:
        return next((p for p in self.pieces
                     if (not p.is_captured) and
                        p.current_state.physics.get_current_cell() == (r, c)), None)

    def _process_input(self, player: str, key: str):

        now  = self.game_time_ms()
        cur_cursor  = self.white_cursor if player == 'WHITE' else self.black_cursor
        from_cell   = self.from_cell[player]
        from_piece  = self.from_piece[player]

        if key in DIRS:
            dr, dc = DIRS[key]
            self._move_cursor(cur_cursor, dr, dc, player)
            return

        if (player == 'WHITE' and key != 'ENTER') or \
           (player == 'BLACK' and key != 'space'):
            return

        r, c = cur_cursor
        piece_here = self._piece_at(r, c)
        my_team = self.white_pieces if player == 'WHITE' else self.black_pieces

        if from_cell is None:
            if piece_here and piece_here in my_team:
                self.from_cell[player] = (r, c)
                self.from_piece[player] = piece_here
            else:
                self.bus.publish(ErrorPlayed(now, "no piece to select", ""))
            return

        if piece_here and piece_here in my_team and (r, c) != from_cell:
            self.from_cell[player] = (r, c)
            self.from_piece[player] = piece_here
            return

        dest = (r, c)
        legal_dests = from_piece.current_state.moves.get_moves(*from_cell)

        if dest == from_cell:
            cmd = Command.create_jump_command(
                piece_id  = from_piece.piece_id,
                positions = [from_cell],
                timestamp = now,
                player_id = player,
            )
            print(f"Player {player} issued vertical JUMP: {cmd}")
            if from_piece.on_command(cmd, now, self):
                self._record_move(player, cmd)
                self.command_history = getattr(self, "command_history", [])
                self.command_history.append(cmd)
            else:
                print(f"Illegal jump command from {from_cell} to {dest}")
                self.bus.publish(ErrorPlayed(now, "illegal jump", from_piece.piece_id))

            self.command_history.append(cmd)
            self.from_cell[player] = None
            self.from_piece[player] = None
            return

        # error
        if dest not in legal_dests:
            self.bus.publish(ErrorPlayed(now, "illegal move", from_piece.piece_id))
            return

        # check 
        if not from_piece.can_jump_over_allies:
            fr = from_cell
            to = dest
            dr = to[0] - fr[0]
            dc = to[1] - fr[1]
            steps = max(abs(dr), abs(dc))
            dr = 0 if dr == 0 else dr // abs(dr)
            dc = 0 if dc == 0 else dc // abs(dc)

            blocked_cells = {p.get_cell() for p in self.pieces if p != from_piece and not p.is_captured}
            for step in range(1, steps):
                cell = (fr[0] + dr * step, fr[1] + dc * step)
                if cell in blocked_cells:

                    self.bus.publish(ErrorPlayed(now, "blocked mid-path", from_piece.piece_id))
                    return

        reservation = self.future_cells.get(dest)

        if reservation and reservation["player"] == player:
            self.bus.publish(ErrorPlayed(now, "blocked mid-path", from_piece.piece_id))
            print(f"Player {player} already reserved {dest} for {reservation['piece_id']}")
            return  # already reserved by same player


        # correct command
        cmd = Command.create_move_command(
            piece_id  = from_piece.piece_id,
            from_pos  = from_cell,
            to_pos    = dest,
            timestamp = now,
            player_id = player
        )


        self.future_cells[dest] = {"piece_id": from_piece.piece_id, "player": player}

        print(f"Player {player} issued command: {cmd}")  
        executed = from_piece.on_command(cmd, now, self)

        if executed:
            self.command_history = getattr(self, "command_history", [])
            self.command_history.append(cmd)
            self._record_move(player, cmd)
        else:
            self.future_cells.pop(dest, None)


        self.from_cell[player] = None
        self.from_piece[player] = None

  
    def _resolve_collisions(self):
        """Check for collisions on same cells, resolve by arrival time."""
        collisions = {}
        for piece in self.pieces:
            if piece.is_captured or piece.current_state.physics.is_jumping:
                continue
            cell = piece.current_state.get_cell()
            collisions.setdefault(cell, []).append(piece)

        for pieces_in_cell in collisions.values():
            if len(pieces_in_cell) <= 1:
                continue
            colors = {"WHITE" if p in self.white_pieces else "BLACK" for p in pieces_in_cell}
            if len(colors) == 1:
                continue
            pieces_in_cell.sort(
                key=lambda p: p.current_state.state_start_time or 0,
                reverse=True
            )
            winner = pieces_in_cell[0]
            for loser in pieces_in_cell[1:]:
                if (winner in self.white_pieces and loser in self.black_pieces) or \
                   (winner in self.black_pieces and loser in self.white_pieces):
                    loser.is_captured = True
                    cell = loser.current_state.get_cell()
                    # שחרור הזמנות
                    self.future_cells = {
                        c: r for c, r in self.future_cells.items()
                        if r["piece_id"] != loser.piece_id
                    }
                    by_color = "WHITE" if winner in self.white_pieces else "BLACK"
                    value = PIECE_VALUE.get(loser.piece_id[0].upper(), 0)
                    self.bus.publish(PieceTaken(loser.piece_id, cell, by_color, value))
                    # הוספת לוג
                    from core.game.move_history import fmt_elapsed
                    ts = fmt_elapsed(self, self.game_time_ms())
                    nota = f"CAPTURE {loser.piece_id} at {cell}"
                    self.move_history[by_color].append((ts, nota))


                    

                   


    # ─── win condition ──────────────────────────────────────────────────────

    def _is_win(self) -> bool:
        """
        Return True if a king has been captured (after a short delay).

        Server/client agnostic:
        - When a king is first detected as captured, we stamp the time and publish
        GameEnded with the WINNER (not the captured color).
        - After ~2 seconds grace period (to let last animations/events finish),
        we return True to signal the loop to terminate (in monolith mode).
        """
        kings = {"WHITE": self.white_king, "BLACK": self.black_king}
        for captured_color, king in kings.items():
            if king.is_captured:
                winner = "BLACK" if captured_color == "WHITE" else "WHITE"
                if not hasattr(self, "_win_timer_ms"):
                    self._win_timer_ms = self.game_time_ms()
                    print(f"{captured_color} king captured – {winner} wins (finishing in 2s)…")
                    # ✅ publish the WINNER
                    self.bus.publish(GameEnded(winner))
                    return False
                # grace period for final animations / network delivery
                if self.game_time_ms() - self._win_timer_ms > 2000:
                    return True
                return False
        return False


    # ---------------------------------------------------------
    # Game – Move history helpers
    # ---------------------------------------------------------  
    def _announce_win(self):
        """Determine and announce the winner (or draw)."""
        white_alive = self.get_white_alive_pieces()
        black_alive = self.get_black_alive_pieces()
        if not white_alive and black_alive:
            print(" Black wins!")
        elif not black_alive and white_alive:
            self.bus.publish(GameEnded('WHITE'))
            print(" White wins!")
        elif not white_alive and not black_alive:
            print(" Draw – no winner!")
        else:
            self.bus.publish(GameEnded('the game ended'))
            print(" Game ended")

    # ─── move‑history hook -------------------------------------------------
    def _record_move(self, player: str, cmd: Command):
        record_move(self, player, cmd)
    # ----------------------------------------------------------
    def get_white_alive_pieces(self):
        return [p for p in self.white_pieces if not p.is_captured]

    def get_black_alive_pieces(self):
        return [p for p in self.black_pieces if not p.is_captured]

    def get_selected_white_piece(self):
        alive = self.get_white_alive_pieces()
        if not alive:
            return None
        return alive[self.white_selected_index % len(alive)]

    def get_selected_black_piece(self):
        alive = self.get_black_alive_pieces()
        if not alive:
            return None
        return alive[self.black_selected_index % len(alive)]

# ----------------------------------------------------------

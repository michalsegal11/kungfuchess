"""client/input_handler – pygame-driven input → Commands (no global hook)."""
# ===================================================================
from __future__ import annotations
import queue, time
from typing import Tuple
from core.engine.Command import Command

_DIRS = {
    "UP": (-1, 0), "DOWN": (1, 0), "LEFT": (0, -1), "RIGHT": (0, 1),
    "w": (-1, 0), "s": (1, 0), "a": (0, -1), "d": (0, 1),
}

class InputHandler:
    """Queues keystrokes from the pygame thread and turns them into Commands."""
    def __init__(self, net_client, model):
        self.net = net_client
        self.model = model
        self.queue: "queue.Queue[Tuple[str,str]]" = queue.Queue()

    # pygame main loop calls this on KEYDOWN
    def enqueue(self, player: str, key: str) -> None:
        self.queue.put((player, key))

    def pump_commands(self):
        while not self.queue.empty():
            player, key = self.queue.get()
            self._process(player, key)

    def _process(self, player: str, key: str):
        # UX guard (השרת בכל מקרה חוסם אחרי GameEnded)
        if getattr(self.model, "game_over", False):
            return

        now = int(time.time() * 1000)
        cur = self.model.white_cursor if player == "WHITE" else self.model.black_cursor
        from_cell = self.model.from_cell[player]
        from_piece = self.model.from_piece[player]

        if key in _DIRS:
            dr, dc = _DIRS[key]
            cur[0] = max(0, min(self.model.board_rows - 1, cur[0] + dr))
            cur[1] = max(0, min(self.model.board_cols - 1, cur[1] + dc))
            return

        if (player == "WHITE" and key != "ENTER") or (player == "BLACK" and key != "space"):
            return

        r, c = cur
        piece = self.model.get_piece_at((r, c))
        if piece and (piece.get("state") != "idle" or self.model.moving.get(piece["id"], False)):
            return  # cannot select moving piece

        if from_cell is None:
            if piece and piece["id"][1] == ("W" if player == "WHITE" else "B"):
                self.model.from_cell[player] = (r, c)
                self.model.from_piece[player] = piece
            return

        dest = (r, c)
        pid = self.model.from_piece[player]["id"]
        if dest == from_cell:
            cmd = Command.create_jump_command(pid, [from_cell], now, player)
        else:
            cmd = Command.create_move_command(pid, from_cell, dest, now, player)
        self.net.send_command(cmd)
        self.model.from_cell[player] = None
        self.model.from_piece[player] = None

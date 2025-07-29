# ============================ move_history.py ============================
"""
Move history recording and notation conversion.
"""
from __future__ import annotations
from .constants import PIECE_LETTER


def cell_to_sq(rc: tuple[int, int]) -> str:
    """Convert (row, col) to standard algebraic square like 'e4'."""
    r, c = rc
    return chr(ord('a') + c) + str(r + 1)

def fmt_elapsed(game, now_ms: int) -> str:
    """Return formatted elapsed time from start (MM:SS.ss)."""
    m, s = divmod((now_ms - game.game_start_ms) // 10, 6000)
    return f"{int(m):02}:{(s / 100):05.2f}"

def notation_from_cmd(cmd: Command) -> str:
    if cmd.type == "Move":
        src, dst = cmd.params
        return f"MOVE {cmd.piece_id}: {src} -> {dst}"
    elif cmd.type == "Jump":
        src = cmd.params[0]
        return f"JUMP {cmd.piece_id}: at {src}"
    elif cmd.type == "Capture":
        _, dst, _ = cmd.params
        return f"CAPTURE at {dst}"
    return f"{cmd.type}"

def record_move(game, player: str, cmd):
    """Append timestamped move to player history and publish event."""
    if game.game_start_ms is None:
        return
    nota = notation_from_cmd(cmd)
    ts   = fmt_elapsed(game, cmd.timestamp)
    game.move_history[player].append((ts, nota))

    from engine.events import MovePlayed
    game.bus.publish(MovePlayed(cmd.timestamp, nota, player))

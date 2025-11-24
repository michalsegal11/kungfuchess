"""Command – a single, immutable game action.

Every action that happens on the board (moving a piece, capturing, castling …)
is represented by a *Command* object.  Commands are **data only** – they don’t
execute anything by themselves – which makes them perfect for logging,
re‑playing, undo / redo, or sending over the network.

▶  Typical life‑cycle

    cmd = Command.move("RW_0_0", (1,0), (3,0), player="WHITE")
    game.apply(cmd)      # some system consumes / executes it

The class deliberately stays **light‑weight** – no inheritance hierarchy, no
side‑effects – just validation and a couple of helpers for (de)serialisation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import json, time, copy
from shared.constants import DIRS
import time


# ---------------------------------------------------------------------------
#   Constants             
# ---------------------------------------------------------------------------

#: all the verb types we currently support
VALID_TYPES = {
    "Move", "Jump", "Attack", "Capture",
    "Castle", "EnPassant", "Promote", "Reset",
}

# ---------------------------------------------------------------------------
#  Helpers               
# ---------------------------------------------------------------------------

def _now_ms() -> int:
    """Current monotonic time in **milliseconds** – handy for stamps."""
    return int(time.time() * 1000)



# ---------------------------------------------------------------------------
#  Command               
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class Command:
    """An immutable, validated DTO representing one game action."""

    timestamp: int                        # ms since epoch / game‑start
    piece_id: str                         # e.g. "RW_0_0"
    type: str                             # see :data:`VALID_TYPES`
    params: List[Any]                     # payload – meaning depends on *type*

    player_id: Optional[str] = None       # "WHITE" / "BLACK" (if relevant)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # ---------------------------------------------------------------------
    #  Validation
    # ---------------------------------------------------------------------
    def __post_init__(self):
        if self.type not in VALID_TYPES:
            raise ValueError(f"Illegal command type: {self.type!r}. Valid: {VALID_TYPES}")
        if self.timestamp < 0:
            raise ValueError("timestamp must be ≥ 0")
        if not self.piece_id:
            raise ValueError("piece_id cannot be empty")
        if not isinstance(self.params, list):
            raise TypeError("params must be a list")

    # ---------------------------------------------------------------------
    #  Canonical constructors – clearer than calling the dataclass directly
    # ---------------------------------------------------------------------
    @classmethod
    def move(cls, piece_id: str, from_pos: Tuple[int, int] | str, to_pos: Tuple[int, int] | str,
             *, player: Optional[str] = None, ts: Optional[int] = None) -> "Command":
        """Create a *Move* command."""
        return cls(ts or _now_ms(), piece_id, "Move", [from_pos, to_pos], player)

    @classmethod
    def capture(cls, piece_id: str, from_pos: Tuple[int, int] | str, to_pos: Tuple[int, int] | str,
                captured_id: str, *, player: Optional[str] = None, ts: Optional[int] = None) -> "Command":
        """Create a *Capture* command."""
        return cls(ts or _now_ms(), piece_id, "Capture", [from_pos, to_pos, captured_id], player,
                   metadata={"captured_piece": captured_id})

    @classmethod
    def create_move_command(cls,
                            piece_id: str,
                            from_pos: Any,
                            to_pos  : Any,
                            timestamp : Optional[int] = None,
                            player_id : Optional[str] = None) -> "Command":
        return cls(timestamp or int(time.time()*1000),
                   piece_id, "Move",
                   [from_pos, to_pos],
                   player_id,
                   {"move_type": "normal"})

    @classmethod
    def create_capture_command(cls,
                               piece_id: str,
                               from_pos: Any,
                               to_pos  : Any,
                               captured_piece_id: str,
                               timestamp : Optional[int] = None,
                               player_id : Optional[str] = None) -> "Command":
        return cls(timestamp or int(time.time()*1000),
                   piece_id, "Capture",
                   [from_pos, to_pos, captured_piece_id],
                   player_id,
                   {"captured_piece": captured_piece_id})

    @classmethod
    def create_jump_command(cls,
                            piece_id: str,
                            positions: List[Any],
                            timestamp : Optional[int] = None,
                            player_id : Optional[str] = None) -> "Command":
        return cls(timestamp or int(time.time()*1000),
                   piece_id, "Jump",
                   positions,
                   player_id,
                   {"jump_sequence": len(positions)-1})
 

    # ---------------------------------------------------------------------
    #  Utilities
    # ---------------------------------------------------------------------
    def clone(self) -> "Command":
        """Deep‑copy – cheap thanks to dataclass *slots*."""
        return copy.deepcopy(self)

    # ------------ serialisation -----------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        """Plain dict – convenient for JSON or DB."""
        return {
            "timestamp": self.timestamp,
            "piece_id" : self.piece_id,
            "type"     : self.type,
            "params"   : self.params,
            "player_id": self.player_id,
            "metadata" : self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Command":
        return cls(**data)

    # JSON helpers – one‑liners on top of *dict* methods
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, s: str) -> "Command":
        return cls.from_dict(json.loads(s))

    # ---------------------------------------------------------------------
    #  Display helpers (debug / logs)
    # ---------------------------------------------------------------------
    def _fmt_time(self) -> str:
        secs = self.timestamp / 1000
        m, s = divmod(secs, 60)
        return f"{int(m):02}:{s:05.2f}"

    def __str__(self) -> str:  # human‑friendly
        params = ", ".join(map(str, self.params))
        plr    = f" player={self.player_id}" if self.player_id else ""
        return f"[{self._fmt_time()}] {self.type} {self.piece_id} → {params}{plr}"

    def __repr__(self) -> str:  # unambiguous
        return ("Command("
                f"timestamp={self.timestamp}, piece_id={self.piece_id!r}, "
                f"type={self.type!r}, params={self.params!r}, "
                f"player_id={self.player_id!r})")


# --------------------------------------------------------------------
# helper: build Command from keyboard (client side)
# --------------------------------------------------------------------
       # {'UP':(-1,0), ...}

    @staticmethod
    def from_key(player: str, key: str, projection: dict):
        """
        Very-minimal conversion of keyboard → Command:
        - WHITE uses ENTER to move pawn forward
        - BLACK uses SPACE to move pawn forward
        """
        key = key.upper()
        if (player == "WHITE" and key != "ENTER") or \
        (player == "BLACK" and key != "SPACE"):
            return None                     

        target = "PW" if player == "WHITE" else "PB"
        for piece in projection.values():
            if piece.piece_id.startswith(target) and not piece.is_captured:
                src = piece.current_state.get_cell()
                dr  = -1 if player == "WHITE" else +1
                dst = (src[0] + dr, src[1])
                ts  = int(time.time()*1000)

                return Command.create_move_command(
                    piece_id  = piece.piece_id,
                    from_pos  = src,
                    to_pos    = dst,
                    timestamp = ts,
                    player_id = player,
                )
        return None


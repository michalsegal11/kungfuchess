# ===================================================================
# File: server/protocol.py   – authoritative ↔ client serialisation
# ===================================================================
from __future__ import annotations
import time
from typing import Dict, Any
from dataclasses import asdict, is_dataclass

from shared.command_dto    import to_dict as cmd_to_dict, from_dict as cmd_from_dict
from shared.message_schema import Message

# -------------------------------------------------------------------
# Encoding helpers ---------------------------------------------------

def encode_command(cmd) -> Dict[str, Any]:
    
    """Wrap a Command instance as a Wire‑Message dict."""
    return Message("command", cmd_to_dict(cmd), int(time.time()*1000)).to_dict()


def encode_event(evt) -> Dict[str, Any]:

    """Dataclass → dict  (adds _event_type)."""
    payload = asdict(evt) if is_dataclass(evt) else dict(evt)
    payload.setdefault("_event_type", type(evt).__name__)
    return Message("event", payload, int(time.time()*1000)).to_dict()


def encode_state(game) -> Dict[str, Any]:

    """Server snapshot → dict for initial sync / resync."""
    return {
        "board": {"rows": game.board.H_cells, "cols": game.board.W_cells},
        "pieces": [
            {
                "id":        p.piece_id,
                "cell":      p.current_state.physics.get_current_cell(),
                "pixel":     p.current_state.physics.current_pixel_pos,
                "state":     p.current_state.state_name,      #  ← NEW
                "captured":  bool(getattr(p, "is_captured", False)),
            }
            for p in game.pieces
        ],
        "ts": game.game_time_ms(),
    }

# -------------------------------------------------------------------
# Helper – list→tuple for JSON round‑tripping ------------------------

def _lt(obj):
    if isinstance(obj, list):
        if len(obj) == 2 and all(isinstance(x, int) for x in obj):
            return tuple(obj)
        return [_lt(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _lt(v) for k, v in obj.items()}
    return obj

# -------------------------------------------------------------------
# Decoder -------------------------------------------------------------

def decode_message(data: Dict[str, Any]):
    msg = Message.from_dict(data)
    if msg.type == "command":
        cmd = cmd_from_dict(msg.payload)
        cmd.params = _lt(getattr(cmd, "params", []))
        return cmd
    if msg.type == "event":
        return _lt(msg.payload)
    return msg.type
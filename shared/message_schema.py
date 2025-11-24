# =============================================================
# Filename: shared/message_schema.py
# =============================================================
"""message_schema – Canonical envelope passed over the WebSocket.

We keep the over‑the‑wire payload *minimal* but still future‑proof by
namespacing the content under a **type** field that tells the recipient
how to interpret *payload* (command, event, system‑ping …).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Dict, Any
# ---------------------------------------------------------------------------

MessageType = Literal["command", "event", "state", "ping", "pong", "error"]


@dataclass(slots=True)
class Message:
    """Single frame exchanged between server and client."""

    type: MessageType     # what is inside *payload*
    payload: Dict[str, Any]
    ts: int               # unix‑epoch‑ms when the message was created

    # ---------------------------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        return {"type": self.type, "payload": self.payload, "ts": self.ts}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Message":
        return cls(d["type"], d["payload"], d["ts"])
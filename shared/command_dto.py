# =============================================================
# Filename: shared/command_dto.py
# =============================================================

"""command_dto – Pure-function helpers to (de)serialise
:class:`core.engine.Command.Command` for transport over the wire.

All conversions happen on simple *dict* objects so the payload can be
JSON-encoded cheaply (no custom JSONEncoder required).
"""
from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any, Dict

# NOTE:  The server process keeps the *authoritative* copy of Command under
# *server/core/engine/Command.py*.  The client – which does **not** import
# the heavy game-logic package – only sees the JSON representation.


try:
    from core.engine.Command import Command  # server side
except ModuleNotFoundError:
    # Fallback for client side: define a *very* thin shim so we can still
    # build a Command object from incoming messages (for rendering / logs).
    class _MiniCommand(dict):  # pragma: no cover – client stub only
        """Minimal read-only stand-in that quacks like the real Command."""
        def to_dict(self) -> Dict[str, Any]:
            return dict(self)
        @classmethod
        def from_dict(cls, data: Dict[str, Any]):
            return cls(**data)
    Command = _MiniCommand  # type: ignore


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def to_dict(cmd: "Command") -> Dict[str, Any]:
    """Convert *Command* → plain dict ready for ``json.dumps``."""
    return cmd.to_dict() if hasattr(cmd, "to_dict") else asdict(cmd)


def from_dict(data: Dict[str, Any]) -> "Command":
    """Inverse of :func:`to_dict` – create *Command* from JSON‑decoded dict."""
    return Command.from_dict(data)  # type: ignore


def to_json(cmd: "Command", *, indent: int | None = None) -> str:
    """Convenience wrapper – serialise directly to a JSON string."""
    return json.dumps(to_dict(cmd), ensure_ascii=False, indent=indent)


def from_json(s: str | bytes | bytearray) -> "Command":
    return from_dict(json.loads(s))
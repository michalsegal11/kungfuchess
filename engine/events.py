# events.py
from collections import defaultdict
from dataclasses import dataclass
from typing import Callable, Dict, List, Type, Any

class EventBus:
    def __init__(self):
        self._subs: Dict[Type, List[Callable[[Any], None]]] = defaultdict(list)

    def subscribe(self, event_type: Type, cb: Callable[[Any], None]):
        self._subs[event_type].append(cb)

    def publish(self, event: Any):
        for cb in self._subs[type(event)]:
            cb(event)

# -------- basic events--------
@dataclass
class MovePlayed:  time_ms: int; move: str; color: str
@dataclass
class PieceTaken:
    piece_id: str
    cell: tuple[int, int]
    by_color: str
    value: int         # ← הוספה!
@dataclass
class JumpPlayed:  time_ms: int; color: str
@dataclass
class ErrorPlayed: time_ms: int; reason: str; piece: str
@dataclass
class GameStarted: white: str;   black: str
@dataclass
class GameEnded:   winner: str | None

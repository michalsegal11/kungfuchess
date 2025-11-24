# =============================================================
# client/model.py – client-side projection of game state
# =============================================================
from __future__ import annotations
from typing import Dict, Tuple, Any, Iterable
from math import hypot

Cell = Tuple[int,int]
CELL = 64

class ClientModel:
    """Keeps the current board projection + UI state for the client."""

    def __init__(self):
        self.board_rows = 8
        self.board_cols = 8
        self.ts = 0
        self.pieces : Dict[str, Dict[str,Any]] = {}
        self.moving : Dict[str,bool] = {}
        self.player_names = {"WHITE": "", "BLACK": ""}

        # UI cursors & selection
        self.white_cursor=[7,4]; self.black_cursor=[0,4]
        self.from_cell={"WHITE":None,"BLACK":None}
        self.from_piece={"WHITE":None,"BLACK":None}
        self.last_pixel: Dict[str, tuple[float,float]] = {}
        self.last_state_ts: Dict[str, int] = {}

        # 🔒 Game over latch (client-side UX; server is authoritative)
        self.game_over: bool = False
        self.winner: str | None = None

    # ---------- sync ----------
    def load_snapshot(self, snap:dict):
        self.board_rows=snap["board"]["rows"]
        self.board_cols=snap["board"]["cols"]
        self.ts=snap["ts"]

        self.pieces={ p["id"]:p for p in snap["pieces"] }
        for p in snap["pieces"]:
            pid = p["id"]
            self.pieces.setdefault(pid, {})
            self.pieces[pid].update({
                "id": pid,
                "cell": tuple(p["cell"]),
                "pixel": tuple(p["pixel"]),
                "state": p["state"],
                "captured": p["captured"],
            })
            prev = self.last_pixel.get(pid, p["pixel"])
            dist = hypot(p["pixel"][0]-prev[0], p["pixel"][1]-prev[1])
            self.moving[pid] = dist >= 0.5
            self.last_pixel[pid] = p["pixel"]
            self.pieces[pid]["state"] = p["state"]

    def apply_event(self, evt: dict):
        et = evt.get("_event_type")
        # print(f"Received event type: {et}")  # debug
        if et == "PieceTaken":
            vid = evt.get("victim_id") or evt.get("piece_id")
            if vid in self.pieces:
                self.pieces[vid]["captured"] = True

        elif et == "StateChanged":
            pid = evt["piece_id"]
            ts  = evt.get("timestamp", 0)
            if pid in self.pieces:
                current_ts = self.last_state_ts.get(pid, -1)
                if ts >= current_ts:
                    self.pieces[pid]["state"] = evt["new_state"]
                    self.last_state_ts[pid] = ts

        elif et == "GameStarted":
            self.player_names["WHITE"] = evt.get("white", "")
            self.player_names["BLACK"] = evt.get("black", "")

        elif et == "GameEnded":
            # Freeze locally (server will also reject further commands)
            self.game_over = True
            self.winner = evt.get("winner")

    # ---------- helpers ----------
    def get_piece_at(self, cell:Cell):
        for p in self.pieces.values():
            if not p.get("captured") and tuple(p["cell"])==cell:
                return p
        return None

    def alive_pieces(self)->Iterable[Dict[str,Any]]:
        return (p for p in self.pieces.values() if not p.get("captured"))

    @property
    def board_pix(self) -> tuple[int, int]:
        return (self.board_cols * CELL, self.board_rows * CELL)

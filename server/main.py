# =============================================================
# Filename: server/main.py  (HEADLESS)
# =============================================================
"""Authoritative Kungfu-Chess WebSocket server – *logic only* (no graphics)."""

from __future__ import annotations
import sys, pathlib, importlib, asyncio, json, signal, csv, types
from typing import Any, Dict, List, Set

import websockets
from websockets import WebSocketServerProtocol

# ───────────── bootstrap PYTHONPATH ───────────────────────────
ROOT = pathlib.Path(__file__).resolve().parents[1]      # …/It1_interfaces
PROJECT_ROOT = ROOT.parent                              # …/CTD25
SERVER_DIR   = ROOT / "server"
CLIENT_DIR   = ROOT / "client"

for p in (SERVER_DIR, CLIENT_DIR, PROJECT_ROOT):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

# ───────────── inject no-op graphics stubs ────────────────────
from server.graphics_stub import Graphics, ImgStub
g_mod = types.ModuleType("client.graphics.Graphics"); g_mod.Graphics = Graphics
sys.modules["client.graphics.Graphics"] = g_mod
img_mod = types.ModuleType("client.graphics.img"); img_mod.Img = ImgStub
sys.modules["client.graphics.img"] = img_mod

sys.modules.setdefault("core", importlib.import_module("server.core"))

# ───────────── imports (logic only) ───────────────────────────
from core.engine.Board        import Board
from core.pieces.PieceFactory import PieceFactory
from core.engine.Command      import Command
from core.game.game           import Game
from core.engine              import events as ev
from protocol                 import decode_message, encode_event, encode_state

# ───────────── global state ───────────────────────────────────
GAME: Game | None = None
CONNECTED: Set[WebSocketServerProtocol] = set()
PLAYERS:   Dict[str, Dict[str, Any]]    = {}   # color ➜ {"name": str, "ws": ws}
GAME_STARTED: bool = False
GAME_OVER:   bool = False                        # ← NEW: נעילת סוף‑משחק סמכותית

PIECE_BY_ID: Dict[str, Any] = {}

graphics_root = PROJECT_ROOT / "pieces"
csv_path      = PROJECT_ROOT / "assets/board.csv"

# ───────────── helpers ────────────────────────────────────────
async def _tick_game(fps: float = 60.0) -> None:
    """
    Server-side game loop:
    - advances piece animations / physics
    - resolves collisions (including captures)
    - checks the win condition regularly (king captured)
    """
    global GAME_OVER
    dt = 1.0 / fps
    while True:
        now = GAME.game_time_ms()
        for p in GAME.pieces:
            p.update(now)

        GAME._resolve_collisions()

        # אם זוהה ניצחון בלולאת הטיק – ננעל
        try:
            if not GAME_OVER and GAME._is_win():          # ← NEW
                GAME_OVER = True                          # ← NEW
        except Exception as e:
            print("[WARN] _is_win check failed:", e)

        await asyncio.sleep(dt)

async def _snapshot_loop(interval: float = 1.0/60) -> None:
    while True:
        if CONNECTED:
            snap = json.dumps({"type": "state", "payload": encode_state(GAME)})
            await asyncio.gather(*(ws.send(snap) for ws in list(CONNECTED)),
                                 return_exceptions=True)
        await asyncio.sleep(interval)

# ───────────── socket handler ─────────────────────────────────
async def handle_socket(ws: WebSocketServerProtocol) -> None:
    global GAME_STARTED, GAME_OVER
    CONNECTED.add(ws)
    print("🔗 client connected:", len(CONNECTED))
    try:
        # סנאפשוט ראשוני
        await ws.send(json.dumps({"type": "state", "payload": encode_state(GAME)}))

        async for raw in ws:
            data = json.loads(raw)
            tp   = data.get("type")

            # -------------------- JOIN --------------------
            if tp == "join":
                name  = (data["payload"].get("name") or "").strip() or "Anonymous"
                color = (data["payload"].get("color") or "").upper()
                if not color:
                    await ws.send(json.dumps({"type":"error","payload":{"err":"missing color"}}))
                    continue
                if color in PLAYERS:   # צבע תפוס
                    await ws.send(json.dumps({"type":"error",
                                              "payload":{"err":"color taken"}}))
                    continue

                PLAYERS[color] = {"name": name, "ws": ws}
                print(f"[LOBBY] {name} joined as {color}")
                await _broadcast_players()

                # נתחיל משחק כשיש שני צבעים
                if (not GAME_STARTED
                        and PLAYERS.get("WHITE")
                        and PLAYERS.get("BLACK")):
                    evt = ev.GameStarted(
                        white=PLAYERS["WHITE"]["name"],
                        black=PLAYERS["BLACK"]["name"]
                    )
                    print("[SERVER] GameStarted:", evt.white, "vs", evt.black)
                    GAME.bus.publish(evt)
                    GAME_STARTED = True
                    GAME_OVER = False                      # ← NEW: איפוס נעילה בתחילת משחק
                continue

            # -------------------- COMMAND -----------------
            msg = decode_message(data)
            if isinstance(msg, Command):
                # 🔒 סמכותי: דוחים כל פקודה אחרי סיום משחק
                if GAME_OVER:                               # ← NEW
                    await ws.send(json.dumps({"type":"error","payload":{"err":"game over"}}))
                    continue

                piece = PIECE_BY_ID.get(msg.piece_id)
                if piece:
                    piece.on_command(msg, GAME.game_time_ms(), GAME)
                else:
                    await ws.send(json.dumps({"type": "error",
                                              "payload": {"err": "bad piece_id"}}))
    finally:
        # ניתוק
        CONNECTED.discard(ws)
        for clr, info in list(PLAYERS.items()):
            if info["ws"] is ws:
                del PLAYERS[clr]
        await _broadcast_players()
        print("⛔ client disconnected:", len(CONNECTED))

# ───────────── event broadcaster ──────────────────────────────
async def _broadcast_events() -> None:
    global GAME_OVER
    q: asyncio.Queue = asyncio.Queue()
    for cls in (ev.MovePlayed, ev.JumpPlayed, ev.PieceTaken,
                ev.ErrorPlayed, ev.GameStarted, ev.GameEnded, ev.StateChanged):
        GAME.bus.subscribe(cls, q.put_nowait)

    while True:
        evt = await q.get()

        # כשהמשחק נגמר – ננעלים סמכותית
        if isinstance(evt, ev.GameEnded):                   # ← NEW
            GAME_OVER = True                                # ← NEW

        if not CONNECTED:
            continue
        payload = json.dumps({"type": "event", "payload": encode_event(evt)})
        await asyncio.gather(*(ws.send(payload) for ws in list(CONNECTED)),
                             return_exceptions=True)

# ---- helper: broadcast current players לכל הקליינטים --------
async def _broadcast_players() -> None:
    payload = {"white": PLAYERS.get("WHITE", {}).get("name"),
               "black": PLAYERS.get("BLACK", {}).get("name")}
    msg = json.dumps({"type": "players", "payload": payload})
    if CONNECTED:
        await asyncio.gather(*(ws.send(msg) for ws in CONNECTED),
                             return_exceptions=True)

# ───────────── main bootstrap ─────────────────────────────────
async def main(host: str = "127.0.0.1", port: int = 8765) -> None:
    global GAME, PIECE_BY_ID, GAME_STARTED, GAME_OVER
    GAME_STARTED = False
    GAME_OVER    = False

    board   = Board(64, 64, 8, 8)
    factory = PieceFactory(board, graphics_root)
    pieces: List[Any] = []

    with csv_path.open(newline="", encoding="utf-8") as fh:
        for r, row in enumerate(csv.reader(fh)):
            for c, code in enumerate(row):
                code = code.strip()
                if code:
                    pieces.append(factory.create_piece(code, (r, c)))

    GAME = Game(pieces, board); board.game = GAME
    PIECE_BY_ID = {p.piece_id: p for p in pieces}

    async with websockets.serve(handle_socket, host, port,
                                ping_interval=20, ping_timeout=20, max_queue=32):
        print(f"🏁 Kungfu-Chess server listening on ws://{host}:{port}")
        asyncio.create_task(_tick_game())
        asyncio.create_task(_broadcast_events())
        asyncio.create_task(_snapshot_loop(1.0 / 60))
        await asyncio.Future()          # run forever

# ───────────── runner ────────────────────────────────────────
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    if sys.platform != "win32":
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, loop.stop)
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()

# =============================================================
# Filename: client/net.py
# =============================================================
"""net – Thin async WebSocket client for Kungfu‑Chess.

After connect, sends a JOIN with (name, color).
Queues all inbound messages so the pygame thread can poll them.
"""
from __future__ import annotations
import asyncio, json, threading, queue
import websockets
from typing import Any, Dict

from shared.command_dto import to_dict as cmd_to_dict
from shared.message_schema import Message

class NetClient:
    """Background thread → asyncio loop → WebSocket connection."""

    def __init__(self, model, my_name: str, my_color: str,
                 url: str = "ws://127.0.0.1:8765") -> None:
        self.model     = model
        self.my_name   = (my_name or "").strip() or "player"
        self.my_color  = (my_color or "ANY").upper()
        self.url       = url
        self._tx: "queue.Queue[Dict[str, Any]]" = queue.Queue()
        self.rx: "queue.Queue[Dict[str, Any]]" = queue.Queue()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)

    # --------------------------- API ----------------------------
    def start(self): self._thread.start()

    async def _send_join(self, ws):
        await ws.send(json.dumps({
            "type": "join",
            "payload": {"name": self.my_name, "color": self.my_color}
        }))

    def send_command(self, cmd):
        self._tx.put(Message("command", cmd_to_dict(cmd), 0).to_dict())

    # --------------------------- internals ----------------------
    async def _ws_loop(self):
        async with websockets.connect(self.url) as ws:
            print("🔗 connected to", self.url)
            await self._send_join(ws)

            async def _sender():
                while True:
                    msg = await asyncio.to_thread(self._tx.get)
                    await ws.send(json.dumps(msg))

            snd_task = asyncio.create_task(_sender())
            try:
                async for raw in ws:
                    try:
                        raw_msg = json.loads(raw)
                    except json.JSONDecodeError:
                        continue

                    # players list → update names on the model
                    if raw_msg.get("type") == "players":
                        payload = raw_msg.get("payload") or {}
                        self.model.player_names["WHITE"] = payload.get("white", "")
                        self.model.player_names["BLACK"] = payload.get("black", "")
                        print("[CLIENT] players:", self.model.player_names)
                        continue

                    self.rx.put(raw_msg)
            finally:
                snd_task.cancel("socket closed")

    def _run_loop(self):
        asyncio.run(self._ws_loop())

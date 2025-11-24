# =============================================================
# client/main.py – Pygame client (synced with NetClient & InputHandler)
# =============================================================
from __future__ import annotations
import sys, pathlib, importlib, pygame
from typing import Dict, Any, List

# ───────── bootstrap import path ─────────
ROOT = pathlib.Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT.parent
SERVER_DIR = ROOT / "server"
for p in (ROOT, PROJECT_ROOT, SERVER_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
if "core" not in sys.modules:
    sys.modules["core"] = importlib.import_module("server.core")

# ───────── imports ─────────
from client.net import NetClient
from client.model import ClientModel
from client.input_handler import InputHandler
from client.graphics.Graphics import Graphics


from client.ui.ui_pygame import GameUI
from client.ui.move_log_ui import MoveLogUI
from client.ui.score_ui import ScoreUI
from client.ui.overlay import Overlay
from client.ui.sound_fx import SoundFX
from client.ui.window_icon import set_window_icon
from client.ui.login_screen import LoginScreen

from core.engine.events import *
from shared.constants import *

# ───────── pygame init ─────────
pygame.init()
CELL = 64
BOARD_W = BOARD_H = CELL * 8
W, H = SIDE_W * 2 + PANEL_GAP * 2 + BOARD_W, 768
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Kungfu-Chess – Client")
set_window_icon("Kungfu-Chess – Client")
clock = pygame.time.Clock()

# ───────── Login (blocks until user picks name+color) ─────────
login  = LoginScreen(screen)
player_name, player_color = login.run()  # returns ("Michal", "WHITE"/"BLACK")

# ───────── Board Surface (background grid) ─────────
board_surf = pygame.Surface((BOARD_W, BOARD_H))
for r in range(8):
    for c in range(8):
        color = (230, 230, 230) if (r + c) % 2 == 0 else (70, 70, 70)
        pygame.draw.rect(board_surf, color, pygame.Rect(c * CELL, r * CELL, CELL, CELL))
board_pos = board_surf.get_rect(topleft=(SIDE_W + PANEL_GAP, TOP_H))

# ───────── Cursor Sprites ─────────
cur_white = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
pygame.draw.rect(cur_white, (0, 255, 255, 120), cur_white.get_rect(), 4)
cur_black = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
pygame.draw.rect(cur_black, (255, 0, 255, 120), cur_black.get_rect(), 4)

# ───────── Sprite Animation Cache ─────────
PIECES_ROOT = PROJECT_ROOT / "pieces"
ANIM_CACHE: Dict[str, Graphics] = {}

def _get_anim(code: str, state: str) -> Graphics:
    key = f"{code}-{state}"
    if key in ANIM_CACHE:
        return ANIM_CACHE[key]
    try:
        path = PIECES_ROOT / code / "states" / state / "sprites"
        anim = Graphics(path, (CELL, CELL), loop=True, fps=6.0)
    except Exception as e:
        print(f"[WARN] {e} – fallback to red circle")
        surf = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
        pygame.draw.circle(surf, (255, 0, 0), (CELL // 2, CELL // 2), CELL // 2 - 3)
        from client.graphics.img import Img
        anim = Graphics(None, (CELL, CELL))
        anim.frames = [Img(surf)]
    ANIM_CACHE[key] = anim
    return anim

# ───────── Core objects ─────────
model = ClientModel()
net = NetClient(model, player_name, player_color)  # ← matches client/net.py signature
net.start()
input_hdl = InputHandler(net, model)               # ← matches client/input_handler.py signature
bus = EventBus()
ui = GameUI(model, MoveLogUI(bus), ScoreUI(bus), Overlay(bus),
            player_name=player_name,
            player_color=player_color)
sfx = SoundFX(bus, "snd/move.wav", "snd/capture.wav", "snd/jump.wav", "snd/error.wav")

# ───────── Event decode helper ─────────
_EVENT_MAP = {cls.__name__: cls for cls in (
    MovePlayed, PieceTaken, JumpPlayed, ErrorPlayed, GameStarted, GameEnded, StateChanged)}

def _decode_event(d: dict):
    cls = _EVENT_MAP.get(d.get("_event_type") or d.get("type"))
    return cls(**{k: v for k, v in d.items() if k not in ("_event_type", "type")}) if cls else None

KEY_MAP = {
    "WHITE": {pygame.K_UP:"UP", pygame.K_DOWN:"DOWN",
              pygame.K_LEFT:"LEFT", pygame.K_RIGHT:"RIGHT",
              pygame.K_RETURN:"ENTER"},
    "BLACK": {pygame.K_w:"w", pygame.K_a:"a", pygame.K_s:"s",
              pygame.K_d:"d", pygame.K_SPACE:"space"},
}

# ───────── Main Loop ─────────
RUN = True
while RUN:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            RUN = False
        elif e.type == pygame.KEYDOWN and not model.game_over:
            cmap = KEY_MAP[player_color.upper()]
            if e.key in cmap:
                input_hdl.enqueue(player_color.upper(), cmap[e.key])

    # Pump inputs only while game is active
    if not model.game_over:
        input_hdl.pump_commands()

    # Net pump
    msgs: List[dict] = []
    while not net.rx.empty():
        msgs.append(net.rx.get())

    # snapshots first
    for m in msgs:
        if m.get("type") == "state":
            model.load_snapshot(m["payload"])
    # then events
    for m in msgs:
        if m.get("type") == "event":
            payload = m["payload"].get("payload", m["payload"])
            model.apply_event(payload)
            if (evt := _decode_event(payload)):
                bus.publish(evt)

    # draw
    now_ms = pygame.time.get_ticks()
    screen.fill((25, 25, 25))
    ui.draw_panels(screen)
    screen.blit(board_surf, board_pos.topleft)

    for p in model.alive_pieces():
        code, state = p["id"][:2], p.get("state", "idle")
        anim = _get_anim(code, state)
        anim.update(now_ms)
        surf = pygame.surfarray.make_surface(anim.get_img().img.swapaxes(0, 1)).convert_alpha()
        if "pixel" in p:
            px, py = p["pixel"]
            x = board_pos.left + px - surf.get_width() // 2
            y = board_pos.top + py - surf.get_height() // 2
        else:
            r, c = p["cell"]
            x = board_pos.left + c * CELL + CELL // 2 - surf.get_width() // 2
            y = board_pos.top + r * CELL + CELL // 2 - surf.get_height() // 2
        screen.blit(surf, (x, y))

    # cursors
    wr, wc = model.white_cursor
    br, bc = model.black_cursor
    screen.blit(cur_white, (board_pos.left + wc * CELL, board_pos.top + wr * CELL))
    screen.blit(cur_black, (board_pos.left + bc * CELL, board_pos.top + br * CELL))

    # If game over – draw dim overlay and hint
    if model.game_over:
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        font_big = pygame.font.SysFont("Arial", 40, bold=True)
        font_small = pygame.font.SysFont("Arial", 24)
        t = font_big.render("GAME OVER", True, (255, 255, 255))
        s = font_small.render(f"Winner: {model.winner or '-'}", True, (220, 220, 220))
        screen.blit(t, t.get_rect(center=(W//2, H//2 - 20)))
        screen.blit(s, s.get_rect(center=(W//2, H//2 + 20)))

    ui.draw_move_log(screen)
    ui.draw_score(screen)
    ui.draw_overlay(screen)
    ui.draw_piece_labels(screen)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()

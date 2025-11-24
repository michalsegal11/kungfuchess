# =============================================================
#  client/ui/overlay.py
# =============================================================


from __future__ import annotations
import pygame, cv2, numpy as np
from collections import deque
from core.engine.events import GameStarted, GameEnded

# ────────────────────────── init pygame stuff ──────────────────────────
pygame.font.init()
_FONT_BIG   = pygame.font.SysFont("Arial", 64, bold=True)
_FONT_SMALL = pygame.font.SysFont("Arial", 48, bold=True)

# ────────────────────────────── class ──────────────────────────────────
class Overlay:
    def __init__(self, bus):
        self.msg_queue   = deque()          # (msg, duration_ms)
        self.current_msg = None
        self.until_ms    = 0

        pygame.mixer.init()
        self.sounds = {
            "Ready":  pygame.mixer.Sound("snd/Ready.wav"),
            "Steady": pygame.mixer.Sound("snd/Steady.wav"),
            "Go!":    pygame.mixer.Sound("snd/Go!.wav"),
            "Win":    pygame.mixer.Sound("snd/win.wav"),
        }

        bus.subscribe(GameStarted, self._on_game_started)
        bus.subscribe(GameEnded,   self._on_game_ended)

    # ───────────────────────── event handlers ──────────────────────────
    def _on_game_started(self, _ev):
        self.queue_message("Ready",  1000)
        self.queue_message("Steady", 1000)
        self.queue_message("Go!",    1000)

    def _on_game_ended(self, ev):
        winner = "White Wins!" if ev.winner == "WHITE" else "Black Wins!"
        self.queue_message(winner, 3500)

    # ───────────────────────── public api ─────────────────────────────
    def queue_message(self, msg: str, duration: int = 2000):
        """Push a message to be shown (`duration` ms)."""
        self.msg_queue.append((msg, duration))

    def draw(self, frame):
        """Draw overlay on *frame* (pygame.Surface **or** cv2‐ndarray)."""
        now = pygame.time.get_ticks()

        # pick next message
        if self.current_msg is None and self.msg_queue:
            self.current_msg, dur = self.msg_queue.popleft()
            self.until_ms = now + dur
            # play sound
            if self.current_msg in self.sounds:
                self.sounds[self.current_msg].play()
            elif "WINS" in self.current_msg.upper():
                self.sounds["Win"].play()

        # done?
        if self.current_msg and now > self.until_ms:
            self.current_msg = None
        if not self.current_msg:
            return

        # branch by backend
        if isinstance(frame, pygame.Surface):
            _draw_pygame_overlay(frame, self.current_msg)
        else:  # assume OpenCV ndarray
            _draw_cv2_overlay(frame, self.current_msg)


# ───────────────────────── helper impls ────────────────────────────────
def _draw_pygame_overlay(surf: pygame.Surface, text: str):
    w, h = surf.get_size()
    is_win = "WINS" in text.upper()

    # dark translucent bar
    bar_h = 120
    bar = pygame.Surface((w, bar_h), pygame.SRCALPHA)
    bar.fill((0, 0, 0, 180))
    surf.blit(bar, (0, h // 2 - bar_h // 2))

    # render text
    font = _FONT_BIG if is_win else _FONT_SMALL
    color = (255, 215, 0) if is_win else (255, 255, 255)
    txt_surf = font.render(text, True, color)
    surf.blit(txt_surf, (w // 2 - txt_surf.get_width() // 2,
                         h // 2 - txt_surf.get_height() // 2))

def _draw_cv2_overlay(img: np.ndarray, text: str):
    h, w = img.shape[:2]
    is_win = "WINS" in text.upper()

    # dark bar
    overlay = img.copy()
    cv2.rectangle(overlay, (0, h // 2 - 60), (w, h // 2 + 60), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.5, img, 0.5, 0, img)

    # put text
    font_scale = 2.4 if is_win else 1.6
    color = (0, 215, 255) if is_win else (255, 255, 255)   # BGR!
    font = cv2.FONT_HERSHEY_SIMPLEX
    thickness = 3
    (tw, th), _ = cv2.getTextSize(text, font, font_scale, thickness)
    x = (w - tw) // 2
    y = (h + th) // 2
    cv2.putText(img, text, (x, y), font, font_scale, color, thickness,
                cv2.LINE_AA)

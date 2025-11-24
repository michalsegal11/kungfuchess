"""Score side‑panel – shows current capture points for each colour.

Like MoveLogUI, this widget can draw either on a *pygame.Surface* or on
an OpenCV / NumPy frame (legacy). When a side captures a piece its text
flashes for one second.
"""
from __future__ import annotations

import time, pygame, cv2, numpy as np
from typing import Tuple
from core.engine.events import PieceTaken
from shared.constants import (
    TXT_FONT, PANEL_BG, TXT_HEADER_CLR, TXT_ROW_CLR,
    SIDE_W, TOP_H, LINE_H,
)

pygame.font.init()
_HEADER_FONT = pygame.font.SysFont(TXT_FONT, 28)
_SCORE_FONT  = pygame.font.SysFont(TXT_FONT, 26)

_BGR_BG: Tuple[int, int, int] = PANEL_BG if len(PANEL_BG) == 3 else PANEL_BG[:3]

_FLASH_MS = 1000

class ScoreUI:
    """Maintains two counters and draws them."""

    def __init__(self, bus):
        self.white = 0
        self.black = 0
        self._flash_until = {"WHITE": 0, "BLACK": 0}
        bus.subscribe(PieceTaken, self._on_capture)

    # ────────────────────────────────────────────────────────── events ──
    def _on_capture(self, evt: PieceTaken):
        now = pygame.time.get_ticks()
        if evt.by_color == "WHITE":
            self.white += evt.value
            self._flash_until["WHITE"] = now + _FLASH_MS
        else:
            self.black += evt.value
            self._flash_until["BLACK"] = now + _FLASH_MS

    # ────────────────────────────────────────────────────────── draw ───
    def draw(self, surface) -> None:
            if isinstance(surface, pygame.Surface):
                self._draw_pygame(surface)
            elif isinstance(surface, np.ndarray):
                self._draw_cv(surface)
            else:
                raise TypeError("Unsupported surface type for ScoreUI.draw")

    # ─────────────────────────────────────────── pygame backend ────
    def _draw_pygame(self, surf: pygame.Surface):
        w, h = surf.get_size()
        x0 = w - SIDE_W

        # panel bg
        pygame.draw.rect(surf, PANEL_BG, pygame.Rect(x0, 0, SIDE_W, h))

        # header
        y =  10
        surf.blit(_HEADER_FONT.render("Score", True, TXT_HEADER_CLR), (x0 + 10, y))
        y += LINE_H

        now = pygame.time.get_ticks()
        white_col = (0, 255, 0) if now < self._flash_until["WHITE"] else TXT_ROW_CLR
        black_col = (255, 0, 0) if now < self._flash_until["BLACK"] else TXT_ROW_CLR

        surf.blit(_SCORE_FONT.render(f"White: {self.white}", True, white_col), (x0 + 10, y))
        y += LINE_H
        surf.blit(_SCORE_FONT.render(f"Black: {self.black}", True, black_col), (x0 + 10, y))

    # ─────────────────────────────────────────── OpenCV backend ───
    def _draw_cv(self, frame: np.ndarray):
        h, w = frame.shape[:2]
        x0 = w - SIDE_W
        cv2.rectangle(frame, (x0, 0), (x0 + SIDE_W, h), _BGR_BG, -1)

        y = TOP_H + 10
        cv2.putText(frame, "Score", (x0 + 10, y), TXT_FONT, 1.0, TXT_HEADER_CLR, 1, cv2.LINE_AA)
        y += LINE_H

        now = pygame.time.get_ticks()
        white_col = (0, 255, 0) if now < self._flash_until["WHITE"] else TXT_ROW_CLR
        black_col = (0, 0, 255) if now < self._flash_until["BLACK"] else TXT_ROW_CLR

        cv2.putText(frame, f"White: {self.white}", (x0 + 10, y), TXT_FONT, 0.9, white_col, 1, cv2.LINE_AA)
        y += LINE_H
        cv2.putText(frame, f"Black: {self.black}", (x0 + 10, y), TXT_FONT, 0.9, black_col, 1, cv2.LINE_AA)

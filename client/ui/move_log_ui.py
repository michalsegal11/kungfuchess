"""
MoveLogUI – keeps two independent move logs (white / black).

The widget subscribes to MovePlayed and PieceTaken events that arrive from the
server via an EventBus.  Each event is routed into the correct deque according
to the acting player’s color, so the UI can later render two separate columns.
"""
from __future__ import annotations
from collections import deque
from typing import Deque, Tuple

import pygame, time
from core.engine.events import MovePlayed, PieceTaken

# UI constants (shared between widgets)
from shared.constants import (
    PANEL_BG, TXT_HEADER_CLR, TXT_ROW_CLR, TXT_FONT,
    LINE_H, FONTSIZE_HEADER, FONTSIZE_ROW, SIDE_W, TOP_H,
)

pygame.font.init()
_HEADER_FONT = pygame.font.SysFont(TXT_FONT, int(FONTSIZE_HEADER * 24))
_ROW_FONT    = pygame.font.SysFont(TXT_FONT, int(FONTSIZE_ROW * 24))


class MoveLogUI:
    """Stores up to MAX_ROWS moves per color and exposes them to the renderer."""

    MAX_ROWS = 50

    def __init__(self, bus) -> None:
        self.white_log: Deque[Tuple[int, str]] = deque(maxlen=self.MAX_ROWS)
        self.black_log: Deque[Tuple[int, str]] = deque(maxlen=self.MAX_ROWS)

        bus.subscribe(MovePlayed,  self._on_move)
        bus.subscribe(PieceTaken, self._on_capture)

    # ───────────────────────── event handlers ──────────────────────────
    def _on_move(self, evt: MovePlayed) -> None:
        """Add a regular move to the correct log."""
        log = self.white_log if evt.color == "WHITE" else self.black_log
        log.appendleft((evt.time_ms, evt.move))

    def _on_capture(self, evt: PieceTaken) -> None:
        """Add a capture marker and target info to the attacker’s log."""
        log   = self.white_log if evt.by_color == "WHITE" else self.black_log
        stamp = int(time.time() * 1000)
        log.appendleft((stamp, f"{evt.piece_id} at {evt.cell}"))
        log.appendleft((stamp, "CAPTURE"))

    # ───────────────────────── public helpers ──────────────────────────
    def last_rows(self, color: str, n: int = 20) -> list[Tuple[int, str]]:
        """Return the last *n* rows for a given color (most-recent first)."""
        log = self.white_log if color == "WHITE" else self.black_log
        return list(log)[:n]

    # Optional: draw a single column directly (unused if GameUI handles drawing)
    def draw_side(self, surface: pygame.Surface, *, left: bool) -> None:
        """Convenience method to draw a standalone history column."""
        w, h = surface.get_size()
        x0   = 0 if left else w - SIDE_W
        y0   = TOP_H + 10

        # background
        pygame.draw.rect(surface, PANEL_BG,
                         pygame.Rect(x0, y0 - 10, SIDE_W, h - y0 + 10))

        # header
        surface.blit(_HEADER_FONT.render("History", True, TXT_HEADER_CLR),
                     (x0 + 10, y0))
        y = y0 + LINE_H

        color = "BLACK" if left else "WHITE"
        for _, txt in self.last_rows(color):
            surface.blit(_ROW_FONT.render(txt, True, TXT_ROW_CLR), (x0 + 10, y))
            y += LINE_H

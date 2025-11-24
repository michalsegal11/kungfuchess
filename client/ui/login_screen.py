"""Simple login / lobby screen for Kungfu-Chess (client side).

The screen collects:
    1.  Player name  – via keyboard input
    2.  Piece color  – WHITE or BLACK (buttons)

When the user presses <Enter> after choosing a color, the `run()` method
returns a tuple (player_name: str, color: str).
"""
from __future__ import annotations
import pygame
from typing import Tuple

WHITE     = (255, 255, 255)
BLACK     = (  0,   0,   0)
BG_COLOR  = ( 25,  25,  25)
BTN_HOVER = ( 80,  80,  80)
FONT_NAME = "Arial"

class LoginScreen:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen      = screen
        self.clock       = pygame.time.Clock()
        self.player_name = ""
        self.color       = None          # "WHITE" / "BLACK"
        pygame.font.init()
        self.font_big   = pygame.font.SysFont(FONT_NAME, 48, bold=True)
        self.font_small = pygame.font.SysFont(FONT_NAME, 32)

        # button rects
        W, H = screen.get_size()
        self.btn_white = pygame.Rect(W//2 - 200, H//2 + 40, 160, 50)
        self.btn_black = pygame.Rect(W//2 + 40,  H//2 + 40, 160, 50)

    # ───────────────────────────────────────────────────────────── helpers
    def _draw(self) -> None:
        self.screen.fill(BG_COLOR)
        W, _ = self.screen.get_size()

        # Title
        title = self.font_big.render("Enter your name:", True, WHITE)
        self.screen.blit(title, (W//2 - title.get_width()//2, 120))

        # Name box
        name_box = self.font_small.render(self.player_name or " ", True, WHITE)
        pygame.draw.rect(self.screen, WHITE,
                         name_box.get_rect(center=(W//2, 200)), 2)
        self.screen.blit(name_box,
                         name_box.get_rect(center=(W//2, 200)))

        # Color buttons
        for rect, label, clr in (
            (self.btn_white, "WHITE", WHITE),
            (self.btn_black, "BLACK", BLACK),
        ):
            hovered = rect.collidepoint(pygame.mouse.get_pos())
            pygame.draw.rect(self.screen, BTN_HOVER if hovered else clr, rect)
            txt = self.font_small.render(label, True,
                                         BLACK if clr == WHITE else WHITE)
            self.screen.blit(txt,
                             txt.get_rect(center=rect.center))

        # Selected color hint
        if self.color:
            hint = self.font_small.render(
                f"Chosen color: {self.color}", True, WHITE
            )
            self.screen.blit(hint,
                             hint.get_rect(center=(W//2, 350)))

        pygame.display.flip()

    # ─────────────────────────────────────────────────────────────── public
    def run(self) -> Tuple[str, str]:
        """
        Blocking loop – returns (name, color) when the user presses <Enter>.
        """
        while True:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    raise SystemExit

                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_RETURN and self.player_name and self.color:
                        return self.player_name, self.color
                    elif ev.key == pygame.K_BACKSPACE:
                        self.player_name = self.player_name[:-1]
                    elif ev.unicode.isprintable():
                        self.player_name += ev.unicode

                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    if self.btn_white.collidepoint(ev.pos):
                        self.color = "WHITE"
                    elif self.btn_black.collidepoint(ev.pos):
                        self.color = "BLACK"

            self._draw()
            self.clock.tick(60)

import pygame
from shared.constants import (
    SIDE_W, TOP_H, LINE_H,
    TXT_HEADER_CLR, TXT_ROW_CLR, PANEL_BG
)

pygame.font.init()
FONT_HEADER = pygame.font.SysFont("Arial", 30, bold=True)
FONT_ROW    = pygame.font.SysFont("Arial", 24)


class GameUI:
    """
    Handles all on-screen widgets: side panels, scores, history columns
    and overlay messages.
    """
    def __init__(self, model, move_log_ui, score_ui, overlay,
        player_name: str = "", player_color: str = "WHITE"):
        self.model       = model
        self.move_log_ui = move_log_ui
        self.score_ui    = score_ui
        self.overlay     = overlay
        self.player_name  = player_name
        self.player_color = player_color

    # --------------------------------------------------------------- panels
    def draw_panels(self, screen):
        W, H = screen.get_size()
        left  = pygame.Rect(0,          0, SIDE_W, H)
        right = pygame.Rect(W - SIDE_W, 0, SIDE_W, H)

        pygame.draw.rect(screen, PANEL_BG, left)
        pygame.draw.rect(screen, PANEL_BG, right)

        # ----- titles & score (left = BLACK, right = WHITE) --------------
        screen.blit(FONT_HEADER.render("Score", True, TXT_HEADER_CLR),
                    (20, 20))
        screen.blit(FONT_ROW.render(f"Black: {self.score_ui.black}",
                                    True, TXT_ROW_CLR), (20, 70))

        x_right = W - SIDE_W + 20
        screen.blit(FONT_HEADER.render("Score", True, TXT_HEADER_CLR),
                    (x_right, 20))
        screen.blit(FONT_ROW.render(f"White: {self.score_ui.white}",
                                    True, TXT_ROW_CLR), (x_right, 70))

        # “History” headers
        screen.blit(FONT_HEADER.render("History", True, TXT_HEADER_CLR),
                    (20, 120))
        screen.blit(FONT_HEADER.render("History", True, TXT_HEADER_CLR),
                    (x_right, 120))
        # Player name & color
        # # Draw player name on the appropriate side of the board
        # name_surf = FONT_ROW.render(self.player_name, True, TXT_HEADER_CLR)
        # board_w, board_h = self.model.board_pix  # width/height of board in px
        # x_center = W//2 - name_surf.get_width()//2

        # if self.player_color == "WHITE":   # bottom
        #     screen.blit(name_surf, (x_center, H - 40))
        # else:                              # top
        #     screen.blit(name_surf, (x_center, TOP_H - 30))


        white_name = self.model.player_names["WHITE"]
        black_name = self.model.player_names["BLACK"]

        if white_name:
            surf = FONT_ROW.render(white_name, True, TXT_HEADER_CLR)
            screen.blit(surf, (W//2 - surf.get_width()//2, H - 40))
        if black_name:
            surf = FONT_ROW.render(black_name, True, TXT_HEADER_CLR)
            screen.blit(surf, (W//2 - surf.get_width()//2, TOP_H - 30))

    # ------------------------------------------------------- move log cols
    def draw_move_log(self, screen):
        """
        Draws two independent history columns:
        left  → BLACK, right → WHITE.
        """
        W, H = screen.get_size()
        y_start = 150           # below score / headers

        # ------- LEFT  (BLACK) ------------------------------------------
        pygame.draw.rect(
            screen, PANEL_BG,
            pygame.Rect(0, y_start, SIDE_W, H - y_start)
        )
        y = y_start + 10
        for _, txt in reversed(self.move_log_ui.last_rows("BLACK", 20)):
            screen.blit(FONT_ROW.render(txt, True, TXT_ROW_CLR),
                        (10, y))
            y += LINE_H

        # ------- RIGHT (WHITE) ------------------------------------------
        x0 = W - SIDE_W
        pygame.draw.rect(
            screen, PANEL_BG,
            pygame.Rect(x0, y_start, SIDE_W, H - y_start)
        )
        y = y_start + 10
        for _, txt in reversed(self.move_log_ui.last_rows("WHITE", 20)):
            screen.blit(FONT_ROW.render(txt, True, TXT_ROW_CLR),
                        (x0 + 10, y))
            y += LINE_H

    # ----------------------------------------------------------- other ui
    def draw_score(self, screen):  # already drawn in draw_panels
        pass

    def draw_overlay(self, screen):
        self.overlay.draw(screen)

    def draw_piece_labels(self, screen):
        """Small helper for debugging piece selection."""
        white = self.model.from_piece["WHITE"]
        black = self.model.from_piece["BLACK"]
        y = 160
        if white:
            screen.blit(FONT_ROW.render(f"White: {white}", True, (255, 255, 255)), (20, y))
            y += 30
        if black:
            screen.blit(FONT_ROW.render(f"Black: {black}", True, (255, 255, 255)), (20, y))

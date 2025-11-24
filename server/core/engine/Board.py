
from __future__ import annotations
from dataclasses import dataclass
import copy
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from core.pieces.Piece import Piece  



@dataclass
class Board:
    cell_H_pix : int
    cell_W_pix : int
    W_cells    : int
    H_cells    : int
    img        : Img| None = None  # main board image (background)
    background_img: Img | None = None
    game: Game | None = None

    # ────────────────────────────────────────────────────────────
    def __post_init__(self):
        # if self.img is None:
        #     raise ValueError("Board.img cant be None")
        pass

    # ────────────────────────────────────────────────────────────
    def clone(self) -> "Board":
        """Return a *logic-only* copy (no images)."""
        return Board(
            cell_H_pix=self.cell_H_pix,
            cell_W_pix=self.cell_W_pix,
            W_cells   =self.W_cells,
            H_cells   =self.H_cells,
            img       = None,
            background_img = None,
        )

    # ────────────────────────────────────────────────────────────
    @property
    def total_width_pix(self) -> int:
        return self.W_cells * self.cell_W_pix

    @property
    def total_height_pix(self) -> int:
        return self.H_cells * self.cell_H_pix

    # ────────────────────────────────────────────────────────────
    def cell_to_pixel(self, row: int, col: int) -> tuple[int, int]:

        x = col * self.cell_W_pix
        y = row * self.cell_H_pix   
        return x, y

    def pixel_to_cell(self, x: int, y: int) -> tuple[int, int]:
        return (y // self.cell_H_pix, x // self.cell_W_pix)

    # ────────────────────────────────────────────────────────────
    def is_valid_cell(self, row: int, col: int) -> bool:
        return 0 <= row < self.H_cells and 0 <= col < self.W_cells

    def get_cell_center_pixel(self, row: int, col: int) -> tuple[int, int]:
        x, y = self.cell_to_pixel(row, col)
        return (x + self.cell_W_pix // 2, y + self.cell_H_pix // 2)

    # ────────────────────────────────────────────────────────────
    # def draw_pieces(self, pieces: list[Piece],include_captured: bool = False) -> "Board":
    #     board_cp = self.clone()

    #     for p in pieces:
    #         if include_captured or not getattr(p, "is_captured", False):
    #             p.draw_on_board(board_cp)
    #     return board_cp
        
    # def draw(self, screen, pieces: list["Piece"]) -> None:
    #     import pygame, cv2

    #     if self.img and self.img.img is not None:
    #         board_rgb = cv2.cvtColor(self.img.img, cv2.COLOR_BGR2RGB)
    #         board_surface = pygame.surfarray.make_surface(board_rgb.swapaxes(0, 1))
    #         screen.blit(board_surface, (0, 0))

    #     for piece in pieces:
    #         if piece.is_captured:
    #             continue

    #         img = piece.current_state.graphics.get_img()
    #         if img and img.img is not None:
    #             sprite_rgb = cv2.cvtColor(img.img, cv2.COLOR_BGR2RGB)
    #             sprite_surface = pygame.surfarray.make_surface(sprite_rgb.swapaxes(0, 1))

    #             row, col = piece.current_state.get_cell()
    #             x, y = self.cell_to_pixel(row, col)
    #             screen.blit(sprite_surface, (x, y))

    # # ────────────────────────────────────────────────────────────
    # def show(self) -> bool:
    #     if self.img and self.img.img is not None:
    #         self.img.show()
    #         return True
    #     print("Board.show(): No image to display")
    #     return False

    # ────────────────────────────────────────────────────────────
    def __str__(self) -> str:
        return f"Board({self.H_cells}×{self.W_cells}, cell {self.cell_W_pix}×{self.cell_H_pix}px)"

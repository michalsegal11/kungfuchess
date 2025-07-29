
from __future__ import annotations
from dataclasses import dataclass
import copy
from graphics.img import Img
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pieces.Piece import Piece  



@dataclass
class Board:
    cell_H_pix : int
    cell_W_pix : int
    W_cells    : int
    H_cells    : int
    img        : Img
    background_img: Img | None = None

    # ────────────────────────────────────────────────────────────
    def __post_init__(self):
        if self.img is None:
            raise ValueError("Board.img cant be None")

    # ────────────────────────────────────────────────────────────
    def clone(self) -> "Board":
        """Return a *deep* copy of the board."""
        cloned = Board(
            cell_H_pix=self.cell_H_pix,
            cell_W_pix=self.cell_W_pix,
            W_cells   =self.W_cells,
            H_cells   =self.H_cells,
            img       = Img(),         
            background_img = None,
        )

       
        src_img = (self.background_img.img
                   if self.background_img and self.background_img.img is not None
                   else self.img.img)
        if src_img is None:
            raise RuntimeError("clone(): no image in sorce board")

        cloned_img = src_img.copy()
        cloned.img.img = cloned_img
        cloned.background_img = Img()
        cloned.background_img.img = cloned_img     
        return cloned

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
    def draw_pieces(self, pieces: list[Piece],include_captured: bool = False) -> "Board":
        board_cp = self.clone()

        for p in pieces:
            if include_captured or not getattr(p, "is_captured", False):
                p.draw_on_board(board_cp)
        return board_cp

    # ────────────────────────────────────────────────────────────
    def show(self) -> bool:
        if self.img and self.img.img is not None:
            self.img.show()
            return True
        print("Board.show(): No image to display")
        return False

    # ────────────────────────────────────────────────────────────
    def __str__(self) -> str:
        return f"Board({self.H_cells}×{self.W_cells}, cell {self.cell_W_pix}×{self.cell_H_pix}px)"

import pathlib
from graphics.img import Img
from game.game import Game
# from Game import Game
import numpy as np

from pieces.PieceFactory import PieceFactory
from engine.Board import Board
from pathlib import Path
import cv2

import pygame
pygame.init()
import csv

def load_pieces_from_csv(csv_path: Path) -> list[tuple[str, tuple[int, int]]]:
    """Reads piece layout from a CSV file and returns list of (piece_type, (row, col))."""
    pieces = []
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row_idx, row in enumerate(reader):
            for col_idx, cell in enumerate(row):
                if cell.strip():  # non-empty
                    pieces.append((cell.strip(), (row_idx, col_idx)))
    return pieces


def create_chessboard_image(cell_size=64, rows=8, cols=8):
    board_height = cell_size * rows
    board_width = cell_size * cols
    board_img = np.zeros((board_height, board_width, 3), dtype=np.uint8)

    color_light = (220, 220, 220)  
    color_dark  = (70, 70, 70)    

    for row in range(rows):
        for col in range(cols):
            color = color_light if (row + col) % 2 == 0 else color_dark
            y0 = row * cell_size
            y1 = y0 + cell_size
            x0 = col * cell_size
            x1 = x0 + cell_size
            board_img[y0:y1, x0:x1] = color

    return board_img



def main():

    cell_W, cell_H = 64, 64

    board_img_np = create_chessboard_image(cell_size=64)
    board_img = Img()
    board_img.img = board_img_np
    img_height, img_width = board_img.img.shape[:2]

    W_cells = img_width // cell_W
    H_cells = img_height // cell_H

    print(f"Board dimensions: {W_cells}x{H_cells} cells, {img_width}x{img_height} pixels")
    print(f"Cell size: {cell_W}x{cell_H} pixels")

    board = Board(
        cell_H_pix=cell_H,
        cell_W_pix=cell_W,
        W_cells=W_cells,
        H_cells=H_cells,
        img=board_img
    )

    bg_path = Path(__file__).parents[2] / "assets" / "bg.jpg"
    bg_img = cv2.imread(str(bg_path))


    background_img = None
    if bg_img is not None:
        background_img = Img()
        background_img.img = bg_img

    pieces_dir = r'C:\Users\user1\Documents\SoftWare\Kamatech\CTD EXAMPLE\CTD25\pieces'
    pieces_root = Path(pieces_dir)
    factory = PieceFactory(board, pieces_root)

    csv_path = Path(__file__).parents[2] / "assets" / "board.csv"
    all_pieces = load_pieces_from_csv(csv_path)

    
    pieces = []

    print(f"\n=== create pieces ===")
    for piece_type, (row, col) in all_pieces:
        try:
            if piece_type in factory.piece_templates:
                piece = factory.create_piece(piece_type, (row, col))
            else:
                piece = factory.create_piece("RB", (row, col))  # fallback
            pieces.append(piece)
            print(f"Created {piece.piece_id}")
        except Exception as e:
            print(f"Error creating {piece_type} at ({row},{col}): {e}")

    print(f"\nTotal pieces created: {len(pieces)}")



    board.background_img = board.img 
    game = Game(pieces, board)
    game.background_img = background_img  

    print(f"\n=== create game ===")
    game.run()

if __name__ == "__main__":
    main()
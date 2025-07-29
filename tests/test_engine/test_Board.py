# tests/test_engine/test_Board.py
import pytest
import numpy as np
from engine.Board import Board
from graphics.img import Img
from pieces.Piece import Piece
from engine.State import State
from engine.Moves import Moves
from graphics.Graphics import Graphics
from physics.idle_physics import IdlePhysics

# ───────────────────────────── Fixtures ─────────────────────────────

@pytest.fixture
def dummy_img():
    img = Img()
    img.img = np.ones((512, 512, 3), dtype=np.uint8) * 255
    return img

@pytest.fixture
def board(dummy_img):
    return Board(cell_H_pix=64, cell_W_pix=64, W_cells=8, H_cells=8, img=dummy_img)

@pytest.fixture
def dummy_piece(board):
    moves = Moves(None, (8, 8))
    graphics = Graphics(sprites_folder=None, cell_size=(64, 64))
    physics = IdlePhysics(start_cell=(3, 4), board=board)
    state = State(moves, graphics, physics)
    return Piece("TEST_3_4", state)

# ───────────────────────────── Tests ─────────────────────────────

def test_total_dimensions(board):
    """Verify total pixel dimensions of the board."""
    assert board.total_width_pix == 8 * 64
    assert board.total_height_pix == 8 * 64

def test_cell_to_pixel_and_back(board):
    """Verify conversion from (row,col) to (x,y) and back."""
    row, col = 2, 3
    x, y = board.cell_to_pixel(row, col)
    assert (x, y) == (3 * 64, 2 * 64)
    assert board.pixel_to_cell(x + 10, y + 10) == (2, 3)

def test_cell_center(board):
    """Verify center of cell is correctly calculated."""
    row, col = 1, 1
    cx, cy = board.get_cell_center_pixel(row, col)
    assert cx == 64 + 32
    assert cy == 64 + 32

def test_is_valid_cell(board):
    """Ensure cell validity boundaries."""
    assert board.is_valid_cell(0, 0) is True
    assert board.is_valid_cell(7, 7) is True
    assert board.is_valid_cell(8, 0) is False
    assert board.is_valid_cell(-1, 3) is False

def test_clone_creates_independent_copy(board):
    """Verify that cloned board has separate image object."""
    cloned = board.clone()
    assert isinstance(cloned, Board)
    assert cloned is not board
    assert cloned.img is not board.img
    assert cloned.background_img is not board.background_img

def test_draw_pieces_only_alive(board, dummy_piece):
    """Verify that only non-captured pieces are drawn on board."""
    clone = board.draw_pieces([dummy_piece])
    assert isinstance(clone, Board)

    dummy_piece.is_captured = True
    clone2 = board.draw_pieces([dummy_piece])
    assert isinstance(clone2, Board)

import pytest
import numpy as np
import cv2
from unittest.mock import MagicMock, patch

from ui.ui import draw, show


from graphics.img import Img

class DummyBoard:
    def __init__(self):
        self.cell_W_pix = 80
        self.cell_H_pix = 80
        self.W_cells = 8
        self.H_cells = 8
        self.img = Img()
        self.img.img = np.zeros((self.total_height_pix, self.total_width_pix, 3), dtype=np.uint8)
        self.background_img = None


    def total_width_pix(self): return self.W_cells * self.cell_W_pix
    def total_height_pix(self): return self.H_cells * self.cell_H_pix

    total_width_pix = property(total_width_pix)
    total_height_pix = property(total_height_pix)

    def get_cell_center_pixel(self, r, c):
        return (c * self.cell_W_pix + self.cell_W_pix // 2,
                r * self.cell_H_pix + self.cell_H_pix // 2)

    def clone(self):
        return self


class DummyPiece:
    def __init__(self, piece_id, state_name="idle"):
        self.piece_id = piece_id
        self.current_state = MagicMock()
        self.current_state.state_name = state_name
        self.is_captured = False

    def draw_on_board(self, board):
        pass


@pytest.fixture
def dummy_game():
    class DummyGame:
        def __init__(self):
            self.board = DummyBoard()
            self.white_cursor = [7, 4]
            self.black_cursor = [0, 4]
            self.pieces = [
                DummyPiece("PW_1_1", "idle"),
                DummyPiece("NB_7_1", "move"),
            ]
            self.clone_board = lambda: self.board
            self.move_history = {"WHITE": [], "BLACK": []}
            self.overlay = MagicMock()
            self.score_ui = MagicMock()
            self.final_img = None
            self.background_img = None
            self.get_selected_white_piece = lambda: self.pieces[0]
            self.get_selected_black_piece = lambda: self.pieces[1]
            self.running = True
    return DummyGame()


def test_draw_creates_final_img(dummy_game):
    draw(dummy_game)
    assert dummy_game.final_img is not None
    assert isinstance(dummy_game.final_img, np.ndarray)


@patch("cv2.imshow")
@patch("cv2.waitKey", return_value=ord('q'))
@patch("cv2.getWindowProperty", return_value=1)
def test_show_exits_on_q(mock_win, mock_key, mock_show, dummy_game):
    draw(dummy_game)
    result = show(dummy_game)
    assert result is False
    assert dummy_game.running is False


@patch("cv2.imshow")
@patch("cv2.waitKey", return_value=-1)
@patch("cv2.getWindowProperty", return_value=1)
def test_show_returns_true_on_open(mock_win, mock_key, mock_show, dummy_game):
    draw(dummy_game)
    result = show(dummy_game)
    assert result is True


def test_show_warns_when_nothing_to_show(capfd, dummy_game):
    dummy_game.final_img = None
    result = show(dummy_game)
    out, _ = capfd.readouterr()
    assert "nothing to show" in out
    assert result is True

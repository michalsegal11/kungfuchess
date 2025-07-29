import pytest
from physics.idle_physics import IdlePhysics
from engine.Board import Board

@pytest.fixture
def dummy_board():
    from graphics.img import Img
    return Board(cell_H_pix=80, cell_W_pix=80, W_cells=8, H_cells=8, img=Img())

def test_capture_flags(dummy_board):
    p = IdlePhysics((3, 3), dummy_board)
    assert p.can_be_captured() is True
    assert p.can_capture() is True

    p.set_capturable(False)
    p.set_can_capture(False)

    assert p.can_be_captured() is False
    assert p.can_capture() is False

def test_speed_multiplier(dummy_board):
    p = IdlePhysics((0, 0), dummy_board, speed_m_s=2.5)
    assert p.speed_multiplier == 2.5

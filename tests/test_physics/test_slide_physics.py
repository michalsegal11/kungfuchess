import pytest
from physics.slide_physics import SlidePhysics
from engine.Command import Command
from engine.Board import Board
from graphics.img import Img

@pytest.fixture
def board():
    return Board(cell_H_pix=80, cell_W_pix=80, W_cells=8, H_cells=8, img=Img())

@pytest.fixture
def slide(board):
    return SlidePhysics(start_cell=(1, 1), board=board, speed_m_s=2.0)

def test_reset_valid_move(slide):
    cmd = Command.move("P_1_1", (1, 1), (3, 1), ts=1000)
    slide.reset(cmd)
    assert slide._moving is True
    assert slide.get_current_cell() == (1, 1)

def test_reset_invalid_cmd_type(slide):
    cmd = Command.capture("P", (1, 1), (1, 2), captured_id="enemy", ts=1000)
    slide.reset(cmd)
    assert not slide._moving


def test_update_animation_progression(slide):
    cmd = Command.move("P", (1, 1), (1, 3), ts=1000)
    slide.reset(cmd)
    pos1 = slide.get_pos()
    slide.update(now_ms=1600)
    pos2 = slide.get_pos()
    assert pos1 != pos2

def test_arrival_detection(slide):
    cmd = Command.move("P", (1, 1), (1, 2), ts=1000)
    slide.reset(cmd)
    duration = slide._segment_duration_ms()
    slide.update(now_ms=1000 + duration + 1)
    assert slide.is_movement_finished()

def test_multi_segment_path(slide):
    path = [(1, 1), (1, 2), (2, 2)]
    slide.set_path(path)
    assert slide._moving is True

    #level 1
    assert slide.start_cell == (1, 1)
    assert slide.target_cell == (1, 2)

    #level 2
    slide.update(1000 + slide._segment_duration_ms() + 10)
    assert slide.get_current_cell() == (1, 2) or slide.get_current_cell() == (2, 2)


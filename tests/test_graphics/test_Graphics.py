import pytest
from graphics.Graphics import Graphics
from graphics.mock_img import MockImg
from engine.Command import Command

@pytest.fixture
def dummy_graphics():
    g = Graphics(sprites_folder=None, cell_size=(64, 64), loop=True, fps=10.0)
    g.frames = [MockImg(), MockImg(), MockImg()]  # שלושה פריימים מזויפים
    g.frame_duration = 100  # כל פריים נמשך 100ms
    return g

def test_loads_frames(dummy_graphics):
    assert len(dummy_graphics.frames) == 3
    assert isinstance(dummy_graphics.frames[0], MockImg)

def test_reset_sets_time_and_frame(dummy_graphics):
    dummy_graphics.start_time = 500
    cmd = Command.move("PW_1_1", (1, 1), (2, 1))
    dummy_graphics.reset(cmd)
    assert dummy_graphics.current_frame_index == 0

def test_update_advances_looping_frame(dummy_graphics):
    dummy_graphics.loop = True
    dummy_graphics.start_time = 0
    dummy_graphics.update(150)
    assert dummy_graphics.current_frame_index == 1

    dummy_graphics.update(350)
    assert dummy_graphics.current_frame_index == 2


def test_update_stops_at_last_frame_when_not_looping(dummy_graphics):
    dummy_graphics.loop = False
    dummy_graphics.start_time = 0

    dummy_graphics.update(150)
    assert dummy_graphics.current_frame_index == 1

    dummy_graphics.update(350)
    assert dummy_graphics.current_frame_index == 2

    dummy_graphics.update(500)
    assert dummy_graphics.current_frame_index == 2  # לא מתקדם מעבר

def test_is_animation_finished(dummy_graphics):
    dummy_graphics.loop = False
    dummy_graphics.start_time = 0

    dummy_graphics.update(50)
    assert not dummy_graphics.is_animation_finished()

    dummy_graphics.update(400)
    assert dummy_graphics.is_animation_finished()

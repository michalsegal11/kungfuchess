import pytest
from graphics.mock_img import MockImg

def test_draw_on_records_position():
    MockImg.reset()
    img = MockImg()
    other = MockImg()
    img.draw_on(other, 20, 30)
    assert (20, 30) in MockImg.traj

def test_put_text_records_text():
    MockImg.reset()
    img = MockImg()
    img.put_text("Hello", 10, 40, font_size=1.2)
    assert ((10, 40), "Hello") in MockImg.txt_traj

def test_copy_returns_new_instance():
    img = MockImg()
    clone = img.copy()
    assert isinstance(clone, MockImg)
    assert clone is not img

def test_reset_clears_traj():
    MockImg.traj = [(1, 2), (3, 4)]
    MockImg.txt_traj = [((5, 5), "abc")]
    MockImg.reset()
    assert not MockImg.traj
    assert not MockImg.txt_traj

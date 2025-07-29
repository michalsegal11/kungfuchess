import pytest
from physics.idle_physics import IdlePhysics
from engine.Board import Board
from engine.Command import Command
from graphics.img import Img

@pytest.fixture
def idle_phys():
    board = Board(80, 80, 8, 8, Img())
    return IdlePhysics(start_cell=(2, 3), board=board)

def test_reset_does_not_change_position(idle_phys):
    old_pos = idle_phys.get_pos()
    cmd = Command.move("P_2_3", (2, 3), (2, 4))
    idle_phys.reset(cmd)
    assert idle_phys.get_pos() == old_pos
    assert idle_phys.is_movement_finished() is True

def test_update_does_nothing(idle_phys):
    before = idle_phys.get_pos()
    idle_phys.update(now_ms=999999)
    after = idle_phys.get_pos()
    assert before == after

def test_copy_returns_equivalent(idle_phys):
    copied = idle_phys.copy()
    assert copied.get_current_cell() == idle_phys.get_current_cell()
    assert copied.get_pos() == idle_phys.get_pos()
    assert copied.speed_multiplier == idle_phys.speed_multiplier

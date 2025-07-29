# ============================ test_PhysicsFactory.py ============================

import pytest
from physics.PhysicsFactory import PhysicsFactory
from physics.idle_physics import IdlePhysics
from physics.slide_physics import SlidePhysics
from engine.Board import Board
from graphics.mock_img import MockImg


# ------------------------------------------------------------------------------
#                                FIXTURES
# ------------------------------------------------------------------------------

@pytest.fixture
def dummy_board():
    return Board(cell_H_pix=32, cell_W_pix=32, W_cells=8, H_cells=8, img=MockImg())

@pytest.fixture
def factory(dummy_board):
    return PhysicsFactory(dummy_board)


# ------------------------------------------------------------------------------
#                                TEST CASES
# ------------------------------------------------------------------------------

def test_idle_physics_creation(factory):
    """
    Ensure that 'idle' state creates an IdlePhysics object.
    """
    physics = factory.create("idle", (0, 0), {})
    assert isinstance(physics, IdlePhysics)


def test_slide_physics_creation_with_default_config(factory):
    """
    Ensure that any non-idle state creates a SlidePhysics object by default.
    """
    physics = factory.create("move", (1, 1), {})
    assert isinstance(physics, SlidePhysics)
    assert physics.speed_multiplier == 1.0
    assert physics.can_capture() is True
    assert physics.can_be_captured() is True


def test_slide_physics_with_custom_config(factory):
    """
    Test SlidePhysics creation with specific configuration for speed and capture flags.
    """
    cfg = {
        "speed": 2.5,
        "can_capture": False,
        "can_be_captured": False
    }
    physics = factory.create("attack", (2, 3), cfg)
    assert isinstance(physics, SlidePhysics)
    assert physics.speed_multiplier == 2.5
    assert physics.can_capture() is False
    assert physics.can_be_captured() is False




def test_slide_physics_path_initialization(factory):
    """
    Ensure SlidePhysics properly initializes movement path.
    """
    physics = factory.create("move", (3, 3), {})
    path = [(3, 3), (4, 4), (5, 5)]
    physics.set_path(path)
    assert physics._path == path
    assert physics._path_idx == 1
    assert physics.start_cell == (3, 3)
    assert physics.target_cell == (4, 4)
    assert physics._moving is True

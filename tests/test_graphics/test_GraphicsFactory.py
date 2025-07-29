import pytest
from graphics.GraphicsFactory import GraphicsFactory
from graphics.Graphics import Graphics
from pathlib import Path
import numpy as np
import cv2

@pytest.fixture
def dummy_sprite_folder(tmp_path):
    sprites = tmp_path / "pawn" / "states" / "idle" / "sprites"
    sprites.mkdir(parents=True)
    for i in range(2):
        (sprites / f"{i}.png").write_text("fake") # create dummy images
    # Return the parent folder to simulate the structure
    return sprites.parent.parent  

@pytest.fixture
def dummy_cfg():
    return {
        "fps": 5.0,
        "loop": False,
        "sprites_folder": "sprites"  #can operate with subfolder
    }

def test_load_graphics_basic(tmp_path, dummy_cfg):
    factory = GraphicsFactory()
    folder = tmp_path / "idle" / "sprites"
    folder.mkdir(parents=True)
    for i in range(3):
        img_path = folder / f"{i}.png"
        dummy_img = np.zeros((32, 32, 3), dtype=np.uint8)  # black image
        cv2.imwrite(str(img_path), dummy_img)

    g = factory.load(folder.parent, dummy_cfg, cell_size=(64, 64))
    assert isinstance(g, Graphics)
    assert g.fps == 5.0
    assert g.loop is False
    assert g.cell_size == (64, 64)
    assert len(g.frames) == 3

def test_load_graphics_with_subfolder(tmp_path):
    import numpy as np, cv2

    root = tmp_path / "idle"
    root.mkdir()
    subfolder = root / "sprites" / "alt"
    subfolder.mkdir(parents=True)

    for i in range(2):
        img_path = subfolder / f"{i}.png"
        dummy_img = np.zeros((32, 32, 3), dtype=np.uint8)
        cv2.imwrite(str(img_path), dummy_img)

    factory = GraphicsFactory()
    cfg = {
        "fps": 4.0,
        "loop": True,
        "sprites_folder": "alt"
    }

    g = factory.load(root / "sprites", cfg, (64, 64))

    assert len(g.frames) == 2
    assert g.loop is True
    assert g.fps == 4.0


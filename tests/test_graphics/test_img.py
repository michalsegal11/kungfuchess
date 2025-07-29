import pytest
import numpy as np
from graphics.img import Img
import cv2

@pytest.fixture
def blank_image():
    """Fixture to create a blank image for testing."""
    # Create a blank image of size 100x100 with 3 color channels (RGB
    img = Img()
    img.img = np.zeros((100, 100, 3), dtype=np.uint8)
    return img

def test_read_valid_image(tmp_path):
    dummy_path = tmp_path / "dummy.png"

    # Create a dummy image
    arr = np.full((32, 32, 3), 255, dtype=np.uint8)
    cv2.imwrite(str(dummy_path), arr)

    img = Img().read(dummy_path)
    assert img.img is not None
    assert img.img.shape[:2] == (32, 32)

def test_read_resize_no_aspect(tmp_path):
    dummy_path = tmp_path / "resize.png"
    arr = np.full((100, 200, 3), 255, dtype=np.uint8)
    cv2.imwrite(str(dummy_path), arr)

    img = Img().read(dummy_path, size=(50, 50), keep_aspect=False)
    assert img.img.shape[0:2] == (50, 50)

def test_draw_on_inside(blank_image):
    fg = Img()
    fg.img = np.ones((20, 20, 3), dtype=np.uint8) * 255
    fg.draw_on(blank_image, 10, 10)

    region = blank_image.img[10:30, 10:30]
    assert np.all(region > 0)

def test_draw_on_outside_bounds(blank_image):
    fg = Img()
    fg.img = np.ones((20, 20, 3), dtype=np.uint8) * 128
    fg.draw_on(blank_image, 90, 90)  # Should clip most of it

    clipped = blank_image.img[90:, 90:]
    assert clipped.shape[0] > 0 and clipped.shape[1] > 0

def test_put_text_on_image(blank_image):
    blank_image.put_text("Hi", 5, 30, font_size=0.5, color=(255, 255, 255))
    assert blank_image.img is not None

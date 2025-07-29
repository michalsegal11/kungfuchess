import pytest
import cv2
import game.constants as C

def test_colors_are_rgb():
    """Ensure all color constants are RGB triplets with int values 0–255."""
    for name in dir(C):
        if name.endswith("CLR") or name.endswith("BG"):
            color = getattr(C, name)
            assert isinstance(color, tuple), f"{name} should be a tuple"
            assert len(color) == 3, f"{name} should have 3 components"
            for c in color:
                assert isinstance(c, int), f"{name} should contain integers"
                assert 0 <= c <= 255, f"{name} values must be in RGB range"

def test_font_is_cv2_constant():
    """Ensure the font used is a valid cv2 font constant."""
    assert isinstance(C.TXT_FONT, int)
    assert C.TXT_FONT in [
        cv2.FONT_HERSHEY_SIMPLEX,
        cv2.FONT_HERSHEY_PLAIN,
        cv2.FONT_HERSHEY_DUPLEX,
        cv2.FONT_HERSHEY_COMPLEX,
        cv2.FONT_HERSHEY_TRIPLEX,
        cv2.FONT_HERSHEY_COMPLEX_SMALL,
        cv2.FONT_HERSHEY_SCRIPT_SIMPLEX,
        cv2.FONT_HERSHEY_SCRIPT_COMPLEX,
    ]

def test_dimensions_are_positive():
    """Verify all UI dimensions are positive."""
    assert C.SIDE_W > 0
    assert C.TOP_H > 0
    assert C.BOT_H > 0
    assert C.LINE_H > 0
    assert C.MAX_ROWS >= 5

def test_font_sizes_are_valid():
    """Check that font sizes are floats in the range [0.1, 3.0]."""
    for name in dir(C):
        if name.startswith("FONTSIZE_"):
            size = getattr(C, name)
            assert isinstance(size, float)
            assert 0.1 <= size <= 3.0, f"{name} out of range"

def test_piece_letter_mapping():
    """Validate piece → letter mapping used for notation."""
    assert isinstance(C.PIECE_LETTER, dict)
    expected = {"K": "K", "Q": "Q", "R": "R", "B": "B", "N": "N", "P": ""}
    assert C.PIECE_LETTER == expected

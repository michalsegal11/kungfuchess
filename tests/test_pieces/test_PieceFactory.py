# tests/test_pieces/test_PieceFactory.py
import pytest
import pathlib
import json
from engine.Board import Board
from pieces.PieceFactory import PieceFactory
from graphics.img import Img

@pytest.fixture
def dummy_board():
    return Board(cell_H_pix=64, cell_W_pix=64, W_cells=8, H_cells=8, img=Img())

@pytest.fixture
def template_structure(tmp_path):
    pw_path = tmp_path / "PW" / "states" / "idle"
    pw_path.mkdir(parents=True)

    cfg = {
        "graphics": {
            "fps": 1.0,
            "loop": True
        },
        "physics": {
            "speed_m_per_sec": 1.0,
            "can_be_captured": True,
            "can_capture": True,
            "next_state_when_finished": "idle"
        }
    }
    with open(pw_path / "config.json", "w", encoding="utf-8") as f:
        json.dump(cfg, f)

    (pw_path / "sprites").mkdir()

    moves_txt = tmp_path / "PW" / "moves.txt"
    with open(moves_txt, "w", encoding="utf-8") as f:
        f.write("1,0:f\n2,0:1st\n")

    return tmp_path

def test_piece_factory_loads_templates(dummy_board, template_structure):
    factory = PieceFactory(dummy_board, template_structure)
    assert "PW" in factory.piece_templates
    idle_state = factory.piece_templates["PW"]
    assert idle_state.state_name == "idle"

def test_create_piece_returns_pawn(dummy_board, template_structure):
    factory = PieceFactory(dummy_board, template_structure)
    pawn = factory.create_piece("PW", (1, 1))
    assert pawn.piece_id == "PW_1_1"
    assert pawn.get_cell() == (1, 1)
    assert pawn.__class__.__name__ == "Pawn"

def test_invalid_type_raises(dummy_board, template_structure):
    factory = PieceFactory(dummy_board, template_structure)
    with pytest.raises(ValueError):
        factory.create_piece("UNKNOWN", (0, 0))

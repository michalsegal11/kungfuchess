# tests/test_engine/test_Moves.py
import tempfile
import pathlib
from engine.Moves import Moves, MoveRule

def test_default_moves_when_file_missing():
    moves = Moves(txt_path=pathlib.Path("nonexistent.txt"), board_size=(8, 8))
    assert len(moves.rules) == 4  # Default moves for rook-like piece
    directions = {(r.dr, r.dc) for r in moves.rules}
    assert (1, 0) in directions
    assert (-1, 0) in directions
    assert (0, 1) in directions
    assert (0, -1) in directions

def test_load_moves_from_file():
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as f:
        f.write("1,0:f\n1,1:x\n-1,0:capture\n")
        f.flush()
        moves = Moves(pathlib.Path(f.name), (8, 8))

    assert len(moves.rules) == 3
    tags = {r.tag for r in moves.rules}
    assert "f" in tags
    assert "x" in tags
    assert "capture" in tags

def test_get_moves_respects_capture_filter():
    rules = [
        MoveRule(1, 0, "f"),
        MoveRule(1, 1, "capture"),
        MoveRule(2, 0, "1st")
    ]
    moves = Moves(txt_path=None, board_size=(8, 8))
    moves.rules = rules

    result = moves.get_moves(1, 1, capture_only=True)
    assert result == [(2, 2)]

    result = moves.get_moves(1, 1, capture_only=False)
    assert result == [(2, 1), (3, 1)]

def test_get_moves_first_move_only():
    rules = [
        MoveRule(1, 0, ""),
        MoveRule(2, 0, "1st"),
    ]
    moves = Moves(txt_path=None, board_size=(8, 8))
    moves.rules = rules

    result = moves.get_moves(1, 1, first_move=True)
    assert result == [(3, 1)]

def test_iter_rules_returns_all():
    rules = [MoveRule(1, 0), MoveRule(0, 1), MoveRule(-1, -1)]
    moves = Moves(txt_path=None, board_size=(8, 8))
    moves.rules = rules

    all_rules = list(moves.iter_rules())
    assert all_rules == rules

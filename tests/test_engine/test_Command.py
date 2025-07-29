# tests/test_engine/test_Command.py
import pytest
from engine.Command import Command

def test_create_valid_move_command():
    cmd = Command.move("PW_1_1", (1, 1), (0, 1), player="WHITE")
    assert cmd.type == "Move"
    assert cmd.piece_id == "PW_1_1"
    assert cmd.params == [(1, 1), (0, 1)]
    assert cmd.player_id == "WHITE"

def test_create_invalid_command_type():
    with pytest.raises(ValueError):
        Command(0, "P1", "Fly", [])

def test_command_to_dict_and_back():
    original = Command.move("P1", (1, 1), (2, 1), player="BLACK")
    data = original.to_dict()
    restored = Command.from_dict(data)
    assert restored == original

def test_command_to_json_and_back():
    original = Command.capture("R1", (0, 0), (0, 7), "Q2", player="WHITE")
    json_str = original.to_json()
    restored = Command.from_json(json_str)

    # assert equality with tolerance to list/tuple mismatch
    assert restored.type == original.type
    assert restored.piece_id == original.piece_id
    assert tuple(restored.params[0]) == original.params[0]
    assert tuple(restored.params[1]) == original.params[1]
    assert restored.params[2] == original.params[2]
    assert restored.player_id == original.player_id

def test_clone_creates_deep_copy():
    cmd = Command.create_jump_command("N1", [(1, 1), (3, 3), (5, 5)], player_id="BLACK")
    clone = cmd.clone()
    assert clone.to_dict() == cmd.to_dict()
    assert clone is not cmd
    assert clone.params is not cmd.params


def test_str_format():
    cmd = Command.move("PW_1_1", (1, 1), (2, 1), player="WHITE", ts=60000)
    s = str(cmd)
    assert "Move PW_1_1" in s
    assert "WHITE" in s

def test_repr_format():
    cmd = Command.move("B2", (2, 2), (3, 3), player="BLACK", ts=12345)
    rep = repr(cmd)
    assert "Command(" in rep
    assert "piece_id='B2'" in rep

def test_negative_timestamp_raises():
    with pytest.raises(ValueError):
        Command(-5, "P1", "Move", [(1, 1), (2, 1)])


def test_non_list_params_raises():
    with pytest.raises(TypeError):
        Command(0, "P1", "Move", "not a list")

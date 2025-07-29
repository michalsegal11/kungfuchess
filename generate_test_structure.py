import os

structure = {
    "tests/test_pieces": ["test_Piece.py", "test_Pawn.py", "test_PieceFactory.py"],
    "tests/test_physics": ["test_Physics.py", "test_PhysicsFactory.py", "test_idle_physics.py", "test_slide_physics.py"],
    "tests/test_graphics": ["test_Graphics.py", "test_GraphicsFactory.py", "test_img.py", "test_mock_img.py"],
    "tests/test_engine": ["test_Moves.py", "test_Board.py", "test_State.py", "test_Command.py", "test_events.py"],
    "tests/test_ui": ["test_overlay.py", "test_input_handler.py", "test_move_log_ui.py"],
    "tests/test_game": ["test_game.py", "test_move_history.py", "test_constants.py"],
}

for folder, files in structure.items():
    os.makedirs(folder, exist_ok=True)
    
    # create __init__.py for each package
    init_path = os.path.join(folder, "__init__.py")
    if not os.path.exists(init_path):
        with open(init_path, "w", encoding="utf-8") as f:
            f.write("# Package initializer\n")

    for file in files:
        file_path = os.path.join(folder, file)
        if not os.path.exists(file_path):
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("# Auto-generated test file\n\n")
                f.write("def test_placeholder():\n")
                f.write("    assert True\n")

# root tests/__init__.py
root_init = os.path.join("tests", "__init__.py")
if not os.path.exists(root_init):
    with open(root_init, "w", encoding="utf-8") as f:
        f.write("# Root test package\n")

print("✅ All test folders, test files, and __init__.py files created successfully.")

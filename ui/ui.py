"""All OpenCV rendering: board → history panels → window."""
from __future__ import annotations
import numpy as np, cv2
from game.constants import *
from ui.score_ui import ScoreUI
from ui.window_icon import set_window_icon


# ──────────────────────────────────────────────────────────────

def draw(game):
    """Build full frame into `game.final_img` with background around the board and side panels."""

    board     = game.board
    board_w   = board.total_width_pix
    board_h   = board.total_height_pix

    start_x   = SIDE_W + PANEL_GAP  
    start_y   = TOP_H

    total_w = SIDE_W * 2 + PANEL_GAP * 2 + board_w
    total_h = TOP_H + board_h + BOT_H


    
    if game.background_img and game.background_img.img is not None:
        bg = cv2.resize(game.background_img.img, (total_w, total_h))
    else:
        bg = np.zeros((total_h, total_w, 3), dtype=np.uint8)


    temp_board = game.clone_board()
    for phase in ["static", "move", "jump"]:
        for p in game.pieces:
            if p.is_captured:
                continue
            st = p.current_state.state_name
            if (phase == "static" and st not in ("move", "jump")) or st == phase:
                p.draw_on_board(temp_board)


    def _circle(cell, color):
        x, y = board.get_cell_center_pixel(*cell)
        x += start_x
        y += start_y
        cv2.circle(temp_board.img.img, (x - start_x, y - start_y), 10, color, 2)

    _circle(tuple(game.white_cursor), (0, 255, 0))
    _circle(tuple(game.black_cursor), (0, 0, 255))


    board_img = temp_board.img.img
    bg[start_y:start_y + board_h, start_x:start_x + board_w] = board_img
    game.final_img = bg


    _draw_board_labels(bg, board, start_x, start_y)
    _draw_history_panels(game, start_x, board_w)
    game.overlay.draw(game.final_img)
    game.score_ui.draw(game.final_img)
    


def _draw_board_labels(bg, board, start_x, start_y):
    """Draw row (1–8) and column (A–H) labels around the board."""
    square_w = board.cell_W_pix
    square_h = board.cell_H_pix
    board_w = board.total_width_pix
    board_h = board.total_height_pix

    for i in range(8):
        letter = chr(ord('A') + i)
        x = start_x + i * square_w + square_w // 3
        y_top = start_y - 10
        y_bot = start_y + board_h + 25
        cv2.putText(bg, letter, (x, y_top), TXT_FONT, 0.5, (255, 255, 255), 1)
        cv2.putText(bg, letter, (x, y_bot), TXT_FONT, 0.5, (255, 255, 255), 1)

    for j in range(8):
        number = str(8 - j)
        y = start_y + j * square_h + square_h // 2 + 5
        x_left = start_x - 20
        x_right = start_x + board_w + 5
        cv2.putText(bg, number, (x_left, y), TXT_FONT, 0.5, (255, 255, 255), 1)
        cv2.putText(bg, number, (x_right, y), TXT_FONT, 0.5, (255, 255, 255), 1)


def _draw_history_panels(game, board_start_x, board_w):
    """Draw black and white history panels on both sides of the board."""
    img     = game.final_img
    board_h = game.board.total_height_pix

    def _draw_panel(x, moves, title):
        overlay = img[TOP_H:TOP_H + board_h, x:x + SIDE_W]
        overlay[:] = PANEL_BG
        cv2.rectangle(overlay, (0, 0), (SIDE_W - 1, board_h - 1), (255, 255, 255), 1)

        title_size = cv2.getTextSize(title, TXT_FONT, FONTSIZE_HEADER, 2)[0]
        center_x = (SIDE_W - title_size[0]) // 2
        cv2.putText(overlay, title, (center_x, 30), TXT_FONT, FONTSIZE_HEADER, TXT_HEADER_CLR, 2)

        y = 60
        for ts, nota in reversed(moves[-MAX_ROWS:]):
            cv2.putText(overlay, ts, (10, y), TXT_FONT, FONTSIZE_ROW, TXT_ROW_CLR, 1)
            cv2.putText(overlay, nota, (100, y), TXT_FONT, FONTSIZE_ROW, TXT_ROW_CLR, 1)
            y += LINE_H

    _draw_panel(board_start_x - PANEL_GAP - SIDE_W, game.move_history["BLACK"], "Black")
    _draw_panel(board_start_x + board_w + PANEL_GAP, game.move_history["WHITE"], "White")




# ---------------------------------------------------------------------------

def show(game):
    """Display frame + handle window/quit events. Returns False when finished."""


    if game.final_img is None:
        return True  # Nothing to show yet

    img = game.final_img.copy()
    y   = 30
    sw  = game.get_selected_white_piece()
    sb  = game.get_selected_black_piece()
    
    if sw:
        cv2.putText(img, f"White: {sw.piece_id}", (10, y), TXT_FONT, 0.7, (255, 255, 255), 2)
        y += 30
    if sb:
        cv2.putText(img, f"Black: {sb.piece_id}", (10, y), TXT_FONT, 0.7, (255, 255, 255), 2)

    cv2.namedWindow("Chess Game", cv2.WINDOW_NORMAL)

    if not getattr(show, "_icon_set", False):
        from pathlib import Path
        ROOT_DIR = Path(__file__).parents[2]
        ICO_PATH = ROOT_DIR / "assets" / "logo.ico"
        set_window_icon("Chess Game", str(ICO_PATH))
        show._icon_set = True          # מסמן: בוצע ✔
    # -------------------------------------------------


    _, _, w, h = cv2.getWindowImageRect("Chess Game")

    if w <= 0 or h <= 0:
        h, w = game.final_img.shape[:2]

    scaled_img = cv2.resize(game.final_img, (w, h), interpolation=cv2.INTER_LINEAR)
    cv2.imshow("Chess Game", scaled_img)

    key = cv2.waitKey(1) & 0xFF
    if key in (ord('q'), 27):           # q or ESC
        game.running = False
        return False
    try:
        return cv2.getWindowProperty("Chess Game", cv2.WND_PROP_VISIBLE) >= 1
    except cv2.error:
        return False

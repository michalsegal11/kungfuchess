"""
constants.py – Shared game constants for visuals, UI, and logic configuration.
"""

import cv2

# ─── UI COLORS ─────────────────────────────────────────────
PANEL_BG        = (45, 45, 45)       # Dark gray side panel
BOARD_BG        = (240, 240, 240)    # Background behind board (unused)
TXT_HEADER_CLR  = (255, 255, 255)    # White for player names / headers
TXT_ROW_CLR     = (220, 220, 220)    # Light gray for move rows
TXT_FOOTER_CLR  = (170, 170, 170)    # Darker gray for score footer

# ─── LAYOUT SETTINGS ───────────────────────────────────────
SIDE_W          = 350   # Width of side panel
TOP_H           = 120   # Top panel height
BOT_H           = 90    # Bottom panel height
PANEL_GAP       = 40    # Space between board and panels

# ─── FONT SETTINGS ─────────────────────────────────────────
TXT_FONT        = cv2.FONT_HERSHEY_SIMPLEX
FONTSIZE_HEADER = 0.9
FONTSIZE_ROW    = 0.45
FONTSIZE_FOOTER = 0.4
LINE_H          = 20
MAX_ROWS        = 18     # Max moves per panel

# ─── PGN LETTER MAPPING ────────────────────────────────────
# Used for converting piece types to standard chess notation.
PIECE_LETTER = {
    "K": "K",  # King
    "Q": "Q",  # Queen
    "R": "R",  # Rook
    "B": "B",  # Bishop
    "N": "N",  # Knight
    "P": "",   # Pawn is represented by empty string in PGN
}

# ─── SCORING LOGIC ─────────────────────────────────────────
# Material value per piece for scoring.
PIECE_VALUE = {
    "P": 1,   # Pawn
    "N": 3,   # Knight
    "B": 3,   # Bishop
    "R": 5,   # Rook
    "Q": 9,   # Queen
    "K": 0    # King has no material value
}


# ─── Player Input Direction Mapping ──────────────────────────────
# Maps keyboard keys to (row delta, col delta) for cursor movement
DIRS = {
    'UP': (-1, 0),     # Arrow key up
    'DOWN': (+1, 0),   # Arrow key down
    'LEFT': (0, -1),   # Arrow key left
    'RIGHT': (0, +1),  # Arrow key right
    'w': (-1, 0),      # Player 2 (WASD)
    's': (+1, 0),
    'a': (0, -1),
    'd': (0, +1),
}



import collections
import cv2
from game.constants import PANEL_BG, TXT_HEADER_CLR, TXT_ROW_CLR, TXT_FONT, LINE_H, FONTSIZE_HEADER, FONTSIZE_ROW, SIDE_W, TOP_H
from engine.events import MovePlayed, PieceTaken
import time

class MoveLogUI:
    def __init__(self, bus):
        self.rows = collections.deque(maxlen=50)
        bus.subscribe(MovePlayed, self._on_move)
        bus.subscribe(PieceTaken, self._on_capture)

    def _on_move(self, evt: MovePlayed):
        self.rows.appendleft((evt.time_ms, evt.move))


    def _on_capture(self, evt: PieceTaken):
        now_ms = int(time.time() * 1000)
        self.rows.appendleft((now_ms, f"{evt.piece_id} at {evt.cell}"))
        self.rows.appendleft((now_ms, "CAPTURE"))



    def draw(self, frame, side: str):
        """
        Draws move history on the screen side panel.

        Parameters:
        - frame: the OpenCV image (numpy array) to draw on
        - side: "left" or "right" – where to place the panel
        """
        x0 = 0 if side == "left" else frame.shape[1] - SIDE_W
        y0 = TOP_H + 10

        # Draw panel background
        cv2.rectangle(frame, (x0, 0), (x0 + SIDE_W, frame.shape[0]), PANEL_BG, -1)

        # Header
        cv2.putText(frame, "History", (x0 + 10, y0),
                    TXT_FONT, FONTSIZE_HEADER, TXT_HEADER_CLR, 1, cv2.LINE_AA)
        y = y0 + LINE_H

        # Rows
        for ts, move in list(self.rows)[:20]:  # show up to 20
            cv2.putText(frame, move, (x0 + 10, y),
                        TXT_FONT, FONTSIZE_ROW, TXT_ROW_CLR, 1, cv2.LINE_AA)
            y += LINE_H

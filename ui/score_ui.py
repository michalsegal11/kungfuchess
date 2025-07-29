from engine.events import PieceTaken
import cv2
from game.constants import TXT_FONT
import pygame.time

class ScoreUI:
    def __init__(self, bus):
        self.white = 0
        self.black = 0
        self.color_flash_until = {"WHITE": 0, "BLACK": 0}
        bus.subscribe(PieceTaken, self._on_capture)

    def _on_capture(self, evt: PieceTaken):
        now = pygame.time.get_ticks()
        if evt.by_color == "WHITE":
            self.white += evt.value
            self.color_flash_until["WHITE"] = now + 1000
        else:
            self.black += evt.value
            self.color_flash_until["BLACK"] = now + 1000



    def draw(self, frame):
        now = pygame.time.get_ticks()

        white_color = (0, 255, 0) if now < self.color_flash_until["WHITE"] else (255, 255, 255)
        black_color = (0, 0, 255) if now < self.color_flash_until["BLACK"] else (255, 255, 255)

        white_txt = f"White Score: {self.white}"
        black_txt = f"Black Score: {self.black}"

        font = TXT_FONT
        font_scale = 1.2
        thickness = 2
        margin = 30 
        y = 40       

        h, w = frame.shape[:2]
        (white_w, _), _ = cv2.getTextSize(white_txt, font, font_scale, thickness)
        
       
        cv2.putText(frame, black_txt, (margin, y), font, font_scale, black_color, thickness, cv2.LINE_AA)

       
        cv2.putText(frame, white_txt, (w - white_w - margin, y), font, font_scale, white_color, thickness, cv2.LINE_AA)

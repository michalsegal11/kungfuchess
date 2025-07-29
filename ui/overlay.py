from engine.events import GameStarted, GameEnded
import pygame
import cv2
from collections import deque

class Overlay:
    def __init__(self, bus):
        self.msg_queue = deque()
        self.current_msg = None
        self.until_ms = 0
        self.start_ticks = pygame.time.get_ticks()

        pygame.mixer.init()

        self.sounds = {
            "Ready":  pygame.mixer.Sound("snd/Ready.wav"),
            "Steady": pygame.mixer.Sound("snd/Steady.wav"),
            "Go!":    pygame.mixer.Sound("snd/Go!.wav"),
            "Win":    pygame.mixer.Sound("snd/win.wav")  
        }

        bus.subscribe(GameStarted, self._on_game_started)
        bus.subscribe(GameEnded, self._on_game_ended)

    def _on_game_started(self, e):
        self.queue_message("Ready", 1000)
        self.queue_message("Steady", 1000)
        self.queue_message("Go!", 1000)

    def _on_game_ended(self, e):
        winner_name =   ("White Wins!" if e.winner == "WHITE" else "Black Wins!")
        self.queue_message(winner_name, 3500)


    def queue_message(self, msg, duration=2000):
        self.msg_queue.append((msg, duration))


        
    def draw(self, frame):
        now = pygame.time.get_ticks()

        if self.current_msg is None and self.msg_queue:
            self.current_msg, dur = self.msg_queue.popleft()
            self.until_ms = now + dur

            # play the sound if it exists
            if self.current_msg in self.sounds:
                self.sounds[self.current_msg].play()
            elif "WINS" in self.current_msg.upper():
                self.sounds["Win"].play()


        if self.current_msg and now > self.until_ms:
            self.current_msg = None
            return

        if not self.current_msg:
            return

        h, w = frame.shape[:2]

       
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, h // 2 - 60), (w, h // 2 + 60), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)

       
        is_win = "WINS" in self.current_msg.upper()
        font_scale = 2.4 if is_win else 1.6
        color = (255, 215, 0) if is_win else (255, 255, 255)

        font = cv2.FONT_HERSHEY_SIMPLEX
        thickness = 3
        (text_w, text_h), _ = cv2.getTextSize(self.current_msg, font, font_scale, thickness)
        x = (w - text_w) // 2
        y = (h + text_h) // 2

        cv2.putText(frame, self.current_msg, (x, y), font, font_scale, color, thickness, cv2.LINE_AA)

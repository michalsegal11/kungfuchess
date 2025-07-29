import pygame.mixer as mx
from engine.events import MovePlayed, PieceTaken, JumpPlayed, ErrorPlayed,GameEnded
import pygame

class SoundFX:
    def __init__(self, bus, wav_move, wav_cap, wav_jump, wav_error):
        mx.init()
        self.snd_move  = mx.Sound(wav_move)
        self.snd_cap   = mx.Sound(wav_cap)
        self.snd_jump  = mx.Sound(wav_jump)
        self.snd_error = mx.Sound(wav_error)
        self.win_sound = pygame.mixer.Sound("snd/win.wav")


        bus.subscribe(MovePlayed,   lambda e: self.snd_move.play())
        bus.subscribe(PieceTaken,   lambda e: self.snd_cap.play())
        bus.subscribe(JumpPlayed,   lambda e: self.snd_jump.play())
        bus.subscribe(ErrorPlayed,  lambda e: self.snd_error.play())
        bus.subscribe(GameEnded,    lambda e: self.win_sound.play())


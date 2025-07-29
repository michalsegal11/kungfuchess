"""Keyboard → Queue.  Keeps Game clean."""
import threading, keyboard, queue

class InputHandler:
    def __init__(self, game):
        self.game   = game
        self.queue  = queue.Queue()
        self.thread = threading.Thread(target=self._hook, daemon=True)

    # ---------------------------------------------------------------------
    def _hook(self):
        def _cb(e):
            if e.event_type != 'down':
                return
            k = e.name
            if k in ('up', 'down', 'left', 'right', 'enter'):
                self.queue.put(('WHITE', k.upper()))
            elif k in ('w', 'a', 's', 'd', 'space'):
                self.queue.put(('BLACK', k))
            elif k in ('q', 'esc'):
                self.game.running = False
        keyboard.hook(_cb)
        keyboard.wait()   # block forever ← thread is daemonic

    # ---------------------------------------------------------------------
    def start(self):
        self.thread.start()
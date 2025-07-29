# ============================ Graphics.py ============================
import pathlib
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
import copy
from graphics.img import Img
from engine.Command import Command

class Graphics:
    """
    Handles frame-based animations using sprite sheets or sequences.
    """
    def __init__(self,
                 sprites_folder: pathlib.Path,
                 cell_size: tuple[int, int],
                 loop: bool = True,
                 fps: float = 6.0):
        self.folder = sprites_folder
        self.loop = loop
        self.fps = fps
        self.cell_size = cell_size
        if sprites_folder is not None:
            self.frames = self._load_frames()
        else:
            self.frames = []
        # self.frames: List[Img] = self._load_frames()
        self.current_frame_index = 0
        self.time_per_frame_ms = int(1000 / fps)
        self.last_update_time_ms = 0

    def _load_frames(self) -> List[Img]:
        """Load all image frames from the folder."""
        return [Img().read(f, self.cell_size) for f in sorted(self.folder.glob("*.png"))]

    def copy(self):
        """Create a shallow copy of the graphics object."""
        return copy.copy(self)

    def reset(self, cmd: Command, now_ms: int = None):
        """Reset animation to the first frame."""
        self.current_frame_index = 0
        self.last_update_time_ms = cmd.timestamp

    def update(self, now_ms: int):
        """Advance frame based on the current time."""
        elapsed = now_ms - self.last_update_time_ms
        self.last_update_time = now_ms 
        if elapsed >= self.time_per_frame_ms:
            frame_count = len(self.frames)
            if frame_count == 0:
                return
            self.last_update_time_ms = now_ms
            self.current_frame_index += 1
            if self.loop:
                self.current_frame_index %= frame_count
            else:
                self.current_frame_index = min(self.current_frame_index, frame_count - 1)

    def get_img(self) -> Img:
        """Return current frame's image."""
        if not self.frames:
            return Img()
        return self.frames[self.current_frame_index]


    def is_animation_finished(self) -> bool:
        if self.loop or not self.frames or self.start_time is None:
            return False
        elapsed = self.last_update_time - self.start_time
        total_duration = len(self.frames) * self.frame_duration
        return elapsed >= total_duration


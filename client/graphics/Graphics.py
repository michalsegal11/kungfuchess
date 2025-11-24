# ============================ Graphics.py ============================

from __future__ import annotations
import pathlib, copy, time
from typing import List
from client.graphics.img import Img
from core.engine.Command import Command


class Graphics:
    """Sprite-sequence animation (5 frames, loop-able)."""

    # ───────────────────────── ctor ────────────────────────────────
    def __init__(
        self,
        sprites_folder: pathlib.Path,
        cell_size: tuple[int, int],
        loop: bool = True,
        fps: float = 6.0,
    ) -> None:
        self.folder = sprites_folder
        self.loop = loop
        self.fps = fps
        self.cell_size = cell_size

        self.frames: List[Img] = self._load_frames()

        self.current_frame = 0
        self.ms_per_frame = int(1000 / fps)
        self.last_update_ms = 0
        self.start_time_ms = 0  # for is_animation_finished()

    # ───────────────────────── internals ───────────────────────────
    def _load_frames(self) -> List[Img]:
        """Load **exactly five** PNGs in lexicographic order."""
        if self.folder is None:
            return []

        files = sorted(self.folder.glob("*.png"))
        if len(files) < 5:
            raise RuntimeError(
                f"{self.folder}: expected 5 frames, found {len(files)}"
            )

        return [Img().read(f, self.cell_size) for f in files[:5]]

    # ───────────────────────── API ─────────────────────────────────
    def copy(self) -> "Graphics":
        """Shallow copy (frames are shared)."""
        return copy.copy(self)

    def reset(self, cmd: Command, *_):
        """Restart animation at frame 0."""
        self.current_frame = 0
        self.last_update_ms = cmd.timestamp
        self.start_time_ms = cmd.timestamp

    def update(self, now_ms: int):
        """Advance frame if enough time elapsed."""
        if not self.frames:
            return
        if now_ms - self.last_update_ms >= self.ms_per_frame:
            self.current_frame += 1
            if self.loop:
                self.current_frame %= len(self.frames)
            else:
                self.current_frame = min(self.current_frame, len(self.frames) - 1)
            self.last_update_ms = now_ms

    def get_img(self) -> Img:
        """Return current frame (Img wrapper)."""
        return self.frames[self.current_frame] if self.frames else Img()

    # ------------------------------------------------------------------
    def is_animation_finished(self) -> bool:
        """True iff non-looping animation reached last frame."""
        if self.loop or not self.frames:
            return False
        total = len(self.frames) * self.ms_per_frame
        return (time.time() * 1000 - self.start_time_ms) >= total

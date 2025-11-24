import math
import typing
from core.physics.Physics import Physics
from core.engine.Command import Command

class SlidePhysics(Physics):
    """
    Physics model for sliding movements between cells.
    """
    def __init__(self, start_cell, board, speed_m_s=1.0):
        super().__init__(start_cell, board, speed_m_s)
        self.current_cell = self.target_cell = start_cell
        self.current_pixel_pos = board.get_cell_center_pixel(*start_cell)
        self.start_time_ms = 0
        self.arrival_time_ms = 0 # time when we arrive at the target cell
        self._moving = False
        self._cmd: typing.Optional[Command] = None
        self._can_capture = True
        self._can_be_captured = True
        self.is_jumping = False

    def reset(self, cmd: Command):
        self._cmd = cmd
        self.start_time_ms = cmd.timestamp

        if cmd.type == "Move" and len(cmd.params) >= 2:
            self.current_cell = self._coerce(cmd.params[0])
            self.target_cell  = self._coerce(cmd.params[1])
            self.current_pixel_pos = self.board.get_cell_center_pixel(*self.current_cell)
            self._moving = True

        elif cmd.type == "Reset":
            self.current_cell = self.target_cell
            self.current_pixel_pos = self.board.get_cell_center_pixel(*self.current_cell)
            self._moving = False
            self.arrival_time_ms = cmd.timestamp  

        else:
            self._moving = False

    def update(self, now_ms: int):
        if not self._moving:
            return

        if self._arrived(now_ms):
            # הגענו ליעד
            self.current_cell = self.target_cell
            self.current_pixel_pos = self.board.get_cell_center_pixel(*self.current_cell)
            self.arrival_time_ms = now_ms  # ← עוד תעד זמן הגעה
            if hasattr(self, "_path") and self._path_idx + 1 < len(self._path):
                self._path_idx += 1
                self.start_cell = self.target_cell
                self.target_cell = self._path[self._path_idx]
                self.start_time_ms = now_ms
            else:
                self._moving = False
                return

        # חישוב מיקום ביניים
        duration = self._segment_duration_ms()
        prog = (now_ms - self.start_time_ms) / duration
        prog = self._ease_in_out(min(1.0, prog))
        src_px = self.board.get_cell_center_pixel(*self.start_cell)
        dst_px = self.board.get_cell_center_pixel(*self.target_cell)
        self.current_pixel_pos = (
            int(src_px[0] + (dst_px[0] - src_px[0]) * prog),
            int(src_px[1] + (dst_px[1] - src_px[1]) * prog),
        )

    def set_path(self, path: list[tuple[int, int]]):
        if not path or len(path) < 2:
            return
        self._path = path
        self._path_idx = 1
        self.start_cell = path[0]
        self.target_cell = path[1]
        self._moving = True

    def _segment_duration_ms(self) -> int:
        src_px = self.board.get_cell_center_pixel(*self.start_cell)
        dst_px = self.board.get_cell_center_pixel(*self.target_cell)
        dist_cells = self._cells_between(src_px, dst_px)
        sec = dist_cells / (self.SLIDE_CELLS_PER_SEC * max(0.01, self.speed_multiplier))
        return max(1, int(sec * 1000))

    def _arrived(self, now_ms: int) -> bool:
        return (now_ms - self.start_time_ms) >= self._segment_duration_ms()

    def _coerce(self, pos):
        return pos if isinstance(pos, tuple) else (int(pos[1]) - 1, ord(pos[0].lower()) - ord('a'))

    def _cells_between(self, src_px, dst_px):
        dx = dst_px[0] - src_px[0]
        dy = dst_px[1] - src_px[1]
        cell = (self.board.cell_W_pix + self.board.cell_H_pix) / 2
        return math.hypot(dx, dy) / cell

    def _ease_in_out(self, t):
        return 2*t*t if t < 0.5 else -1 + (4 - 2*t)*t
        

    def can_be_captured(self):     return self._can_be_captured
    def can_capture(self):         return self._can_capture
    def get_pos(self):             return self.current_pixel_pos
    def get_current_cell(self):    return self.current_cell
    def is_movement_finished(self):return not self._moving

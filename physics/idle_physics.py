# ============================ idle_physics.py ============================
from physics.Physics import Physics

class IdlePhysics(Physics):
    """
    Physics model for stationary states (e.g., idle or rest).
    """
    def __init__(self, start_cell, board, speed_m_s: float = 1.0):
        super().__init__(start_cell, board, speed_m_s)
        self.current_cell      = start_cell
        self.current_pixel_pos = board.get_cell_center_pixel(*start_cell)
        self._moving = False
        self.is_jumping = False
        self.start_time_ms = 0

    def reset(self, cmd):
        self._moving = False

    def update(self, now_ms):
        pass  # No movement in idle

    def copy(self):
        return type(self)(self.start_cell, self.board, self.speed_multiplier)

    def can_be_captured(self): return self._can_be_captured
    def can_capture(self):     return self._can_capture
    def get_pos(self):         return self.current_pixel_pos
    def get_current_cell(self):return self.current_cell
    def is_movement_finished(self): return True
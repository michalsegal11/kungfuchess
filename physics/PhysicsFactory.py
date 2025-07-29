# ============================ PhysicsFactory.py ============================
from physics.idle_physics import IdlePhysics
from physics.slide_physics import SlidePhysics
from typing import Tuple
from engine.Board import Board

class PhysicsFactory:
    """
    Creates physics behavior objects based on state name and configuration.
    """
    def __init__(self, board: Board):
        self.board = board

    def create(self,
               state_name: str,
               start_cell: Tuple[int, int],
               opts: dict):
        """
        Selects and instantiates a physics class based on state.

        Parameters:
            state_name – e.g., "idle", "move", "jump"
            start_cell – initial cell (row, col)
            opts       – dictionary with optional config:
                         {"speed": float, "can_be_captured": bool, "can_capture": bool}

        Returns:
            An initialized subclass of Physics.
        """
        speed       = opts.get("speed", 1.0)
        capturable  = opts.get("can_be_captured", True)
        can_capture = opts.get("can_capture",     True)

        if state_name in ("idle", "short_rest", "long_rest"):
            phys = IdlePhysics(start_cell, self.board, speed)
        else:
            phys = SlidePhysics(start_cell, self.board, speed)

        phys.set_capturable(capturable)
        phys.set_can_capture(can_capture)

        print(f"[PhysicsFactory] {state_name}: {phys.__class__.__name__}")
        return phys

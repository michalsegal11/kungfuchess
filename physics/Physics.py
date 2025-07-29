# ============================ Physics.py ============================
from abc import ABC, abstractmethod
from typing import Tuple
from engine.Board import Board
from engine.Command import Command

class Physics(ABC):
    """
    Abstract base class for defining physics behaviors of game pieces.
    """
    SLIDE_CELLS_PER_SEC = 4.0

    def __init__(self,
                 start_cell: Tuple[int, int],
                 board: Board,
                 speed_m_s: float = 1.0):
        self.start_cell       = start_cell
        self.board            = board
        self.speed_multiplier = speed_m_s
        self._can_be_captured = True
        self._can_capture     = True

    def set_capturable(self, flag: bool):
        self._can_be_captured = flag

    def set_can_capture(self, flag: bool):
        self._can_capture = flag

    def can_be_captured(self) -> bool:
        return self._can_be_captured

    def can_capture(self) -> bool:
        return self._can_capture

    @abstractmethod
    def reset(self, cmd: Command) -> None: ...

    @abstractmethod
    def update(self, now_ms: int) -> None: ...

    @abstractmethod
    def get_pos(self) -> Tuple[int, int]: ...

    @abstractmethod
    def get_current_cell(self) -> Tuple[int, int]: ...

    @abstractmethod
    def is_movement_finished(self) -> bool: ...
"""Finite-state-machine node for a single piece animation / behaviour."""
from __future__ import annotations
from typing import Dict, Optional, Sequence

from core.engine.Command import Command
from core.engine.Moves   import Moves
try:
    from client.graphics.Graphics import Graphics
except ModuleNotFoundError:
    class Graphics:
        def __init__(self, *_, **__): pass
        def copy(self):               return self
        def reset(self, *_, **__):    pass
        def update(self, *_, **__):   pass
        frame_duration: int = 0
        loop: bool = True
        
from core.physics.Physics import Physics        
from core.engine.events  import StateChanged

SHORT_REST_MS = 1_000       # ms
LONG_REST_MS  = 3_000       # ms


# --------------------------------------------------------------------- helpers
def _bus(state):
    game = getattr(state.physics.board, "game", None)
    return getattr(game, "bus", None)


# --------------------------------------------------------------------- State
class State:
    """A single node in the per-piece FSM."""

    def __init__(
        self,
        moves:     Moves,
        graphics:  Graphics,
        physics:   Physics,
        cfg:       dict | None = None,
    ) -> None:

        cfg = cfg or {}
        self.cfg = cfg

        self.moves, self.physics = moves, physics
        self.graphics = graphics or Graphics()

        self.state_name      = cfg.get("state_name", "idle")
        self.piece_id: Optional[str] = None

        rest_dur = {"short_rest": SHORT_REST_MS, "long_rest": LONG_REST_MS}
        self.min_duration_ms  = rest_dur.get(self.state_name, cfg.get("min_duration_ms", 0))
        self.next_state_name  = cfg.get("physics", {}).get("next_state_when_finished", "")
        if self.next_state_name == self.state_name:
            self.next_state_name = ""

        # physics tweaks
        spd = cfg.get("physics", {}).get("speed_m_per_sec")
        if spd is not None:
            self.physics.speed_multiplier = spd / Physics.SLIDE_CELLS_PER_SEC
        self.physics.set_capturable(cfg.get("physics", {}).get("can_be_captured", True))
        self.physics.set_can_capture(cfg.get("physics", {}).get("can_capture",   True))

        # graphics tweaks
        fps = cfg.get("graphics", {}).get("frames_per_sec") or cfg.get("graphics", {}).get("fps")
        if fps:
            if self.graphics:   
                self.graphics.frame_duration = int(1000 / float(fps))
        if self.graphics:   
            self.graphics.loop = cfg.get("graphics", {}).get("is_loop", cfg.get("graphics", {}).get("loop", True))


        # runtime fields
        self.transitions : Dict[str, "State"] = {}
        self.current_command : Command | None = None
        self.state_start_time: int | None = None

    # ------------------------------------------------ deep-copy
    def _clone(self, memo: Dict[int, "State"]) -> "State":
        if id(self) in memo:
            return memo[id(self)]
        phys_new = type(self.physics)(
            self.physics.start_cell,
            self.physics.board,
            getattr(self.physics, "speed_multiplier", 1.0))
        phys_new.set_capturable(self.physics.can_be_captured())
        phys_new.set_can_capture(self.physics.can_capture())

        graphics_copy = self.graphics.copy() if self.graphics else None
        new = State(self.moves, graphics_copy, phys_new, self.cfg.copy())
        memo[id(self)] = new

        new.next_state_name = self.next_state_name
        for ev, tgt in self.transitions.items():
            new.transitions[ev] = tgt._clone(memo)
        return new

    def copy(self) -> "State":
        return self._clone({})

    # ------------------------------------------------ transitions
    def set_transition(self, event: str, target: "State") -> None:
        self.transitions[event] = target

    # ------------------------------------------------ lifecycle
    def reset(self, cmd: Command) -> None:
        """Enter this state at server-time cmd.timestamp."""
        self.current_command  = cmd
        self.state_start_time = cmd.timestamp
        if self.graphics:
            self.graphics.reset(cmd, cmd.timestamp)
        self.physics.reset(cmd)

        bus = _bus(self)
        if bus:
            # שולח את השם של המצב אליו נכנסנו
            bus.publish(StateChanged(self.piece_id, self.state_name, cmd.timestamp))

    # ------------------------------------------------ external trigger
    _EVENT_BY_CMD = {"Move": "move", "Jump": "jump", "Attack": "attack",
                     "Capture": "capture", "Special": "special"}

    def get_state_after_command(self, cmd: Command, now_ms: int) -> "State":
        ev = self._EVENT_BY_CMD.get(cmd.type, "unknown")
        if ev not in self.transitions or not self._can_leave(now_ms):
            return self

        nxt = self.transitions[ev]
        if ev in ("move", "jump"):
            nxt.physics.current_cell      = self.physics.current_cell
            nxt.physics.current_pixel_pos = self.physics.current_pixel_pos
        else:
            nxt.physics = self.physics

        server_cmd = Command(now_ms, cmd.piece_id, cmd.type, cmd.params)
        nxt.reset(server_cmd)
        return nxt

    # ------------------------------------------------ update loop
    def update(self, now_ms: int) -> "State":
        if self.graphics:   
            self.graphics.update(now_ms)
        self.physics.update(now_ms)
        return self._auto_transition(now_ms)

    # ------------------------------------------------ automatic chain
    def _auto_transition(self, now_ms: int) -> "State":
        finished = (not getattr(self.physics, "_moving", False)) and self._can_leave(now_ms)
        if finished and self.next_state_name:
            nxt = self.transitions.get(self.next_state_name)
            if nxt:
                cell = self.physics.get_current_cell()
                server_cmd = Command(now_ms, self.piece_id or "?", "Reset", [cell])
                nxt.reset(server_cmd)
                bus = _bus(self)
                if bus:
                    bus.publish(StateChanged(self.piece_id, self.next_state_name, now_ms))
                return nxt

        return self

    # ------------------------------------------------ helpers
    def _can_leave(self, now_ms: int) -> bool:
        elapsed_time = now_ms - (self.state_start_time or 0)
        return elapsed_time >= self.min_duration_ms

    def get_current_image(self):
        if self.graphics:   
            return self.graphics.get_img()

    def get_current_position(self):
        return self.physics.get_pos()

    def get_cell(self):
        return self.physics.get_current_cell()

    def start_move(self, dest: tuple[int,int] | Sequence[tuple[int,int]], now_ms: int) -> None:
        if isinstance(dest, Sequence) and dest and isinstance(dest[0], Sequence):
            path = list(dest)
            final_cell = path[-1]
            self.physics.set_path(path)
        else:
            final_cell = dest
            self.physics.set_path([self.physics.get_current_cell(), final_cell])

        self.physics.start_time_ms = now_ms
        self.physics._moving       = True
        self.physics.current_command = Command(
            now_ms, self.piece_id or "?", "Move",
            [self.physics.get_current_cell(), final_cell]
        )

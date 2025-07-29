# ==============================  state.py  ==============================


from __future__ import annotations
from typing import Dict, Optional, Tuple
from typing import Sequence   


from engine.Command  import Command
from engine.Moves import Moves
from graphics.Graphics import Graphics
from physics.Physics  import Physics

# --------------------------------------------------------------------- 
DEBUG_STATE = False
def _lg(*msg):         
    if DEBUG_STATE:
        print(*msg)


SHORT_REST_MS = 1000# short_rest – 
LONG_REST_MS  = 3000 # long_rest –

# --------------------------------------------------------------------- 
class State:
    """Node in a finite‑state‑machine that represents one animation / behaviour."""

    # ───────────────────────────── ctor ───────────────────────────────
    def __init__(self,
                 moves:     Moves,
                 graphics:  Graphics,
                 physics:   Physics,
                 cfg:       dict | None = None):

        cfg       = cfg or {}
        phys_cfg  = cfg.get("physics",  {})
        gfx_cfg   = cfg.get("graphics", {})

        # core components
        self.moves     = moves
        self.graphics  = graphics
        self.physics   = physics

        # basic metadata
        self.state_name      = cfg.get("state_name", "idle")


        REST_DURATION = {          # ➊ טבלה אחת ברורה
            "short_rest": SHORT_REST_MS,
            "long_rest":  LONG_REST_MS,
        }


                # ----- min-duration -----
        cfg_dur = cfg.get("min_duration_ms")     
        self.min_duration_ms = REST_DURATION.get(      
            self.state_name,
            cfg_dur if cfg_dur is not None else 0  
       )


        # self.min_duration_ms = cfg.get("min_duration_ms", 0)

        # automatic‑next
        nxt = phys_cfg.get("next_state_when_finished", "")
        self.next_state_name = "" if nxt == self.state_name else nxt

        # configure physics speed
        spd = phys_cfg.get("speed_m_per_sec")
        if spd is not None:
            self.physics.speed_multiplier = spd / Physics.SLIDE_CELLS_PER_SEC

        # capture flags
        self.physics.set_capturable( phys_cfg.get("can_be_captured", True) )
        self.physics.set_can_capture( phys_cfg.get("can_capture",   True) )

        # graphics FPS / looping
        fps = gfx_cfg.get("frames_per_sec") or gfx_cfg.get("fps")
        if fps:
            self.graphics.frame_duration = int(1000 / float(fps))
        self.graphics.loop = gfx_cfg.get("is_loop", gfx_cfg.get("loop", True))

        # graph helpers
        self.cfg              = cfg
        self.direction        = "down"
        self.piece_id: Optional[str] = None

        self.transitions: Dict[str, State] = {}
        self.current_command: Command | None = None
        self.state_start_time: int | None = None

    # ───────────────────── deep‑copy (FSM clone) ──────────────────────
    def _clone(self, memo: Dict[int, State]) -> State:
        if id(self) in memo:
            return memo[id(self)]

        phys_cls = type(self.physics)

        try:
           
            phys_new = phys_cls(self.physics.start_cell,
                                self.physics.board,
                                self.physics.speed_multiplier)
        except TypeError:
          
            phys_new = phys_cls(self.physics.start_cell,
                                self.physics.board)

        phys_new.set_capturable(self.physics.can_be_captured())
        phys_new.set_can_capture(self.physics.can_capture())

        new = State(self.moves,
                    self.graphics.copy(),
                    phys_new,
                    self.cfg.copy())
        memo[id(self)] = new

        for ev, tgt in self.transitions.items():
            new.transitions[ev] = tgt._clone(memo)
        return new

    def copy(self) -> State:
        """deep‑copy entire reachable FSM sub‑graph."""
        return self._clone({})

    # ───────────────────────── transitions ────────────────────────────
    def set_transition(self, event: str, target: State) -> None:
        
        self.transitions[event] = target

    # ───────────────────────── lifecycle ──────────────────────────────
    def reset(self, cmd: Command) -> None:
        """restart graphics & physics for *this* state."""
        self.current_command  = cmd
        self.state_start_time = cmd.timestamp
        self.graphics.reset(cmd, cmd.timestamp)   
        self.physics.reset(cmd)
        _lg(f"[{self.piece_id}] reset ⇒ {self.state_name}")

    # --- helpers ------------------------------------------------------
    _EVENT_BY_CMD = {
        "Move":   "move",
        "Jump":   "jump",
        "Attack": "attack",
        "Capture":"capture",
        "Special":"special",
    }
    def _command_to_event(self, cmd: Command) -> str:
        return self._EVENT_BY_CMD.get(cmd.type, "unknown")

    def _can_leave(self, now_ms: int) -> bool:
        return (self.state_start_time is None or
                now_ms - self.state_start_time >= self.min_duration_ms)

    # --- external trigger --------------------------------------------
    def get_state_after_command(self, cmd: Command, now_ms: int) -> State:
        ev = self._command_to_event(cmd)
        if ev not in self.transitions or not self._can_leave(now_ms):
            return self

        nxt = self.transitions[ev]

        # share / sync physics
        if ev in ("move", "jump"):                         # need SlidePhysics
            nxt.physics.current_cell      = self.physics.current_cell
            nxt.physics.current_pixel_pos = self.physics.current_pixel_pos
        else:                                              # idle / rest
            nxt.physics = self.physics                     # reuse same object

        nxt.reset(cmd)
        _lg(f"[{self.piece_id}] {self.state_name} --{ev}→ {nxt.state_name}")
        return nxt

    # ───────────────────── update‑loop entrypoint ─────────────────────
    def update(self, now_ms: int) -> State:
        self.graphics.update(now_ms)
        self.physics.update(now_ms)
        
        return self._auto_transition(now_ms)

    # --- automatic chain (move → rest → idle …) -----------------------
    def _auto_transition(self, now_ms: int) -> State:
        finished = (not getattr(self.physics, "_moving", False)) \
                   and self._can_leave(now_ms)  
        if finished and self.next_state_name:
            nxt = self.transitions.get(self.next_state_name)
            if nxt:
                nxt.physics = self.physics
                dummy = Command(now_ms, self.piece_id or "?", "Reset", [])
                nxt.reset(dummy)
                return nxt
        return self

    # ────────────────────────── helpers ───────────────────────────────
    def get_current_image(self):              return self.graphics.get_img()
    def get_current_position(self) -> tuple[int,int]:
        return self.physics.get_pos()
    def get_cell(self) -> tuple[int,int]:
        return self.physics.get_current_cell()
    


    # ─────────────────────── helpers ────────────────────────────

    def start_move(self,
                dest: tuple[int,int] | Sequence[tuple[int,int]],
                now_ms: int) -> None:
        """
        dest – או תא יחיד (move רגיל) או רשימת תאים (path לקפיצה).
        """
        if isinstance(dest, (list, tuple)) and dest and isinstance(dest[0], (list, tuple)):
           
            path: list[tuple[int,int]] = list(dest)
            self.physics.set_path(path)
            final_cell = path[-1]
        else:
           
            final_cell = dest
            self.physics.set_path([self.physics.get_current_cell(), final_cell])

        self.physics.start_time_ms = now_ms
        self.physics.is_moving     = True
        self.physics.current_command = Command(
            now_ms, self.piece_id or "?", "Move", [self.physics.get_current_cell(), final_cell]
        )




# =====================================================================

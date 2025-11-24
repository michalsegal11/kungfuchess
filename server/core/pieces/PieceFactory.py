# NOTE:
# The following module was reconstructed from a packed markdown representation.
# Some fences introduced a stray "python" marker at the top of the file; this
# line is now commented out to avoid a NameError when the module is imported.
# Additionally, the FSM construction has been enhanced to ensure that pieces
# correctly transition from movement states into appropriate rest states.
# See the section below for details.
# python
import pathlib, json
from pathlib                  import Path
from typing                   import Dict, Tuple

from core.engine.Board             import Board
try:
    from client.graphics.GraphicsFactory import GraphicsFactory  # לקוח
except ModuleNotFoundError:
    class GraphicsFactory:               # שרת – מחלקה ריקה
        def load(self, *_, **__):
            return None
from core.engine.Moves             import Moves
from core.physics.PhysicsFactory   import PhysicsFactory
from core.pieces.Piece             import Piece
from core.pieces.Pawn              import Pawn
from core.engine.State             import State



DEBUG_FACTORY = True
def _dbg(*a):
    if DEBUG_FACTORY:
        print(*a)


def _load_json(path: pathlib.Path, default: dict | None = None) -> dict:
    """Safely load a JSON file. If missing or invalid, return a default dict."""
    if not path.exists():
        return default or {}
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as e:
        print(f"[PieceFactory] JSON error in {path}: {e}")
        return default or {}


class PieceFactory:
    """
    Responsible for loading, managing, and creating game pieces
    using a state machine template for each type.
    """

    def __init__(self, board: Board, pieces_root: pathlib.Path) -> None:
        self.board            = board
        self.pieces_root      = pieces_root
        self.graphics_factory = GraphicsFactory()
        self.physics_factory  = PhysicsFactory(board)
        self.piece_templates : Dict[str, State] = {}
        self._load_piece_templates()

    def _load_piece_templates(self) -> None:
        if not self.pieces_root.exists():
            print(f"[PieceFactory] dir not found: {self.pieces_root}")
            return

        for piece_dir in self.pieces_root.iterdir():
            if not piece_dir.is_dir():
                continue
            p_type = piece_dir.name.upper()
            try:
                self.piece_templates[p_type] = self._build_state_machine(piece_dir, p_type)
                _dbg(f"Loaded piece template: {p_type}")
            except Exception as e:
                print(f"Failed to load piece {p_type}: {e}")

    def _build_state_machine(self, piece_dir: Path, p_type: str) -> State:
        states : dict[str, State] = {}
        states_root = piece_dir / "states"

        for state_dir in states_root.iterdir():
            if not state_dir.is_dir():
                continue

            cfg       = _load_json(state_dir / "config.json")
            name      = state_dir.name
            cfg['state_name'] = name

            cell_size = (self.board.cell_W_pix, self.board.cell_H_pix)
            graphics  = self.graphics_factory.load(
                state_dir / "sprites",
                cfg.get("graphics", {}),
                cell_size)

            phys_cfg  = cfg.get("physics", {})
            speed_m_s = phys_cfg.get("speed_m_per_sec", 0.0)

            physics   = self.physics_factory.create(
                state_name = name,
                start_cell = (0, 0),
                opts       = {
                    "speed": speed_m_s,
                    "can_be_captured": phys_cfg.get("can_be_captured", True),
                    "can_capture":     phys_cfg.get("can_capture",   True),
                })

            invert_y = piece_dir.name.endswith("B") # Black pieces invert Y-axis
            moves = Moves(piece_dir / "moves.txt", (self.board.W_cells, self.board.H_cells), invert_y)


            st = State(moves, graphics, physics, cfg)
            states[name] = st

        # Link automatic transitions
        for st in states.values():
            nxt_name = st.next_state_name
            if nxt_name and nxt_name in states:
                st.set_transition(nxt_name, states[nxt_name])

        # --- Manual fallback transitions ---------------------------------
        if "idle" in states and "move" in states:
            states["idle"].set_transition("move", states["move"])
        if "idle" in states and "jump" in states:
            states["idle"].set_transition("jump", states["jump"])

        # >>> הוספה ↓↓↓ ----------------------------------------------------
        if "long_rest" in states and "idle" in states:
            # כשה-long_rest מסתיים, לעבור אוטומטית ל-idle
            states["long_rest"].next_state_name = "idle"
            states["long_rest"].set_transition("idle", states["idle"])

        if "short_rest" in states and "idle" in states:
            states["short_rest"].next_state_name = "idle"
            states["short_rest"].set_transition("idle", states["idle"])
        # <<< --------------------------------------------------------------
        # When a jump finishes, pieces should recover for a short period before
        # returning to idle.  If the JSON configuration omitted this rule, add
        # sensible defaults here: assign the next state and create the
        # corresponding transition.  Without this fallback, the client will
        # never see the short_rest → idle sequence and pieces remain stuck in
        # the jump state.
        if "jump" in states and "short_rest" in states:
            # Only override if the author didn't specify a target state
            if not states["jump"].next_state_name:
                states["jump"].next_state_name = "short_rest"
            # Ensure there is a transition entry so State.get_state_after_command
            # can resolve it.
            if "short_rest" not in states["jump"].transitions:
                states["jump"].set_transition("short_rest", states["short_rest"])

        # New fallback: ensure that a completed move automatically enters
        # a long rest state.  Without this, pieces remain in the "move"
        # state indefinitely, preventing selection and blocking further
        # commands.  This behaviour implements the expected sequence
        # [move → long_rest → idle] in the absence of explicit configuration.
        if "move" in states and "long_rest" in states:
            # Assign default next_state_name only if missing
            if not states["move"].next_state_name:
                states["move"].next_state_name = "long_rest"
            # Create the transition mapping if it doesn't already exist
            if "long_rest" not in states["move"].transitions:
                states["move"].set_transition("long_rest", states["long_rest"])


        
        

        if DEBUG_FACTORY:
            for nm, st in states.items():
                _dbg(f"{piece_dir.name}:{nm} auto→{st.next_state_name} events={list(st.transitions)}")

        return states.get("idle") or next(iter(states.values()))

    def _clone_machine(self, root: State) -> State:
        return root.copy()

    def create_piece(self, p_type: str, cell: Tuple[int, int]) -> Piece:
        if len(p_type) != 2:
            raise ValueError(f"Invalid piece code: {p_type}")

        kind, color = p_type[0], p_type[1] 

        template_key = f"{kind}{color}" 

        if template_key not in self.piece_templates:
            raise ValueError(f"Unknown piece type: {template_key}")

        state = self._clone_machine(self.piece_templates[template_key])
        piece_id = f"{p_type}_{cell[0]}_{cell[1]}"

        seen: set[int] = set()
        def assign(st: State):
            if id(st) in seen:
                return
            seen.add(id(st))
            st.piece_id = piece_id
            for nxt in st.transitions.values():
                assign(nxt)
        assign(state)

        state.physics.start_cell        = cell
        state.physics.current_cell      = cell
        state.physics.current_pixel_pos = self.board.get_cell_center_pixel(*cell)

        forward = -1 if color == "BLACK" else +1
        if kind == "P":
            return Pawn(piece_id, state, state.moves, forward=forward)

        return Piece(piece_id, state, state.moves)

import pathlib, json
from pathlib                  import Path
from typing                   import Dict, Tuple

from engine.Board             import Board
from graphics.GraphicsFactory import GraphicsFactory
from engine.Moves             import Moves
from physics.PhysicsFactory   import PhysicsFactory
from pieces.Piece             import Piece
from pieces.Pawn              import Pawn
from engine.State             import State



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

        # Manual fallback transitions
        if "idle" in states and "move" in states:
            states["idle"].set_transition("move", states["move"])
        if "idle" in states and "jump" in states:
            states["idle"].set_transition("jump", states["jump"])
        if "long_rest" in states and "idle" in states:
            states["long_rest"].set_transition("idle", states["idle"])
        if "jump" in states and "short_rest" in states:
            states["jump"].next_state_name = states["jump"].next_state_name or "short_rest"

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

# ============================ Moves.py ============================
from __future__ import annotations
import pathlib
from dataclasses import dataclass
from typing import List, Tuple, Iterable

@dataclass(frozen=True)
class MoveRule:
    dr: int
    dc: int
    tag: str = ""

    def target_cell(self, r: int, c: int) -> Tuple[int, int]:
        return (r + self.dr, c + self.dc)

class Moves:
    def __init__(self, txt_path: pathlib.Path | None, board_size: Tuple[int, int], invert_y: bool = False):
        self.rows, self.cols = board_size
        self.rules: list[MoveRule] = []
        self.invert_y = invert_y

        if txt_path and txt_path.exists():
            self._load_moves_from_file(txt_path)
        else:
            self.rules = [MoveRule(1, 0), MoveRule(-1, 0), MoveRule(0, 1), MoveRule(0, -1)]



    def _load_moves_from_file(self, txt_path: pathlib.Path) -> None:
        self.rules.clear()
        with open(txt_path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#"): continue
                move_part, *tag_part = line.split(":", 1)
                if "," not in move_part: continue
                try:
                    dr_txt, dc_txt = move_part.split(",", 1)
                    dr = int(dr_txt.strip())
                    
                    dc = int(dc_txt.strip())
                except ValueError:
                    continue
                tag = tag_part[0].strip() if tag_part else ""
                self.rules.append(MoveRule(dr, dc, tag))
            if self.invert_y:
                self.rules = [MoveRule(-r.dr, r.dc, r.tag) for r in self.rules]


    def get_moves(self, r: int, c: int,
                  *, capture_only: bool | None = None,
                     first_move: bool | None = None) -> List[Tuple[int, int]]:
        def rule_ok(rule: MoveRule) -> bool:
            if capture_only is True and rule.tag != "capture": return False
            if capture_only is False and rule.tag == "capture": return False
            if first_move is True and rule.tag != "1st": return False
            return True

        moves = []
        for rule in self.rules:
            if not rule_ok(rule): continue
            nr, nc = rule.target_cell(r, c)
            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                moves.append((nr, nc))
        return moves

    def iter_rules(self) -> Iterable[MoveRule]:
        return iter(self.rules)


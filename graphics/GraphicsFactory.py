# ============================ GraphicsFactory.py ============================
from __future__ import annotations
import pathlib
from typing import Mapping, Any
from graphics.Graphics import Graphics

class GraphicsFactory:
    """
    Builds a Graphics object from sprite folder and configuration dictionary.
    """
    def load(self,
             sprites_dir: pathlib.Path,
             cfg: Mapping[str, Any] | None,
             cell_size: tuple[int, int]) -> Graphics:
        """
        Load graphics sprites from a directory with config.

        Parameters:
            sprites_dir – Directory containing the sprite images.
            cfg         – Configuration dictionary (fps, loop, subfolder).
            cell_size   – Final resized frame size in pixels.

        Returns:
            Graphics – Initialized object with frames and animation settings.
        """
        cfg = cfg or {}
        fps = float(cfg.get("fps", 6.0))
        loop = bool(cfg.get("loop", True))

        subfolder = cfg.get("sprites_folder")
        if subfolder:
            sprites_dir = sprites_dir / str(subfolder)

        if not sprites_dir.exists():
            raise FileNotFoundError(f"Sprites folder not found: {sprites_dir}")

        return Graphics(sprites_folder=sprites_dir,
                        cell_size=cell_size,
                        loop=loop,
                        fps=fps)
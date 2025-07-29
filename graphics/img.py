# ============================ img.py ============================
from __future__ import annotations
import pathlib
import cv2
import numpy as np

class Img:
    """
    Wrapper around OpenCV image, providing loading, drawing, and utility methods.
    """
    def __init__(self):
        self.img = None

    def read(self, path: str | pathlib.Path,
             size: tuple[int, int] | None = None,
             keep_aspect: bool = False,
             interpolation: int = cv2.INTER_AREA) -> Img:
        """
        Load image from file and optionally resize.
        
        Parameters:
            path          – file path to load from.
            size          – (w, h) tuple or None.
            keep_aspect   – preserve aspect ratio.
            interpolation – OpenCV interpolation mode.
        """
        path = str(path)
        self.img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        if self.img is None:
            raise FileNotFoundError(f"Cannot load image: {path}")

        if size:
            target_w, target_h = size
            h, w = self.img.shape[:2]
            if keep_aspect:
                scale = min(target_w / w, target_h / h)
                new_w, new_h = int(w * scale), int(h * scale)
            else:
                new_w, new_h = target_w, target_h
            self.img = cv2.resize(self.img, (new_w, new_h), interpolation=interpolation)
        return self

    def draw_on(self, other_img, x, y):
        """Overlay self on top of another image at position (x,y)."""
        if self.img is None or other_img.img is None:
            raise ValueError("Images not loaded")

        x, y = int(x), int(y)
        h, w = self.img.shape[:2]
        H, W = other_img.img.shape[:2]

        if x < 0 or y < 0 or x + w > W or y + h > H:
            src_x_start = max(0, -x)
            src_y_start = max(0, -y)
            src_x_end = min(w, W - x)
            src_y_end = min(h, H - y)

            dst_x_start = max(0, x)
            dst_y_start = max(0, y)

            if src_x_end <= src_x_start or src_y_end <= src_y_start:
                return

            src_img = self.img[src_y_start:src_y_end, src_x_start:src_x_end]
            h, w = src_img.shape[:2]
            x, y = dst_x_start, dst_y_start
        else:
            src_img = self.img

        if len(src_img.shape) != len(other_img.img.shape):
            if src_img.shape[2] == 3 and other_img.img.shape[2] == 4:
                src_img = cv2.cvtColor(src_img, cv2.COLOR_BGR2BGRA)
            elif src_img.shape[2] == 4 and other_img.img.shape[2] == 3:
                src_img = cv2.cvtColor(src_img, cv2.COLOR_BGRA2BGR)

        roi = other_img.img[y:y + h, x:x + w]

        if src_img.shape[2] == 4:
            b, g, r, a = cv2.split(src_img)
            mask = a.astype(float) / 255.0
            for c in range(min(3, roi.shape[2])):
                roi[..., c] = (1 - mask) * roi[..., c] + mask * src_img[..., c]
        else:
            other_img.img[y:y + h, x:x + w] = src_img

    def put_text(self, txt, x, y, font_size, color=(255, 255, 255, 255), thickness=1):
        if self.img is None:
            raise ValueError("Image not loaded")
        cv2.putText(self.img, txt, (x, y), cv2.FONT_HERSHEY_SIMPLEX, font_size, color, thickness, cv2.LINE_AA)

    def show(self):
        if self.img is None:
            raise ValueError("Image not loaded")
        cv2.imshow("Chess Board", self.img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
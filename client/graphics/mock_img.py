# ============================ mock_img.py ============================
from graphics.img import Img

class MockImg(Img):
    """Mock version of Img class, for testing graphics without rendering."""
    traj     : list[tuple[int,int]]  = []
    txt_traj : list[tuple[tuple[int,int],str]] = []

    def __init__(self):
        self.img = None
        self.width = 100
        self.height = 100

    def read(self, path, *_, **__):
        self.width = 64
        self.height = 64
        return self

    def draw_on(self, other, x, y):
        MockImg.traj.append((x, y))
        return self

    def put_text(self, txt, x, y, font_size, *_, **__):
        MockImg.txt_traj.append(((x, y), txt))
        return self

    def show(self):
        pass

    def copy(self):
        return MockImg()

    @classmethod
    def reset(cls):
        cls.traj.clear()
        cls.txt_traj.clear()
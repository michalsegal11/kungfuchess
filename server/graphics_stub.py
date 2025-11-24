# server/graphics_stub.py
class Graphics:
    """No-op replacement – keeps server headless."""
    def __init__(self, *_, **__): pass
    def copy(self):                return self
    def reset(self, *_, **__):     pass
    def update(self, *_, **__):    pass
    def get_img(self):             return None

class ImgStub:
    def __init__(self, *_, **__):  self.img = None
    def read(self, *_, **__):      return self

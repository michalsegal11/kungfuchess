# graphics ↔ client.graphics
# importlib.import_module("client.graphics")
# sys.modules["graphics"]       = sys.modules["client.graphics"]
# sys.modules["core.graphics"]  = sys.modules["client.graphics"]  # כדי ש-import 'core.graphics.*' יעבוד

# ui ↔ client.ui  (ל־MoveLogUI/ScoreUI/Overlay/ui.draw/ui.show)
# importlib.import_module("client.ui")
# sys.modules["ui"]             = sys.modules["client.ui"]
# sys.modules["core.ui"]        = sys.modules["client.ui"]

# # input_handler ↔ client.input_handler
# importlib.import_module("client.input_handler")
# sys.modules["input_handler"]  = sys.modules["client.input_handler"]


__all__: list[str] = []
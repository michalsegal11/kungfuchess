# ui/window_icon.py
import os, sys
def set_window_icon(window_title: str, ico_path: str = "assets/logo.ico") -> None:
    if os.name != "nt":
        print("[icon] not Windows, skip")
        return

    try:
        import win32gui, win32con
    except ImportError as e:
        print("[icon] pywin32 missing →", e)
        return

    if not os.path.isfile(ico_path):
        print("[icon] ICO not found →", os.path.abspath(ico_path))
        return

    # Load icon
    icon_flags = win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
    hicon = win32gui.LoadImage(0, ico_path, win32con.IMAGE_ICON, 0, 0, icon_flags)
    if not hicon:
        print("[icon] LoadImage failed")
        return

    # Find window *after* it exists
    hwnd = win32gui.FindWindow(None, window_title)
    print("[icon] HWND:", hwnd)
    if not hwnd:
        print("[icon] window not found yet")
        return

    win32gui.SendMessage(hwnd, win32con.WM_SETICON, win32con.ICON_SMALL, hicon)
    win32gui.SendMessage(hwnd, win32con.WM_SETICON, win32con.ICON_BIG,   hicon)
    print("[icon] icon set ✔")

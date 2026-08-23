import sys
import os
import threading
import time
import socket
import ctypes
import webview
from app import create_app

# Single Instance Lock Port
SINGLE_INSTANCE_PORT = 49152

def get_active_app_hwnd():
    """Finds the active top-level window HWND for the current process ID (PID)."""
    if sys.platform != "win32":
        return 0

    user32 = ctypes.windll.user32
    my_pid = os.getpid()
    found_hwnd = [0]

    def enum_cb(hwnd, lparam):
        if user32.IsWindowVisible(hwnd):
            pid = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if pid.value == my_pid:
                class_buff = ctypes.create_unicode_buffer(256)
                user32.GetClassNameW(hwnd, class_buff, 256)
                cls_name = class_buff.value
                if "WindowsForms" in cls_name or "Chrome" in cls_name or "HwndWrapper" in cls_name:
                    found_hwnd[0] = hwnd
                    return False
        return True

    EnumProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_size_t, ctypes.c_size_t)
    user32.EnumWindows(EnumProc(enum_cb), 0)

    if not found_hwnd[0]:
        hwnd = user32.FindWindowW(None, "iPortfolio Tracker — Wealth Cockpit")
        if hwnd:
            found_hwnd[0] = hwnd

    return found_hwnd[0]

class DesktopAPI:
    def __init__(self):
        self._window = None
        self._is_max = True

    def set_window(self, window):
        self._window = window

    def minimize(self):
        if sys.platform == "win32":
            hwnd = get_active_app_hwnd()
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 6)  # SW_MINIMIZE
                return True
        if self._window:
            self._window.minimize()
        return True

    def toggle_maximize(self):
        if sys.platform == "win32":
            try:
                user32 = ctypes.windll.user32
                hwnd = get_active_app_hwnd()
                if hwnd:
                    is_zoomed = bool(user32.IsZoomed(hwnd))
                    if is_zoomed:
                        user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                        self._is_max = False
                    else:
                        user32.ShowWindow(hwnd, 3)  # SW_MAXIMIZE
                        self._is_max = True
                    return True
            except Exception:
                pass

        if self._window:
            if self._window.maximized:
                self._window.restore()
            else:
                self._window.maximize()
        return True

    def close(self):
        if self._window:
            self._window.destroy()
        return True

def acquire_single_instance_lock():
    """Enforces single-instance lock across the system using a dedicated loopback socket."""
    try:
        lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        lock_socket.bind(('127.0.0.1', SINGLE_INSTANCE_PORT))
        lock_socket.listen(1)
        return lock_socket
    except (socket.error, OverflowError):
        return None

def on_app_startup(window, api):
    """Callback executed by PyWebView as soon as GUI runtime starts to enforce maximization and icon."""
    # 1. Native PyWebView maximize
    try:
        window.maximize()
    except Exception:
        pass

    # 2. Win32 HWND maximization & Icon setting via PID lookup
    if sys.platform == "win32":
        try:
            user32 = ctypes.windll.user32
            hwnd = 0
            # Rapid poll every 20ms (up to 100 loops / 2 seconds) for PID window creation
            for _ in range(100):
                hwnd = get_active_app_hwnd()
                if hwnd and user32.IsWindowVisible(hwnd):
                    break
                time.sleep(0.02)

            if hwnd:
                # Snap to top-left (0,0) position immediately (SWP_NOSIZE | SWP_NOZORDER)
                SWP_NOSIZE = 0x0001
                SWP_NOZORDER = 0x0004
                user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, SWP_NOSIZE | SWP_NOZORDER)

                # Set Window Icon
                icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_icon.ico")
                if getattr(sys, 'frozen', False):
                    base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(sys.executable)))
                    candidate = os.path.join(base_dir, "app", "static", "app_icon.ico")
                    if os.path.exists(candidate):
                        icon_path = candidate
                    else:
                        icon_path = os.path.join(os.path.dirname(os.path.abspath(sys.executable)), "app_icon.ico")

                if os.path.exists(icon_path):
                    IMAGE_ICON = 1
                    LR_LOADFROMFILE = 0x00000010
                    hicon_big = user32.LoadImageW(0, icon_path, IMAGE_ICON, 48, 48, LR_LOADFROMFILE)
                    hicon_small = user32.LoadImageW(0, icon_path, IMAGE_ICON, 16, 16, LR_LOADFROMFILE)
                    WM_SETICON = 0x0080
                    ICON_SMALL = 0
                    ICON_BIG = 1
                    if hicon_big:
                        user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon_big)
                    if hicon_small:
                        user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon_small)

                # Force Win32 SW_MAXIMIZE (3)
                user32.ShowWindow(hwnd, 3)
                user32.UpdateWindow(hwnd)
                if api:
                    api._is_max = True
        except Exception:
            pass


def find_free_port():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('127.0.0.1', 0))
    port = sock.getsockname()[1]
    sock.close()
    return port

def run_flask(port):
    app = create_app()
    # Turn off debug reloader for clean native desktop runtime
    app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)

if __name__ == "__main__":
    # 1. Acquire Single Instance Lock
    lock_socket = acquire_single_instance_lock()
    if not lock_socket:
        # Another instance is already running
        print("iPortfolio Tracker is already running.")
        sys.exit(0)

    port = find_free_port()
    
    # 2. Start local server in background thread
    server_thread = threading.Thread(target=run_flask, args=(port,), daemon=True)
    server_thread.start()

    time.sleep(0.5)
    url = f"http://127.0.0.1:{port}/"
    
    desktop_api = DesktopAPI()

    # Open frameless native desktop window anchored at (0, 0) top-left in maximized mode
    window = webview.create_window(
        title="iPortfolio Tracker — Wealth Cockpit",
        url=url,
        x=0,
        y=0,
        width=1360,
        height=880,
        min_size=(1040, 680),
        resizable=True,
        maximized=True,
        frameless=True,  # REMOVE OS NATIVE TITLE BAR
        easy_drag=True,
        text_select=True,
        confirm_close=False,
        js_api=desktop_api
    )
    desktop_api.set_window(window)
    
    # Pass on_app_startup callback to webview.start to enforce window maximization right after GUI window is created
    webview.start(on_app_startup, (window, desktop_api), private_mode=False)


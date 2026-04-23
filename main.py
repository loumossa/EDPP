"""EDPP - Elite Dangerous PowerPlay Dashboard

Read-only dashboard for viewing PowerPlay data and related commander
information from Elite Dangerous journal files.
"""

import sys
import tkinter as tk

from config import APP_TITLE, WINDOW_DEFAULT_GEOMETRY, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT
from ui_app import EDPPApp


def main():
    # Windows DPI awareness for crisp rendering on high-DPI displays
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

    root = tk.Tk()
    root.title(APP_TITLE)
    root.geometry(WINDOW_DEFAULT_GEOMETRY)
    root.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)

    # Set window icon (optional - won't fail if missing)
    try:
        root.iconbitmap(default="")
    except Exception:
        pass

    app = EDPPApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

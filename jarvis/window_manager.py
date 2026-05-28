import logging
import sys

def focus_jarvis_window():
    """
    Finds the browser window with the Jarvis WebApp and brings it to the front.
    Cross-platform support: Windows (pygetwindow), others (logging fallback).
    """
    try:
        if sys.platform == "win32":
            import pygetwindow as gw
            windows = gw.getWindowsWithTitle('Jarvis')
            if windows:
                jarvis_win = windows[0]
                if jarvis_win.isMinimized:
                    jarvis_win.restore()
                jarvis_win.activate()
                logging.info("🚀 Jarvis WebApp window focused (Windows).")
            else:
                logging.warning("⚠️ Jarvis WebApp window not found.")
        elif sys.platform == "darwin":
            # macOS: Potrebbe essere implementato con AppleScript se necessario
            logging.info("ℹ️ Focus not implemented for macOS yet.")
        else:
            # Linux/Others
            logging.info(f"ℹ️ Focus not implemented for {sys.platform}.")
    except Exception as e:
        logging.error(f"❌ Error focusing Jarvis window: {e}")

if __name__ == "__main__":
    # Test focus
    focus_jarvis_window()

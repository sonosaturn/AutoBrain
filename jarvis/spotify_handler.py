import os
import time
import subprocess
import pyautogui
import pyperclip
import win32gui
from datetime import datetime

class SpotifyHandler:
    def __init__(self):
        self.spotify_path = "spotify:"
        self.is_fullscreen = False

    def _log(self, message):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [SpotifyHandler] 🎵 {message}")

    def _is_spotify_fullscreen(self):
        """Rileva se Spotify è massimizzato o in fullscreen."""
        self.is_fullscreen = False
        def callback(hwnd, extra):
            if win32gui.IsWindowVisible(hwnd):
                classname = win32gui.GetClassName(hwnd)
                title = win32gui.GetWindowText(hwnd)
                # Spotify usa Chrome_WidgetWin_0 o Chrome_WidgetWin_1
                if "Chrome_WidgetWin" in classname and title:
                    rect = win32gui.GetWindowRect(hwnd)
                    x, y, x1, y1 = rect
                    w, h = x1 - x, y1 - y
                    screen_w, screen_h = pyautogui.size()
                    
                    placement = win32gui.GetWindowPlacement(hwnd)
                    # placement[1] == 2 significa massimizzato
                    if placement[1] == 2 or (w >= screen_w - 50 and h >= screen_h - 50):
                        self.is_fullscreen = True

        win32gui.EnumWindows(callback, None)
        return self.is_fullscreen

    def focus_spotify(self):
        """Avvia o porta Spotify in primo piano."""
        os.system(f"start {self.spotify_path}")
        time.sleep(2)
        return self._is_spotify_fullscreen()

    def play(self, query=None):
        """Esegue la ricerca e avvia la riproduzione."""
        try:
            if not query:
                self._log("Avvio Spotify senza parametri.")
                os.system(f"start {self.spotify_path}")
                return "Spotify avviato."

            self._log(f"Procedura di riproduzione per: {query}")
            is_fs = self.focus_spotify()
            self._log(f"Modalità {'Fullscreen' if is_fs else 'Finestra'} rilevata.")

            # 1. Focus sulla barra di ricerca (Ctrl+L)
            pyautogui.hotkey('ctrl', 'l')
            time.sleep(0.5)

            # 2. Inserimento query
            pyperclip.copy(query)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.3)
            pyautogui.press('enter')
            time.sleep(2.0) # Attesa caricamento risultati

            # 3. Navigazione verso il primo risultato
            # Spesso serve premere Tab una o due volte a seconda del layout
            pyautogui.press('tab')
            time.sleep(0.3)
            
            if not is_fs:
                pyautogui.press('tab')
                time.sleep(0.3)

            # 4. Play
            pyautogui.press('enter')
            time.sleep(0.2)
            pyautogui.press('enter') # Doppio invio per sicurezza su alcuni layout

            return f"SILENT|Ho avviato la riproduzione di {query} su Spotify."

        except Exception as e:
            self._log(f"Errore: {e}")
            return f"Spiacente, si è verificato un errore con Spotify: {str(e)}"

# Singleton instance
spotify_manager = SpotifyHandler()

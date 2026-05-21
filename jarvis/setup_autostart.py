import os
import winshell
from win32com.client import Dispatch

def setup_autostart():
    """
    Crea uno script VBS per avviare Jarvis in background e lo aggiunge all'avvio di Windows.
    """
    project_dir = os.path.dirname(os.path.abspath(__file__))
    venv_python = os.path.join(project_dir, "venv", "Scripts", "pythonw.exe") # pythonw non apre la console
    main_script = os.path.join(project_dir, "main.py")
    
    # Percorso cartella Startup di Windows
    startup_path = winshell.startup()
    
    # 1. Crea il file VBS per l'avvio silenzioso
    vbs_content = f'Set WinScriptHost = CreateObject("WScript.Shell")\nWinScriptHost.Run Chr(34) & "{venv_python}" & Chr(34) & " " & Chr(34) & "{main_script}" & Chr(34), 0\nSet WinScriptHost = Nothing'
    vbs_path = os.path.join(project_dir, "run_jarvis.vbs")
    
    with open(vbs_path, "w") as f:
        f.write(vbs_content)
    
    # 2. Crea il collegamento nella cartella Startup
    shortcut_path = os.path.join(startup_path, "Jarvis.lnk")
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.Targetpath = "wscript.exe"
    shortcut.Arguments = f'"{vbs_path}"'
    shortcut.WorkingDirectory = project_dir
    shortcut.WindowStyle = 7 # Minimized
    shortcut.IconLocation = "shell32.dll, 24" # Icona generica sistema
    shortcut.save()
    
    print(f"✅ Jarvis configurato per l'avvio automatico!")
    print(f"📁 Shortcut creato in: {shortcut_path}")
    print(f"📄 Script VBS creato in: {vbs_path}")

if __name__ == "__main__":
    setup_autostart()

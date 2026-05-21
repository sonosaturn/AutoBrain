import os
import subprocess
import sys

def setup():
    print("🚀 Benvenuto nel setup del Secondo Cervello AI!")
    
    # 1. Creazione venv se non esiste
    if not os.path.exists("venv"):
        print("📦 Creazione ambiente virtuale...")
        subprocess.run([sys.executable, "-m", "venv", "venv"])
    
    # 2. Installazione requirements
    python_exe = os.path.join("venv", "Scripts", "python.exe") if os.name == "nt" else os.path.join("venv", "bin", "python")
    
    if os.path.exists("requirements.txt"):
        print("📥 Installazione dipendenze...")
        subprocess.run([python_exe, "-m", "pip", "install", "-r", "requirements.txt"])
    else:
        print("⚠️ requirements.txt non trovato. Salto installazione.")

    # 3. Controllo .env
    if not os.path.exists(".env"):
        print("🔑 File .env non trovato!")
        print("Ricordati di crearlo con le tue chiavi API (OPENROUTER_API_KEY, GEMINI_API_KEY, ecc.)")
    
    print("\n✨ Setup completato! Ora puoi avviare il sistema.")

if __name__ == "__main__":
    setup()

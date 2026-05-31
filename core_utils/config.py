import os
from dotenv import load_dotenv
from pathlib import Path

# Identify project root
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / ".env")

class Config:
    # API Keys
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    JARVIS_API_KEY = os.getenv("JARVIS_API_KEY", "jarvis_default_secret_2026") # Default for safety

    # Vault Paths
    VAULT_PATH = os.getenv("VAULT_PATH")
    CONVO_VAULT_PATH = os.getenv("CONVO_VAULT_PATH")

    # Models (Standard 2026 names)
    VOICE_MODEL = "gemini-3.1-flash-lite"
    BRAIN_MODEL = "gemini-3.1-flash-lite"

    # Folders
    CORE_DIR = ROOT_DIR / "autobrain_core"
    JARVIS_DIR = ROOT_DIR / "jarvis"

    @classmethod
    def validate(cls):
        """Checks if critical configurations are missing."""
        missing = []
        if not cls.GEMINI_API_KEY: missing.append("GEMINI_API_KEY")
        if not cls.VAULT_PATH: missing.append("VAULT_PATH")
        if missing:
            raise EnvironmentError(f"❌ Missing mandatory config: {', '.join(missing)}")

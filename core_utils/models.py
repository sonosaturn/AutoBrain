from google import genai
from .config import Config

# Shared Gemini Client
client = genai.Client(api_key=Config.GEMINI_API_KEY)

def get_model_config(system_instruction: str = None):
    """Returns a standard model configuration for generate_content."""
    from google.genai import types
    config = {
        "temperature": 0.1
    }
    if system_instruction:
        config["system_instruction"] = system_instruction
    return config

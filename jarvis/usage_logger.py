import os
import json
from datetime import datetime

def log_usage(model_name, prompt_tokens, completion_tokens, task_type="analysis"):
    """
    Registra l'utilizzo dei token in un file centrale per l'osservabilità.
    """
    log_file = "ai_usage_history.jsonl"
    
    # Prezzi stimati per 1M token (in USD) - Basati su Gemini 1.5/2.0/3.0 approx
    pricing = {
        "gemini-3.1-flash-lite": {"input": 0.10, "output": 0.40},
        "gemini-3-flash-preview": {"input": 0.10, "output": 0.40},
        "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
        "default": {"input": 0.10, "output": 0.40}
    }
    
    rates = pricing.get(model_name, pricing["default"])
    cost = (prompt_tokens / 1_000_000 * rates["input"]) + (completion_tokens / 1_000_000 * rates["output"])
    
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "model": model_name,
        "task": task_type,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
        "estimated_cost_usd": round(cost, 6)
    }
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

def get_today_stats():
    """Ritorna un riassunto dei costi di oggi."""
    log_file = "ai_usage_history.jsonl"
    if not os.path.exists(log_file):
        return "Nessun dato di utilizzo registrato oggi."
    
    today = datetime.now().strftime("%Y-%m-%d")
    total_cost = 0
    total_tokens = 0
    calls = 0
    
    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line)
            if data["timestamp"].startswith(today):
                total_cost += data["estimated_cost_usd"]
                total_tokens += data["total_tokens"]
                calls += 1
                
    return f"📊 Oggi (Python Scripts): {calls} chiamate, {total_tokens} token, ${round(total_cost, 4)}"

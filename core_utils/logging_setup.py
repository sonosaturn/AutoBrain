import logging
import sys
import os
import json
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime

class JsonFormatter(logging.Formatter):
    """Formatter che produce log in formato JSON per l'osservabilità strutturata."""
    def format(self, record):
        log_record = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "name": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "filename": record.filename,
            "lineno": record.lineno
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)

def setup_logging(name="jarvis", log_level=logging.INFO):
    """Configura un sistema di logging professionale con output Console, Testo e JSON."""
    # Cartella log in root del progetto
    log_dir = Path(__file__).parent.parent / "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Evita duplicazione se il logger è già configurato
    if logger.handlers:
        return logger

    # Formattatore standard per console e file di testo
    standard_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )
    
    # 1. Console Handler (Standard Output)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(standard_formatter)
    logger.addHandler(console_handler)
    
    # 2. File Handler (Testo Leggibile - Rotazione 10MB)
    text_file_path = log_dir / f"{name}.log"
    text_file_handler = RotatingFileHandler(
        text_file_path, 
        maxBytes=10*1024*1024, 
        backupCount=5,
        encoding='utf-8'
    )
    text_file_handler.setFormatter(standard_formatter)
    logger.addHandler(text_file_handler)
    
    # 3. JSON File Handler (Per analisi automatizzata / Vibe Coding prevention)
    json_file_path = log_dir / f"{name}_structured.jsonl"
    json_file_handler = RotatingFileHandler(
        json_file_path,
        maxBytes=10*1024*1024,
        backupCount=5,
        encoding='utf-8'
    )
    json_file_handler.setFormatter(JsonFormatter())
    logger.addHandler(json_file_handler)
    
    return logger

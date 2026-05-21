import os
import logging
import datetime
import time
from google import genai
from google.genai import types
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler

# Importazione locale per gli agenti
try:
    from jarvis_engine import agente_sviluppatore
except ImportError:
    # Se lanciato fuori dal folder jarvis
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from jarvis_engine import agente_sviluppatore

basedir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(basedir, ".env"))

# CONFIGURAZIONE MODELLI
BRAIN_MODEL = "gemini-3-flash-preview"

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CreativeLeaderAgent:
    def __init__(self):
        self.convo_vault = os.getenv("CONVO_VAULT_PATH")
        self.report_dir = os.path.join(os.path.dirname(basedir), "creative_reports")
        self.failed_report_dir = os.path.join(os.path.dirname(basedir), "failed_reports")
        
        os.makedirs(self.report_dir, exist_ok=True)
        os.makedirs(self.failed_report_dir, exist_ok=True)
        
        if self.convo_vault:
            os.makedirs(os.path.join(self.convo_vault, "Jarvis", "_Errori_Sviluppo"), exist_ok=True)

    def get_pending_errors(self):
        """Controlla se ci sono errori non risolti nel vault."""
        if not self.convo_vault: return []
        error_vault = os.path.join(self.convo_vault, "Jarvis", "_Errori_Sviluppo")
        return [f for f in os.listdir(error_vault) if f.endswith(".md")]

    def execute_innovation_cycle(self):
        """Generates new ideas (once a day)."""
        logger.info("🎨 Starting DAILY INNOVATION cycle...")
        self._run_task(task_mode="INNOVATION")

    def execute_repair_cycle(self):
        """Checks and repairs errors (every 2 hours)."""
        pending_errors = self.get_pending_errors()
        if not pending_errors:
            logger.info("✅ No pending errors. Skipping repair cycle.")
            return
            
        logger.info(f"🚨 {len(pending_errors)} errors detected. Starting AUTO-REPAIR cycle...")
        self._run_task(task_mode="REPAIR", error_file=pending_errors[0])

    def _run_task(self, task_mode, error_file=None):
        context_error = ""
        if error_file and self.convo_vault:
             with open(os.path.join(self.convo_vault, "Jarvis", "_Errori_Sviluppo", error_file), "r", encoding="utf-8") as f:
                context_error = f.read()

        # 1. Project Context Analysis
        project_context = self.analyze_project()
        
        # 2. Brainstorming or Debugging
        if task_mode == "REPAIR":
            prompt = f"You are the Senior Debugger. Resolve this error: {context_error}. Propose a fix."
        else:
            prompt = "You are the Creative Leader. Propose a single useful technical improvement."

        try:
            response = client.models.generate_content(
                model=BRAIN_MODEL,
                contents=f"{prompt}\n\nPROJECT CONTEXT:\n{project_context}"
            )
            proposta = response.text
            
            # 3. DELEGATION
            logger.info(f"👨‍💻 Delegating {task_mode} to the Developer Agent...")
            esito_sviluppo = agente_sviluppatore(f"{task_mode} Task: {proposta}")
            
            successo = "✅" in esito_sviluppo or "successo" in esito_sviluppo.lower() or "success" in esito_sviluppo.lower()
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            
            report_finale = f"# 🤖 {task_mode} Report - {timestamp}\n\n## 💡 Proposal\n{proposta}\n---\n## 🛠️ Result\n{esito_sviluppo}"

            if successo:
                if task_mode == "REPAIR" and self.convo_vault:
                    old_path = os.path.join(self.convo_vault, "Jarvis", "_Errori_Sviluppo", error_file)
                    resolved_dir = os.path.join(self.convo_vault, "Jarvis", "_Errori_Risolti")
                    os.makedirs(resolved_dir, exist_ok=True)
                    os.rename(old_path, os.path.join(resolved_dir, error_file))
                self._salva_report(timestamp, report_finale, "completed", self.report_dir)
            else:
                if self.convo_vault and task_mode != "REPAIR":
                    error_vault_path = os.path.join(self.convo_vault, "Jarvis", "_Errori_Sviluppo", f"ERROR_{timestamp}.md")
                    with open(error_vault_path, "w", encoding="utf-8") as f:
                        f.write(f"---\ntype: development_error\nstatus: pending\n---\n{report_finale}")
                self._salva_report(timestamp, report_finale, "failed", self.failed_report_dir)

        except Exception as e:
            logger.error(f"❌ Errore critico nel task {task_mode}: {e}")

def start_creative_engine():
    leader = CreativeLeaderAgent()
    scheduler = BackgroundScheduler()

    # INNOVATION CYCLE: Ogni 24 ore
    scheduler.add_job(leader.execute_innovation_cycle, 'interval', days=1, next_run_time=datetime.datetime.now())
    
    # REPAIR CYCLE: Ogni 2 ore
    scheduler.add_job(leader.execute_repair_cycle, 'interval', hours=2)
    
    scheduler.start()
    logger.info("🚀 Motore Creativo e di Riparazione Ibrido avviato.")

    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()

    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()

if __name__ == "__main__":
    start_creative_engine()

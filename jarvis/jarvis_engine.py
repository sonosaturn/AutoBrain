import os
import json
import logging
import sys

# Modular Import Logic
try:
    from core_utils import Config, models
except ImportError:
    # Fallback for transition phase
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from core_utils import Config, models

# MANDATORY MODEL NAMES (From Hub)
VOICE_MODEL = Config.VOICE_MODEL
BRAIN_MODEL = Config.BRAIN_MODEL

client = models.client

# ---------------------------------------------------------------------------
# "HANDS" - DEVELOPMENT TOOLS (For Agents)
# ---------------------------------------------------------------------------

BASE_DIR = Config.JARVIS_DIR

def _resolve_path(file_path: str):
    """Resolves and validates paths to avoid system errors or access outside the project folder."""
    # Removes any quotes the LLM might pass by mistake
    file_path = file_path.strip("'\"")
    # Builds the absolute path
    abs_path = os.path.abspath(os.path.join(BASE_DIR, file_path))
    # Security measure: prevents exiting the project folder
    if not abs_path.startswith(BASE_DIR):
        raise PermissionError(f"Access denied: Cannot operate outside of {BASE_DIR}")
    return abs_path

import py_compile
import shutil
import subprocess

def gitnexus_query(query_text: str):
    """Queries the project architecture using GitNexus."""
    try:
        # We use --skip-git since the project structure might not be a standard git repo in all environments
        result = subprocess.run(["gitnexus", "query", query_text, "--skip-git"], capture_output=True, text=True, check=True)
        return result.stdout
    except Exception as e:
        return f"❌ GitNexus Query Error: {e}"

def gitnexus_impact(symbol_name: str):
    """Analyzes the impact (blast radius) of modifying a specific symbol."""
    try:
        result = subprocess.run(["gitnexus", "impact", "--target", symbol_name, "--direction", "upstream", "--skip-git"], capture_output=True, text=True, check=True)
        return result.stdout
    except Exception as e:
        return f"❌ GitNexus Impact Error: {e}"

def scrivi_codice(file_path: str, contenuto: str):
    """Allows the agent to write or overwrite a file in the project with safety checks."""
    try:
        abs_path = _resolve_path(file_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        
        # Security/Validation for Python files
        if abs_path.endswith(".py"):
            temp_path = abs_path + ".tmp"
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(contenuto)
            
            try:
                # Syntax check
                py_compile.compile(temp_path, doraise=True)
                # If valid, replace original
                if os.path.exists(abs_path):
                    backup_path = abs_path + ".bak"
                    shutil.copy2(abs_path, backup_path)
                
                shutil.move(temp_path, abs_path)
                return f"✅ File {file_path} validated and written successfully."
            except py_compile.PyCompileError as e:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                return f"❌ Syntax Error in generated code: {e.msg}. File not updated."
            except Exception as e:
                return f"❌ Validation error: {e}"
        else:
            # Direct write for other files
            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(contenuto)
            return f"✅ File {file_path} written successfully."
            
    except Exception as e:
        return f"❌ File writing error: {e}"

def leggi_codice(file_path: str):
    """Allows the agent to read a file's content."""
    try:
        abs_path = _resolve_path(file_path)
        if os.path.isdir(abs_path):
             return f"❌ Error: {file_path} is a directory, not a file."
        with open(abs_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"❌ File reading error: {e}"

# Available tools for the model
tools = [scrivi_codice, leggi_codice, gitnexus_query, gitnexus_impact]

# ---------------------------------------------------------------------------
# AGENTIC CORE (NATIVE)
# ---------------------------------------------------------------------------

import time
import random

def delega_alla_cli(obiettivo: str, errore_precedente: str = ""):
    """Writes a task file in the dispatch queue for the Gemini CLI."""
    try:
        convo_vault = os.getenv("CONVO_VAULT_PATH")
        if not convo_vault:
            return "❌ Error: CONVO_VAULT_PATH not configured."
            
        dispatch_dir = os.path.join(convo_vault, "Jarvis", "_Dispatch_Queue")
        os.makedirs(dispatch_dir, exist_ok=True)
        
        timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
        file_path = os.path.join(dispatch_dir, f"TASK_DELEGATION_{timestamp}.md")
        
        contenuto = f"""---
type: cli_delegation
status: pending
created: {timestamp}
---
# 🛰️ Delegation Request from Jarvis

## 🎯 Goal
{obiettivo}

## ❌ Error encountered by Jarvis
{errore_precedente if errore_precedente else "Task too complex for voice resources."}

---
**Instructions for the CLI:** Execute the requested bug fixing or development. Once finished, update this file by changing the status to 'completed' and write a brief summary of the solution.
"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(contenuto)
            
        return f"🛰️ Task delegated to Gemini CLI. File ready at {file_path}. Inform Lorenzo."
    except Exception as e:
        return f"❌ Error during delegation: {e}"

def agente_sviluppatore(obiettivo: str):
    """Handles a development objective with retry, fallback, and CLI delegation on persistent failure."""
    models_to_try = [BRAIN_MODEL, VOICE_MODEL]
    ultimo_errore = ""
    
    system_instruction = (
        "You are the Jarvis Senior Developer. Your goal is to analyze and write Python code. "
        "MANDATORY: Before modifying any function or class, you MUST run 'gitnexus_impact' to understand the blast radius. "
        "Use 'gitnexus_query' to explore the architecture and 'leggi_codice' to read files. "
        "Use 'scrivi_codice' to implement fixes. Proceed step-by-step. Be concise and professional."
    )

    for current_model in models_to_try:
        print(f"\n👨‍💻 [DEVELOPER AGENT] Attempting with model: {current_model}")
        contents = [types.Content(role="user", parts=[types.Part.from_text(text=obiettivo)])]
        
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=[types.Tool(function_declarations=[
                types.FunctionDeclaration(
                    name="scrivi_codice",
                    description="Writes or overwrites a file.",
                    parameters={
                        "type": "OBJECT",
                        "properties": {
                            "file_path": {"type": "STRING"},
                            "contenuto": {"type": "STRING"}
                        },
                        "required": ["file_path", "contenuto"]
                    }
                ),
                types.FunctionDeclaration(
                    name="leggi_codice",
                    description="Reads a file.",
                    parameters={
                        "type": "OBJECT",
                        "properties": {
                            "file_path": {"type": "STRING"}
                        },
                        "required": ["file_path"]
                    }
                ),
                types.FunctionDeclaration(
                    name="gitnexus_query",
                    description="Queries the project architecture.",
                    parameters={
                        "type": "OBJECT",
                        "properties": {
                            "query_text": {"type": "STRING"}
                        },
                        "required": ["query_text"]
                    }
                ),
                types.FunctionDeclaration(
                    name="gitnexus_impact",
                    description="Analyzes the impact of modifying a symbol.",
                    parameters={
                        "type": "OBJECT",
                        "properties": {
                            "symbol_name": {"type": "STRING"}
                        },
                        "required": ["symbol_name"]
                    }
                )
            ])]
        )

        try:
            # Reasoning loop (max 5 iterations)
            for i in range(5):
                # Internal retry for temporary errors (e.g., 503)
                retry_count = 0
                max_retries = 3
                success = False
                response = None
                
                while retry_count < max_retries:
                    try:
                        response = client.models.generate_content(
                            model=current_model,
                            contents=contents,
                            config=config
                        )
                        success = True
                        break 
                    except Exception as e:
                        ultimo_errore = str(e)
                        if ("503" in ultimo_errore or "429" in ultimo_errore) and retry_count < max_retries - 1:
                            retry_count += 1
                            wait_time = (2 ** retry_count) + random.random()
                            print(f"⚠️ Model overloaded. Next attempt in {wait_time:.1f}s...")
                            time.sleep(wait_time)
                        else:
                            break 

                if not success:
                    raise Exception(f"Fatal error with model {current_model}: {ultimo_errore}")

                # Add response to context
                contents.append(response.candidates[0].content)
                
                tool_results = []
                for part in response.candidates[0].content.parts:
                    if part.function_call:
                        fn_name = part.function_call.name
                        args = part.function_call.args
                        print(f"🛠️ [ACTION] Executing {fn_name}...")
                        
                        if fn_name == "scrivi_codice":
                            result_text = scrivi_codice(**args)
                        elif fn_name == "leggi_codice":
                            result_text = leggi_codice(**args)
                        
                        print(f"📡 [RESULT] {result_text[:50]}...")
                        tool_results.append(types.Part.from_function_response(
                            name=fn_name,
                            response={"result": result_text}
                        ))
                
                if not tool_results:
                    return response.text

                contents.append(types.Content(role="tool", parts=tool_results))

        except Exception as e:
            ultimo_errore = str(e)
            print(f"🚨 Error with {current_model}: {ultimo_errore}")
            if current_model == BRAIN_MODEL:
                print("🔄 Attempting fallback to Lite model...")
                continue
            
    # If we reach here, both models failed. Delegate to CLI.
    print("🛰️ [SYSTEM] Total failure of local agents. Activating CLI DELEGATION protocol...")
    return delega_alla_cli(obiettivo, ultimo_errore)

if __name__ == "__main__":
    # Test logic
    # print(agente_sviluppatore("Create a test_jarvis.py file with a greeting"))
    pass

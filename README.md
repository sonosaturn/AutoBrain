# 🧠 Second Brain AI & Jarvis

Welcome to the **Second Brain AI** ecosystem, an advanced productivity and development environment powered by Artificial Intelligence. This project combines a sophisticated RAG (Retrieval-Augmented Generation) system for knowledge management with **Jarvis**, an autonomous voice assistant and developer capable of self-improvement.

## 🌟 Key Features

- **🧠 Second Brain (RAG):** Processes PDF, DOCX, and text files by extracting semantic chunks. Uses ChromaDB for lightning-fast vector searches directly within an Obsidian Vault.
- **🎙️ Jarvis (Voice Interaction):** A hands-free voice interface based on Vosk (offline Speech-to-Text) and Gemini (Text-to-Speech and logic).
- **🦾 Agentic Engine (Self-Healing):** Jarvis doesn't just talk; it acts. It can write and modify its own source code. If it encounters an error, it logs it in the Vault and triggers a self-healing cycle every 2 hours.
- **🎨 Creative Leader:** Once a day, the "Creative Leader" agent analyzes the codebase, proposes "out of the box" features, and delegates their implementation to the Developer Agent.
- **🌌 Holographic GUI:** A custom Arc Reactor interface built in Python (Tkinter) providing real-time visual feedback on Jarvis's cognitive states (Listening, Thinking, Speaking).
- **🛰️ GitNexus Integration:** The entire project is mapped via GitNexus, allowing agents to understand the deep structure of the code before making any modifications.

## 🚀 Project Architecture

The system uses a **Hub & Spoke** architecture with resource delegation:
1.  **Voice Front-End:** Powered by the high-speed `gemini-3.1-flash-lite` model.
2.  **Cognitive Back-End:** Powered by the deep-reasoning `gemini-3-flash-preview` model for code generation and complex logic.
3.  **Dispatch Queue:** Overly complex tasks are offloaded to an Obsidian queue to be resolved manually or via the Gemini CLI with higher resource limits.

## 🛠️ System Requirements

- Python 3.10+
- Obsidian (for Knowledge Graph visualization)
- Google Gemini API Key
- GitNexus CLI (Optional, but recommended)

## 💡 Project Philosophy: AI for Everyone (Free Tier First)

AutoBrain was born out of a desire to dive into the world of **Agentic AI and RAG** without the barrier of high entry costs. 

While many enterprise solutions rely on expensive paid models, this project is built with a **"Zero-Budget"** mindset:
- **Models:** We exclusively use **Google Gemini (Free Tier)** and **Vosk (Offline STT)** to ensure that students and hobbyists can run a full-scale AI assistant without spending a cent.
- **Tools:** Every part of the stack, from **Obsidian** to **GitNexus**, is chosen for its power and accessibility.
- **Why?** To prove that architectural intelligence (how you design the system) is more important than the cost of the API tokens.

## 📥 Detailed Installation & Setup

To get AutoBrain running on your machine, follow these steps carefully:

### 1. Prerequisites
- **Python 3.10 or higher** installed and added to your PATH.
- **Git** installed.
- **Obsidian** (optional, but highly recommended to visualize your Second Brain).

### 2. Clone and Prepare
```bash
git clone https://github.com/sonosaturn/AutoBrain.git
cd AutoBrain
```

### 3. Automated Environment Setup
We provide a script that handles the heavy lifting (creating the Virtual Environment and installing over 100+ dependencies listed in `requirements.txt`):
```bash
python setup_laptop.py
```
*Wait for the script to finish. It will ensure all libraries like `google-genai`, `chromadb`, and `vosk` are ready.*

### 4. Configuration (.env)
You **must** create a file named `.env` in the root folder. Use the following template:
```env
GEMINI_API_KEY=your_free_google_ai_studio_key
VAULT_PATH=C:/Path/To/Your/University_Vault
CONVO_VAULT_PATH=C:/Path/To/Your/Conversation_Vault
```
> **Note:** Get your free API key at [Google AI Studio](https://aistudio.google.com/).

### 5. First Launch
1.  **Initialize the Brain:** Run `start_brain.bat`. It will scan your documents and build the initial Knowledge Graph.
2.  **Activate Jarvis:** Run `run_jarvis.vbs`. The Arc Reactor GUI will appear at the center of your screen when you call him.

## 🎮 Usage

- **Start the Brain (Data Indexing):**
  Run `start_brain.vbs` or execute `python brain.py` to start the file watcher that indexes new PDFs and Markdown files in real-time.
- **Start Jarvis (Voice Assistant):**
  Run `run_jarvis.vbs` to start the voice assistant and the GUI in the background.
- **Auto-Improvement:**
  Add `run_creative_leader.vbs` to your Windows Startup folder to enable the background self-evolution cycle.

## ⚙️ Customization & Configuration

You can easily adapt AutoBrain to your needs by modifying a few key parameters:

### 🌍 Language and Speech
- **Voice Recognition (STT):** To change the language, update the `vosk_url` in `jarvis/main.py`. The system currently defaults to Italian.
- **Agent Personality:** Modify the `SYSTEM_PROMPT` in `jarvis/intent_parser.py` and `jarvis/main.py` to change how Jarvis speaks or what language he uses for responses.

### 🤖 AI Models
We use specific models for different tasks to balance speed and reasoning power:
- **Fast Responses/Voice:** `gemini-3.1-flash-lite`
- **Deep Reasoning/Coding:** `gemini-3-flash-preview`
To swap models, update the global variables in `jarvis/jarvis_engine.py` and `jarvis/main.py`.

### ⏱️ Autonomous Cycles
- **Self-Healing (Repair):** Defaults to every **2 hours**. Change this in `jarvis/creative_leader.py`.
- **Innovation (Creative):** Defaults to every **24 hours**. Change this in `jarvis/creative_leader.py`.

## 🛡️ Security and Portability
The `.gitignore` is pre-configured to exclude heavy databases (ChromaDB) and sensitive API keys (`.env`). The project is ready for multi-machine synchronization (e.g., via Syncthing or Git) without conflicts.

## 📜 License
MIT License. Feel free to fork, modify, and build your own personal AI assistant!

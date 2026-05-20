ASTRO V2.0 - Autonomous AI System Administrator
ASTRO is an advanced, terminal-centric AI agent designed for autonomous system administration and VoIP-based communication. Version 2.0 introduces a modular architecture, a sophisticated Textual dashboard, and a powerful reasoning engine powered by LangGraph and ChromaDB.

🚀 Key Features
Advanced Reasoning Hierarchy: Built on LangGraph, allowing the agent to think, plan, and execute tool calls (like terminal commands) autonomously.
Interactive UI (TUI): A premium Textual-based terminal dashboard featuring a dynamic "Matrix" background, a pulsing "Orb" life-sign, and real-time activity logs.
VoIP & Asterisk Integration: Full voice-to-voice capabilities via the Asterisk Gateway Interface (AGI).
Secure Sudo Handling: Root privileges are managed using Fernet AES-128 encryption, allowing the agent to perform administrative tasks without repeated password prompts.
Persistent Memory: Uses ChromaDB for vector-based long-term memory and SQLite for call logs and mission tracking.
🎙️ Asterisk & Voice Integration
ASTRO features a robust voice engine that turns a standard phone call into an interactive session with an AI agent.

Voice Flow Architecture
Incoming/Outgoing Call: The Asterisk PBX system triggers the AGI script located at agi/bridge.py.
Speech-to-Text (STT):
The caller's voice is recorded using Asterisk's RECORD FILE command.
Vosk, an offline speech recognition toolkit, processes the audio locally to ensure low latency and privacy.
Core Intelligence:
The transcribed text is sent to the LLM (Google Gemini 2.0 Flash) with full conversation history and available tools.
If the user asks for a system task (e.g., "Check server disk space"), the agent executes it via the run_terminal tool.
Text-to-Speech (TTS):
After generating a response, ASTRO uses Microsoft Edge TTS to create high-quality, natural-sounding audio in Uzbek (or English).
The audio is processed through FFmpeg to match telephony standards (8000Hz, Mono, 16-bit PCM).
Asterisk plays the audio back to the caller using the STREAM FILE command.
📁 Project Structure
agi/bridge.py: The AGI script for Asterisk integration.
astro_agent/core/: Backend logic, configuration, and sudo management.
astro_agent/ui/: The Textual-based user interface components.
astro_agent/memory/: ChromaDB and SQLite memory implementations.
astro_agent/tools/: Suite of autonomous tools (terminal, weather, etc.).
astro.py: Main entry point for the TUI application.
install.sh: Automated environment setup and dependency installer.
🛠️ Installation & Setup
Clone the project and navigate to the directory.
Run the installation script:
bash install.sh
This will set up the Virtual Environment and install required dependencies (Textual, LangGraph, ChromaDB, Edge-TTS, Vosk).
Configure Asterisk: Map your dialplan to call the AGI script:
exten => 100,1,AGI(/home/user/astro-agent/agi/bridge.py)
💻 Usage
To launch the ASTRO Autonomous Dashboard:

python3 astro.py run
To monitor Asterisk voice logs: The dashboard will dynamically display incoming call transcripts and tool activity.

🛡️ Security
ASTRO takes security seriously. Administrative access is protected with AES encryption. The agent can be configured for "Zero-Permission" mode, where it can autonomously troubleshoot and fix server issues while logging every action for human review.

Created by Husan. Managed by ASTRO V2.0.


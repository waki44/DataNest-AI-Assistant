## ⚡ Overview

**DataNest** combines a cyberpunk HUD aesthetic with high-performance desktop control. Powered by the **Gemini API** and built on top of **CustomTkinter**, it runs as an executive desktop operator capable of multi-turn conversational reasoning, hardware monitoring, and natural voice interaction.

---

## 🚀 Key Modules

| Module | Features & Capabilities |
| :--- | :--- |
| **🤖 AI Assistant** | ChatGPT-style dynamic scrollable chat, real-time reasoning, and automated web task execution. |
| **📊 Telemetry Hub** | Live gauge monitors for CPU load, RAM usage, and primary disk availability. |
| **📈 Analytics** | Dynamic line chart rendering real-time CPU spikes alongside logical core thread loads. |
| **⚡ Process Supervisor** | Task manager tracking top resource-consuming processes by Memory (MB) and PID. |
| **🎙 Audio Engine** | Threaded voice recognition and speech response synthesis. |
| **⚙ Utility Deck** | In-app unit storage converters and real-time exchange rate estimators. |

---

## 🛠 Tech Stack

- **Interface:** CustomTkinter, Tkinter Canvas (Custom charts & glowing AI Orb)
- **Intelligence:** Google GenAI SDK (`gemini-flash-lite`)
- **System Telemetry:** `psutil`
- **Audio & Voice:** `speech_recognition`, `pygame`
- **Asset Processing:** `Pillow` (PIL)

---

## 📦 Installation & Setup

### 1. Clone Repository
\`\`\`bash
git clone https://github.com/waki44/DataNest-AI-Assistant.git
cd DataNest-AI-Assistant
\`\`\`

### 2. Environment Setup
\`\`\`bash
python -m venv venv
venv\\Scripts\\activate
pip install -r requirements.txt
\`\`\`

### 3. Configure Credentials
Duplicate the sample configuration and insert your API key:
\`\`\`bash
copy config.example.json config.json
\`\`\`
Edit \`config.json\`:
\`\`\`json
{
  \"GEMINI_API_KEY\": \"your_actual_gemini_api_key_here\"
}
\`\`\`

### 4. Launch Operator
\`\`\`bash
python gui_assistant.py
\`\`\`

---

## 🛡 Security Note

Sensitive credentials and build artifacts are strictly excluded via \`.gitignore\`:
- \`config.json\` is never committed to remote tracking.
- Distributable binaries (\`dist/\`, \`build/\`) remain local.

---

<div align=\"center\">
Designed & Developed by <b>Syed Waqar</b>

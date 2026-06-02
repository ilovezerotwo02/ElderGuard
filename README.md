# 🛡️ ElderGuard

> AI-Powered Elderly Fraud Protection System — Multi-modal fraud detection with smart rule engine and LLM integration.

---

## 📁 Project Structure

```
elderguard/
├── source/                  # All source code (development here)
│   ├── app/                 # Python main package (api/core/database/llm/services)
│   ├── static/              # Frontend pages (index.html, config.html)
│   ├── scripts/             # Utility scripts
│   ├── launcher.py          # GUI Launcher (tkinter)
│   ├── run.py               # CLI entry point
│   ├── build_exe.py         # EXE build script
│   └── requirements.txt     # Dependencies
├── release/                 # Packaged executables (double-click to run)
└── workspace/               # Developer workspace (docs, test files, build logs)
```

---

## 🚀 Quick Start

### Run from Source (Development)

#### Step 1: Install Dependencies

```bash
cd source
pip install -r requirements.txt
```

#### Step 2: Start the Service

```bash
cd source
python run.py
```

#### Step 3: Access the System

Once the service starts, open your browser:

| Page | URL | Description |
|------|-----|-------------|
| **Detection** | http://localhost:8000 | Main UI for fraud detection |
| **Config** | http://localhost:8000/config | LLM API configuration |
| **API Docs** | http://localhost:8000/docs | Developer API documentation |

### Run as EXE (End Users)

Go to `release/` and double-click `ElderGuard.exe`. Click "Start System" in the launcher window.

---

## 🔧 LLM Configuration (Optional)

**Rules-only mode is enabled by default — no API key needed.**

### Option 1: Web Config Page (Recommended)

1. Start the service and visit: http://localhost:8000/config
2. Select mode (Rules / Ollama / OpenAI)
3. Fill in the info and save

### Option 2: GUI Launcher Config

1. Run the launcher (double-click `ElderGuard.exe` or `python launcher.py`)
2. Go to "Model Config" card and select a mode
3. Fill in the details and click "Save Config"
4. Click "Start System"

### Option 3: Edit `.env` Manually

File located at `source/.env`:

```env
# Rules-only mode (free, default)
USE_RULES_ONLY=True

# Ollama local model
USE_OLLAMA=True
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL_NAME=deepseek-r1:8b

# OpenAI API
USE_OLLAMA=False
OPENAI_API_KEY=sk-your-key
```

---

## 💡 Features

✅ **Out of the box** - Rules-only mode, no AI model needed
✅ **GUI Launcher** - tkinter-based, one-click start/stop
✅ **Multiple Modes** - Rules / Ollama / OpenAI
✅ **Web Configuration** - Visual LLM API setup
✅ **Large Font UI** - Designed for elderly users
✅ **Multi-modal Detection** - URL, SMS, call, voice
✅ **Real-time Alerts** - Tiered risk warnings
✅ **Knowledge Base** - RAG-powered fraud prevention guides

---

## 🏗️ Build EXE

```bash
cd source
pip install pyinstaller
python build_exe.py
```

---

## 🆘 FAQ

### Q: How do I start the service?
A: Double-click `start.bat` or run `cd source && python run.py`

### Q: The web page won't open?
A: Make sure the service is running (don't close the terminal window), check http://localhost:8000

### Q: Can I use it without an API key?
A: Yes! Rules-only mode works completely offline with no API key needed.

---

## 📞 Emergency Contacts

If you encounter a real fraud attempt:
- Police: **110**
- Anti-Fraud Hotline: **96110**

---

## 📄 License

MIT License

# ElderGuard

An anti-fraud tool for elderly users. Detects scam URLs, SMS, and phone calls using a rule engine. Optionally connects to Ollama or OpenAI for deeper analysis.

## Project Layout

```
elderguard/
├── source/              # Where you develop
│   ├── app/             # Python backend
│   ├── static/          # Frontend HTML pages
│   ├── scripts/         # Helper scripts
│   ├── launcher.py      # Desktop GUI (tkinter)
│   ├── run.py           # Start from terminal
│   └── build_exe.py     # Package into .exe
├── release/             # Built exe goes here
└── workspace/           # Your scratch files
```

## Quick Start

```bash
cd source
pip install -r requirements.txt
python run.py
```

Then open http://localhost:8000 in your browser.

Or just double-click `release/ElderGuard.exe` if you downloaded the release.

## How to Configure LLM (Optional)

By default it runs in rules-only mode — no API key, works offline.

**Via web:** Start the service, visit http://localhost:8000/config, pick a mode, save.

**Via launcher:** Open the GUI, go to "Model Config", select Ollama or API mode.

**Via .env:** Edit `source/.env` manually.

```
USE_RULES_ONLY=True          # default, no AI needed
USE_OLLAMA=True              # for local models
OLLAMA_MODEL_NAME=deepseek-r1:8b
```

## Build EXE Yourself

```bash
cd source
pip install pyinstaller
python build_exe.py
```

## Notes

- Rules-only mode works completely offline, no internet needed.
- For Ollama mode, install Ollama first and pull a model.
- The UI uses large fonts — designed for older users.
- If something looks suss, hit the emergency numbers: 110 (police) or 96110 (anti-fraud hotline).

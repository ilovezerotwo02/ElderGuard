# -*- mode: python ; coding: utf-8 -*-
# ElderGuard - PyInstaller Build Configuration
# Builds GUI Launcher (window mode, no console)

import sys
import os
from pathlib import Path

# Project root - use current working directory
project_root = Path.cwd()

# Add project path to sys.path
sys.path.insert(0, str(project_root))

# Collected data files
datas = []

# Static files (bundled into exe resources, extracted to _MEIPASS at runtime)
static_dir = project_root / "static"
if static_dir.exists():
    datas.append((str(static_dir), "static"))

# Config file example
env_example = project_root / ".env.example"
if env_example.exists():
    datas.append((str(env_example), "."))

# Hidden imports (dynamically imported modules)
hiddenimports = [
    # FastAPI related
    'fastapi',
    'uvicorn',
    'uvicorn.lifespan',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.websockets',
    'uvicorn.lifespan.on',
    'uvicorn.lifespan.off',

    # Pydantic related
    'pydantic',
    'pydantic.generics',
    'pydantic.types',
    'pydantic_schema',

    # SQLAlchemy related
    'sqlalchemy',
    'sqlalchemy.ext',
    'sqlalchemy.ext.asyncio',
    'sqlalchemy.orm',
    'aiosqlite',

    # Database models
    'app.database.models',
    'app.database.session',
    'app.database.init_data',

    # Service modules
    'app.services.url_detector',
    'app.services.risk_assessor',
    'app.services.voice_detector',
    'app.services.content_analyzer',

    # LLM modules
    'app.llm.service',
    'app.llm.rag',

    # API modules
    'app.api.detection',
    'app.api.knowledge',
    'app.api.schemas',

    # Core config
    'app.core.config',

    # Entry points (dynamically imported by GUI launcher)
    'app.main',
    'run',
    'run_server',

    # Other dependencies
    'loguru',
    'passlib',
    'bcrypt',
    'python_multipart',
    'pydantic_settings',

    # AI client libraries (must be explicitly included for packaging)
    'ollama',
    'openai',
]

# Exclude unnecessary modules (reduce size)
excludes = [
    'matplotlib',
    'pygame',
    'PyQt5',
    'PySide2',
    'scipy',
    'sympy',
    'notebook',
    'jupyter',
    'ipython',
    'django',
    'flask',
    'boto3',
    'awscli',
    # Exclude large AI modules to reduce packaging issues and size
    'torch',
    'transformers',
    'sentence_transformers',
    'chromadb',
    'faiss',
    'librosa',
    'soundfile',
    'pydub',
]

# Build options
a = Analysis(
    ['launcher.py'],                        # <- Entry point changed to GUI launcher
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,                       # tkinter is NOT in excludes — automatically included
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Set exe output
pyz = PYZ(a.pure)

# Create window-mode exe (no console/terminal window)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ElderGuard',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,                           # <- Window mode, hides the black terminal
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

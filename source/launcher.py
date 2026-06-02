"""
ElderGuard - GUI Launcher
Modern tkinter-based GUI with Ollama detection, model management, and service control
"""
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import subprocess
import sys
import os
import webbrowser
import time
import json
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime
from typing import Optional

# ── Color Scheme ──
C = {
    "bg": "#f0f4f8",
    "card": "#ffffff",
    "header_bg": "#1a237e",
    "header_fg": "#ffffff",
    "primary": "#1565c0",
    "success": "#2e7d32",
    "warning": "#e65100",
    "error": "#c62828",
    "text_primary": "#212121",
    "text_secondary": "#616161",
    "border": "#cfd8dc",
    "disabled": "#bdbdbd",
    "log_bg": "#263238",
    "log_fg": "#eceff1",
}

# ── Path Utilities ──

def get_resource_path(relative_path: str) -> Path:
    if getattr(sys, "frozen", False):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).parent
    return base / relative_path


def get_work_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent


def log_time() -> str:
    return datetime.now().strftime("%H:%M:%S")


# ── Main Launcher ──

class AntiFraudLauncher:
    """ElderGuard GUI Launcher"""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("ElderGuard - Launcher")
        self.root.geometry("720x780")
        self.root.resizable(False, False)
        self.root.configure(bg=C["bg"])

        try:
            ico = get_resource_path("app/icon.ico")
            if ico.exists():
                self.root.iconbitmap(str(ico))
        except Exception:
            pass

        self.center_window()

        # ── State Variables ──
        self.server_thread: Optional[threading.Thread] = None
        self.server_running = False
        self.ollama_installed: Optional[bool] = None
        self.ollama_version = ""
        self.ollama_running = False
        self.ollama_models: list[str] = []
        self.expected_model = self._detect_expected_model()
        self.model_ok = False

        # ── Config State ──
        self.config_mode = tk.StringVar(value="ollama")   # "ollama" or "api"
        self.cfg_ollama_url = tk.StringVar(value="http://localhost:11434")
        self.cfg_ollama_model = tk.StringVar(value=self.expected_model)
        self.cfg_api_key = tk.StringVar()
        self.cfg_api_url = tk.StringVar(value="https://api.openai.com/v1")
        self.cfg_api_model = tk.StringVar(value="gpt-3.5-turbo")
        self._load_config_from_env()  # Load current config from .env

        # ── Build UI ──
        self._build_ui()

        # ── Auto Detection ──
        self.root.after(800, self._run_initial_checks)

    # ── Window ──

    def center_window(self):
        self.root.update_idletasks()
        w, h = 720, 780
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    # ── UI Construction ──

    def _build_ui(self):
        style = ttk.Style()
        style.theme_use("clam")

        # ── Main Container ──
        self.main_frame = tk.Frame(self.root, bg=C["bg"])
        self.main_frame.pack(fill="both", expand=True)

        # Header
        self._build_header()

        # Content
        content = tk.Frame(self.main_frame, bg=C["bg"], padx=20, pady=16)
        content.pack(fill="both", expand=True)

        self._build_status_card(content)
        tk.Frame(content, bg=C["bg"], height=12).pack(fill="x")
        self._build_config_card(content)  # Model config
        tk.Frame(content, bg=C["bg"], height=12).pack(fill="x")
        self._build_action_card(content)
        tk.Frame(content, bg=C["bg"], height=12).pack(fill="x")
        self._build_log_card(content)

        # Status bar
        self._build_statusbar()

        # UI ready flag (used by _toggle_config_mode)
        self._ui_ready = True

    def _build_header(self):
        header = tk.Frame(self.main_frame, bg=C["header_bg"], height=90)
        header.pack(fill="x")
        header.pack_propagate(False)

        inner = tk.Frame(header, bg=C["header_bg"], padx=28, pady=12)
        inner.pack(fill="both", expand=True)

        title_row = tk.Frame(inner, bg=C["header_bg"])
        title_row.pack(anchor="w")

        tk.Label(title_row, text="🛡", font=("Segoe UI Emoji", 24),
                 bg=C["header_bg"], fg=C["header_fg"]).pack(side="left", padx=(0, 10))

        tk.Label(title_row, text="ElderGuard",
                 font=("Microsoft YaHei", 20, "bold"),
                 bg=C["header_bg"], fg=C["header_fg"]).pack(side="left")

        tk.Label(inner, text="AI-Powered Multi-Modal Fraud Detection System · GUI Launcher",
                 font=("Microsoft YaHei", 10),
                 bg=C["header_bg"], fg="#b3c6e7").pack(anchor="w", padx=(50, 0), pady=(2, 0))

    def _build_status_card(self, parent):
        card = tk.Frame(parent, bg=C["card"], highlightbackground=C["border"],
                        highlightthickness=1, padx=20, pady=16)
        card.pack(fill="x")

        tk.Label(card, text="System Status", font=("Microsoft YaHei", 13, "bold"),
                 bg=C["card"], fg=C["text_primary"]).pack(anchor="w")
        tk.Frame(card, bg=C["border"], height=1).pack(fill="x", pady=(8, 12))

        grid = tk.Frame(card, bg=C["card"])
        grid.pack(fill="x")

        items = [
            ("ollama_status",    "Ollama Status",     "⏳ Checking..."),
            ("model_status",     "Installed Models",  "⏳ Checking..."),
            ("expected_model_l", "Expected Model",    self.expected_model),
            ("port_status",      "System Port",       "8000"),
            ("server_status",    "Service Status",    "⚫ Not Running"),
        ]

        for i, (attr, label, default) in enumerate(items):
            row, col = i // 2, i % 2
            f = tk.Frame(grid, bg=C["card"])
            f.grid(row=row, column=col, sticky="ew", pady=4)
            grid.columnconfigure(col, weight=1)

            tk.Label(f, text=f"{label}:", font=("Microsoft YaHei", 11),
                     bg=C["card"], fg=C["text_secondary"],
                     width=14, anchor="w").pack(side="left")

            val = tk.Label(f, text=default, font=("Microsoft YaHei", 11, "bold"),
                           bg=C["card"], fg=C["text_secondary"], anchor="w")
            val.pack(side="left", fill="x", expand=True, padx=(0, 20 if col == 0 else 0))
            setattr(self, f"_{attr}", val)

    def _make_btn(self, parent, text, color, cmd, state="normal", big=False):
        kw = dict(
            text=text,
            font=("Microsoft YaHei", 12, "bold") if big else ("Microsoft YaHei", 11),
            bg=color, fg="white",
            activebackground=color, activeforeground="white",
            relief="flat", bd=0,
            padx=20 if big else 14, pady=8 if big else 6,
            cursor="hand2",
            state=state,
            disabledforeground="#cccccc",
            command=cmd,
        )
        return tk.Button(parent, **kw)

    # ── Config Management ──────────────────────────────────────────

    def _load_config_from_env(self):
        """Load current config from .env file"""
        env_path = get_work_dir() / ".env"
        if not env_path.exists():
            return
        try:
            lines = env_path.read_text("utf-8", errors="ignore").splitlines()
            for line in lines:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k, v = k.strip(), v.strip().strip('"').strip("'")
                if k == "OLLAMA_MODEL_NAME" and v:
                    self.cfg_ollama_model.set(v)
                elif k == "OLLAMA_BASE_URL" and v:
                    self.cfg_ollama_url.set(v)
                elif k == "OPENAI_API_KEY" and v and v != "your-openai-api-key":
                    self.cfg_api_key.set(v)
                elif k == "OPENAI_API_BASE" and v:
                    self.cfg_api_url.set(v)
                elif k == "LLM_MODEL_NAME" and v:
                    self.cfg_api_model.set(v)
                elif k == "USE_RULES_ONLY" and v == "True":
                    self.config_mode.set("rules")
                elif k == "USE_OLLAMA":
                    if v == "True":
                        self.config_mode.set("ollama")
                    elif self.config_mode.get() != "rules":  # Only switch to api if not in rules mode
                        self.config_mode.set("api")
        except Exception:
            pass

    def _build_config_card(self, parent):
        """Model Configuration Card"""
        card = tk.Frame(parent, bg=C["card"], highlightbackground=C["border"],
                        highlightthickness=1, padx=20, pady=16)
        card.pack(fill="x")

        tk.Label(card, text="Model Configuration", font=("Microsoft YaHei", 13, "bold"),
                 bg=C["card"], fg=C["text_primary"]).pack(anchor="w")
        tk.Frame(card, bg=C["border"], height=1).pack(fill="x", pady=(8, 8))

        # ── Mode Selection ──
        mode_frame = tk.Frame(card, bg=C["card"])
        mode_frame.pack(fill="x", pady=(0, 8))

        tk.Radiobutton(mode_frame, text="Ollama Local Model", variable=self.config_mode,
                       value="ollama", bg=C["card"], fg=C["text_primary"],
                       font=("Microsoft YaHei", 11),
                       selectcolor=C["card"], command=self._toggle_config_mode
                       ).pack(side="left", padx=(0, 20))
        tk.Radiobutton(mode_frame, text="Remote API", variable=self.config_mode,
                       value="api", bg=C["card"], fg=C["text_primary"],
                       font=("Microsoft YaHei", 11),
                       selectcolor=C["card"], command=self._toggle_config_mode
                       ).pack(side="left", padx=(0, 20))
        tk.Radiobutton(mode_frame, text="Local Rules Mode", variable=self.config_mode,
                       value="rules", bg=C["card"], fg=C["text_primary"],
                       font=("Microsoft YaHei", 11),
                       selectcolor=C["card"], command=self._toggle_config_mode
                       ).pack(side="left")

        # ── Ollama Config Section ──
        self.ollama_config_frame = tk.Frame(card, bg=C["card"])
        self.ollama_config_frame.pack(fill="x", pady=(0, 6))

        row1 = tk.Frame(self.ollama_config_frame, bg=C["card"])
        row1.pack(fill="x", pady=2)
        tk.Label(row1, text="Ollama URL:", bg=C["card"], fg=C["text_secondary"],
                 font=("Microsoft YaHei", 10), width=11, anchor="w").pack(side="left")
        tk.Entry(row1, textvariable=self.cfg_ollama_url,
                 font=("Consolas", 10), bg="#f5f5f5", relief="solid", bd=1).pack(side="left", fill="x", expand=True, padx=(0, 8))

        row2 = tk.Frame(self.ollama_config_frame, bg=C["card"])
        row2.pack(fill="x", pady=2)
        tk.Label(row2, text="Select Model:", bg=C["card"], fg=C["text_secondary"],
                 font=("Microsoft YaHei", 10), width=11, anchor="w").pack(side="left")
        self.model_combo = ttk.Combobox(row2, textvariable=self.cfg_ollama_model,
                                        font=("Microsoft YaHei", 10),
                                        state="readonly", width=30)
        self.model_combo.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.b_refresh_models = self._make_btn(row2, "🔄", C["primary"], self._refresh_models)
        self.b_refresh_models.pack(side="left")

        # ── API Config Section ──
        self.api_config_frame = tk.Frame(card, bg=C["card"])
        self.api_config_frame.pack(fill="x", pady=(0, 6))

        for label, var, placeholder in [
            ("API Key:",  self.cfg_api_key,  "sk-..."),
            ("API URL:", self.cfg_api_url,  "https://api.openai.com/v1"),
            ("Model Name:", self.cfg_api_model, "gpt-3.5-turbo"),
        ]:
            r = tk.Frame(self.api_config_frame, bg=C["card"])
            r.pack(fill="x", pady=2)
            tk.Label(r, text=label, bg=C["card"], fg=C["text_secondary"],
                     font=("Microsoft YaHei", 10), width=11, anchor="w").pack(side="left")
            tk.Entry(r, textvariable=var, font=("Consolas", 10),
                     bg="#f5f5f5", relief="solid", bd=1,
                     show="*" if "key" in label.lower() else "").pack(side="left", fill="x", expand=True)

        # ── Save Button ──
        btn_row = tk.Frame(card, bg=C["card"])
        btn_row.pack(fill="x", pady=(4, 0))
        self.b_save_config = self._make_btn(btn_row, "💾 Save Config", C["primary"], self._save_config)
        self.b_save_config.pack(side="left")
        self.config_save_status = tk.Label(btn_row, text="", bg=C["card"], fg=C["success"],
                                            font=("Microsoft YaHei", 10))
        self.config_save_status.pack(side="left", padx=(12, 0))

        # ── Rules Mode Info ──
        self.rules_info_frame = tk.Frame(card, bg=C["card"])
        self.rules_info_frame.pack(fill="x", pady=(4, 0))
        tk.Label(self.rules_info_frame,
                 text="Pure local rules mode — no AI model required. Fraud detection based on keyword and regex matching. Works offline.",
                 font=("Microsoft YaHei", 10), bg="#fff3e0", fg=C["warning"],
                 wraplength=550, justify="left", padx=8, pady=6, relief="solid", bd=1).pack(fill="x")

        # Initial display state
        self._toggle_config_mode()

    def _toggle_config_mode(self):
        """Toggle config section visibility based on mode"""
        mode = self.config_mode.get()
        # Hide all sections first
        self.ollama_config_frame.pack_forget()
        self.api_config_frame.pack_forget()
        self.rules_info_frame.pack_forget()
        # Show the matching section
        if mode == "ollama":
            self.ollama_config_frame.pack(fill="x", pady=(0, 6))
        elif mode == "api":
            self.api_config_frame.pack(fill="x", pady=(0, 6))
        else:  # rules
            self.rules_info_frame.pack(fill="x", pady=(0, 6))
        # Update start button state (only after UI is fully built)
        if getattr(self, "_ui_ready", False):
            self._refresh_ui()

    def _refresh_models(self):
        """Refresh installed Ollama model list"""
        self.log("Refreshing model list...")
        self.b_refresh_models.configure(state="disabled", text="⏳")

        def task():
            try:
                models = self._check_models()
                if not models:
                    self.root.after(0, self.log, "⚠ No installed models detected", "warn")
                else:
                    self.ollama_models = models
                    self.root.after(0, self.model_combo.configure, values=models)
                    # Update model_ok: check if current selection is in the list
                    current_selected = self.cfg_ollama_model.get()
                    if current_selected in models:
                        self.model_ok = True
                    elif models:
                        # Current selection not in list, auto-select first available model
                        self.model_ok = False
                        first = models[0]
                        self.root.after(0, lambda nm=first: self.cfg_ollama_model.set(nm))
                    self.root.after(0, self.log, f"✓ Found {len(models)} model(s)", "ok")
                    self.root.after(0, self._refresh_ui)
            except Exception as e:
                import traceback
                self.root.after(0, self.log, f"❌ Refresh failed: {e}", "error")
                self.root.after(0, self.log, traceback.format_exc()[-200:], "error")
            self.root.after(0, self.b_refresh_models.configure, state="normal", text="🔄")

        threading.Thread(target=task, daemon=True).start()

    def _save_config(self):
        """Save config to .env file"""
        try:
            env_path = get_work_dir() / ".env"
            mode = self.config_mode.get()

            lines = []
            # Preserve existing non-conflicting config lines
            if env_path.exists():
                old_lines = env_path.read_text("utf-8", errors="ignore").splitlines()
                # Filter out lines that will be overwritten
                skip_keys = {"USE_RULES_ONLY", "USE_OLLAMA", "OLLAMA_BASE_URL",
                             "OLLAMA_MODEL_NAME", "OPENAI_API_KEY", "OPENAI_API_BASE",
                             "LLM_MODEL_NAME", "USE_LOCAL_MODEL"}
                for line in old_lines:
                    if not line.strip() or line.strip().startswith("#"):
                        lines.append(line)
                    elif "=" in line:
                        k = line.split("=", 1)[0].strip()
                        if k not in skip_keys:
                            lines.append(line)

            if mode == "ollama":
                lines.append("")
                lines.append("# Ollama config (saved by launcher)")
                lines.append("USE_RULES_ONLY=False")
                lines.append("USE_OLLAMA=True")
                lines.append(f"OLLAMA_BASE_URL={self.cfg_ollama_url.get()}")
                lines.append(f"OLLAMA_MODEL_NAME={self.cfg_ollama_model.get()}")
            elif mode == "api":
                lines.append("")
                lines.append("# API config (saved by launcher)")
                lines.append("USE_RULES_ONLY=False")
                lines.append("USE_OLLAMA=False")
                lines.append(f"OPENAI_API_KEY={self.cfg_api_key.get()}")
                lines.append(f"OPENAI_API_BASE={self.cfg_api_url.get()}")
                lines.append(f"LLM_MODEL_NAME={self.cfg_api_model.get()}")
            else:  # rules
                lines.append("")
                lines.append("# Local rules mode (saved by launcher)")
                lines.append("USE_RULES_ONLY=True")
                lines.append("USE_OLLAMA=False")
                lines.append("USE_LOCAL_MODEL=False")
                lines.append("# Model config below is not needed, kept for reference when switching modes")
                lines.append(f"OLLAMA_MODEL_NAME={self.cfg_ollama_model.get()}")

            # Deduplicate empty lines
            clean = []
            prev_empty = False
            for line in lines:
                empty = not line.strip()
                if empty and prev_empty:
                    continue
                clean.append(line)
                prev_empty = empty

            env_path.write_text("\n".join(clean) + "\n", encoding="utf-8")

            self.expected_model = self.cfg_ollama_model.get()
            self.config_save_status.configure(text="✓ Config saved! Restart service to apply")
            self.log("✓ Config saved to .env file", "ok")
            mode_name = {"ollama": "Ollama Local Model", "api": "Remote API", "rules": "Local Rules Mode"}
            self.log(f"   Mode: {mode_name.get(mode, mode)}", "info")
            if mode == "ollama":
                self.log(f"   Model: {self.cfg_ollama_model.get()}", "info")
            elif mode == "api":
                self.log(f"   Model: {self.cfg_api_model.get()}", "info")
            else:
                self.log("   No AI model needed — pure keyword rule detection", "info")
            self.log("   If the service is running, please stop and restart it", "warn")

            # Update status display
            self._refresh_ui()

        except Exception as e:
            self.config_save_status.configure(text=f"✗ Save failed: {e}", fg=C["error"])
            self.log(f"❌ Failed to save config: {e}", "error")

    def _build_action_card(self, parent):
        card = tk.Frame(parent, bg=C["card"], highlightbackground=C["border"],
                        highlightthickness=1, padx=20, pady=16)
        card.pack(fill="x")

        tk.Label(card, text="Actions", font=("Microsoft YaHei", 13, "bold"),
                 bg=C["card"], fg=C["text_primary"]).pack(anchor="w")
        tk.Frame(card, bg=C["border"], height=1).pack(fill="x", pady=(8, 12))

        # Row 1: Tool Buttons
        row1 = tk.Frame(card, bg=C["card"])
        row1.pack(fill="x", pady=(0, 8))

        self.b_install_ollama = self._make_btn(row1, "📥 Install Ollama", C["warning"], self._install_ollama)
        self.b_install_ollama.pack(side="left", padx=(0, 10))

        self.b_download_model = self._make_btn(row1, "📦 Download Model", C["primary"], self._download_model, "disabled")
        self.b_download_model.pack(side="left", padx=(0, 10))

        self.b_recheck = self._make_btn(row1, "🔄 Re-check", C["text_secondary"], self._run_initial_checks)
        self.b_recheck.pack(side="left")

        # Row 2: Service Control
        row2 = tk.Frame(card, bg=C["card"])
        row2.pack(fill="x", pady=(4, 0))

        self.b_start = self._make_btn(row2, "🚀 Launch System", C["success"], self._start_server, "disabled", big=True)
        self.b_start.pack(side="left", padx=(0, 10))

        self.b_browser = self._make_btn(row2, "🌐 Open Browser", C["primary"], self._open_browser, "disabled", big=True)
        self.b_browser.pack(side="left", padx=(0, 10))

        self.b_stop = self._make_btn(row2, "⏹ Stop Service", C["error"], self._stop_server, "disabled", big=True)
        self.b_stop.pack(side="left")

    def _build_log_card(self, parent):
        card = tk.Frame(parent, bg=C["card"], highlightbackground=C["border"],
                        highlightthickness=1, padx=20, pady=16)
        card.pack(fill="both", expand=True)

        tk.Label(card, text="Runtime Logs", font=("Microsoft YaHei", 13, "bold"),
                 bg=C["card"], fg=C["text_primary"]).pack(anchor="w")
        tk.Frame(card, bg=C["border"], height=1).pack(fill="x", pady=(8, 8))

        lf = tk.Frame(card, bg=C["log_bg"])
        lf.pack(fill="both", expand=True)

        self.log_text = tk.Text(lf, height=10,
                                bg=C["log_bg"], fg=C["log_fg"],
                                font=("Consolas", 10),
                                relief="flat", bd=0, padx=10, pady=8,
                                wrap="word", state="disabled")
        self.log_text.pack(fill="both", expand=True)

        sb = tk.Scrollbar(self.log_text, command=self.log_text.yview)
        sb.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=sb.set)

    def _build_statusbar(self):
        bar = tk.Frame(self.main_frame, bg=C["border"], height=28)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)

        self.status_text = tk.Label(bar, text="Ready - Checking system environment...",
                                    font=("Microsoft YaHei", 10),
                                    bg=C["border"], fg=C["text_secondary"],
                                    anchor="w", padx=16)
        self.status_text.pack(fill="both", expand=True)

    # ── Logging ──

    def log(self, msg: str, level: str = "info"):
        col = {"info": C["log_fg"], "ok": "#66bb6a", "warn": "#ffa726", "error": "#ef5350"}
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"[{log_time()}] ", "t")
        self.log_text.insert("end", f"{msg}\n", f"l{level}")
        self.log_text.tag_config("t", foreground="#78909c")
        self.log_text.tag_config(f"l{level}", foreground=col.get(level, C["log_fg"]))
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
        self.status_text.configure(text=msg[:80])
        self.root.update_idletasks()

    # ── Ollama Detection ──

    def _detect_expected_model(self) -> str:
        env_path = get_work_dir() / ".env"
        if env_path.exists():
            try:
                for line in env_path.read_text("utf-8", errors="ignore").splitlines():
                    line = line.strip()
                    if line.startswith("OLLAMA_MODEL_NAME="):
                        return line.split("=", 1)[1].strip().strip('"').strip("'")
            except Exception:
                pass
        return "deepseek-r1:8b"

    def _check_ollama_installed(self) -> bool:
        """Check if Ollama is installed (try 3 methods in order)"""
        # Method 1: ollama command
        try:
            r = subprocess.run(["ollama", "--version"],
                               capture_output=True, text=True, timeout=10,
                               creationflags=subprocess.CREATE_NO_WINDOW)
            if r.returncode == 0:
                ver = (r.stdout.strip() or r.stderr.strip()).strip()
                # Compatible with various version output formats: "ollama version is 0.21.0" or "0.21.0"
                for prefix in ["ollama version is ", "version "]:
                    if ver.startswith(prefix):
                        ver = ver[len(prefix):]
                self.ollama_version = ver.strip()
                return True
        except Exception:
            pass
        # Method 2: HTTP API
        try:
            req = urllib.request.Request("http://localhost:11434/api/version")
            with urllib.request.urlopen(req, timeout=3) as resp:
                d = json.loads(resp.read().decode())
                self.ollama_version = d.get("version", "?")
                return True
        except Exception:
            pass
        # Method 3: ollama Python SDK
        try:
            import ollama as _ollama_sdk
            v = _ollama_sdk.list()
            if v:
                self.ollama_version = "SDK"
                return True
        except Exception:
            pass
        return False

    def _check_ollama_running(self) -> bool:
        """Check if Ollama service is running"""
        try:
            req = urllib.request.Request("http://localhost:11434/api/tags")
            with urllib.request.urlopen(req, timeout=3) as resp:
                return resp.status == 200
        except Exception:
            pass
        try:
            import ollama as _ollama_sdk
            _ollama_sdk.list()
            return True
        except Exception:
            pass
        return False

    def _check_models(self) -> list[str]:
        """Check installed Ollama models (try 3 methods in order)"""
        models = []

        # Method 1: ollama Python SDK (most reliable)
        try:
            import ollama as _ollama_sdk
            resp = _ollama_sdk.list()
            # Compatible with old and new SDK: new returns ListResponse object, old returns dict
            if isinstance(resp, dict):
                raw_models = resp.get("models", [])
            else:
                raw_models = getattr(resp, "models", []) if hasattr(resp, "models") else []
            for item in raw_models:
                if isinstance(item, dict):
                    name = item.get("name") or item.get("model") or ""
                else:
                    # New SDK: Model object, attributes are model/name
                    name = getattr(item, "model", "") or getattr(item, "name", "") or str(item)
                if name and name not in models:
                    models.append(name)
            if models:
                return models
        except Exception:
            pass

        # Method 2: ollama list command
        try:
            r = subprocess.run(["ollama", "list"],
                               capture_output=True, text=True, timeout=15,
                               creationflags=subprocess.CREATE_NO_WINDOW)
            if r.returncode == 0:
                lines = r.stdout.strip().split("\n")
                for line in lines[1:]:  # Skip header
                    line = line.strip()
                    if line:
                        name = line.split()[0]
                        if name and name not in models:
                            models.append(name)
        except Exception as e:
            self.log(f"  ollama list command failed: {e}", "warn")

        # Method 3: HTTP API
        if not models:
            try:
                req = urllib.request.Request("http://localhost:11434/api/tags")
                with urllib.request.urlopen(req, timeout=5) as resp:
                    for m in json.loads(resp.read().decode()).get("models", []):
                        name = m.get("name") or m.get("model") or ""
                        if name and name not in models:
                            models.append(name)
            except Exception:
                pass

        return models

    def _set_status(self, attr: str, text: str, color: str):
        lbl = getattr(self, attr, None)
        if lbl:
            lbl.configure(text=text, fg=color)

    def _refresh_ui(self):
        # Ollama Status
        if self.ollama_installed is True:
            if self.ollama_running:
                self._set_status("_ollama_status", f"✅ Running ({self.ollama_version})", C["success"])
            else:
                self._set_status("_ollama_status", f"⚠️ Installed, Not Running ({self.ollama_version})", C["warning"])
        elif self.ollama_installed is False:
            self._set_status("_ollama_status", "❌ Not Installed", C["error"])
        else:
            self._set_status("_ollama_status", "⏳ Checking...", C["text_secondary"])

        # Model Status
        if self.ollama_installed and self.ollama_models:
            if self.model_ok:
                self._set_status("_model_status", f"✅ {', '.join(self.ollama_models[:3])}", C["success"])
            else:
                # Show all available models for user selection
                model_list = ', '.join(self.ollama_models[:4])
                self._set_status("_model_status", f"⚠ Available: {model_list}", C["warning"])
        elif self.ollama_installed:
            self._set_status("_model_status", "❌ No Models Installed", C["error"])
        else:
            self._set_status("_model_status", "⏳ Waiting...", C["text_secondary"])

        # Service Status
        if self.server_running:
            self._set_status("_server_status", "🟢 Running", C["success"])
        else:
            self._set_status("_server_status", "⚫ Not Running", C["text_secondary"])

        # Buttons
        self.b_install_ollama.configure(
            state="normal" if self.ollama_installed is False else "disabled",
            bg=C["warning"] if self.ollama_installed is False else C["disabled"])
        self.b_download_model.configure(
            state="normal" if (self.ollama_installed and not self.model_ok) else "disabled",
            bg=C["primary"] if (self.ollama_installed and not self.model_ok) else C["disabled"])
        mode = self.config_mode.get()
        can_start = not self.server_running
        if mode == "rules":
            pass  # can_start remains True
        elif mode == "api":
            api_key = self.cfg_api_key.get().strip()
            can_start = can_start and api_key != "" and api_key != "your-openai-api-key"
        elif mode == "ollama":
            selected = self.cfg_ollama_model.get()
            model_available = selected in (self.ollama_models or [])
            can_start = can_start and self.ollama_installed and model_available
        self.b_start.configure(
            state="normal" if can_start else "disabled",
            bg=C["success"] if can_start else C["disabled"])
        self.b_browser.configure(
            state="normal" if self.server_running else "disabled",
            bg=C["primary"] if self.server_running else C["disabled"])
        self.b_stop.configure(
            state="normal" if self.server_running else "disabled",
            bg=C["error"] if self.server_running else C["disabled"])

    # ── Initial Checks ──

    def _run_initial_checks(self):
        self.log("Checking system environment...")
        self._refresh_ui()

        def task():
            self.log("→ Checking Ollama installation...")
            installed = self._check_ollama_installed()

            if installed:
                self.ollama_installed = True
                self.log(f"✓ Ollama is installed (version: {self.ollama_version})", "ok")

                self.ollama_running = self._check_ollama_running()
                if self.ollama_running:
                    self.log("✓ Ollama service is running", "ok")
                    self.log("→ Checking installed models...")
                    self.ollama_models = self._check_models()
                    if self.ollama_models:
                        self.log(f"✓ Detected {len(self.ollama_models)} model(s): {', '.join(self.ollama_models)}", "ok")
                        # Update dropdown model list
                        self.root.after(0, lambda m=self.ollama_models: self.model_combo.configure(values=m))
                        if self.expected_model in self.ollama_models:
                            self.model_ok = True
                            self.log(f"✓ Target model {self.expected_model} is ready", "ok")
                            self.log("💡 You can now click \"Launch System\"!", "info")
                        else:
                            self.model_ok = False
                            self.log(f"⚠ Target model {self.expected_model} not found", "warn")
                            self.log(f"   Installed models: {', '.join(self.ollama_models)}", "info")
                            self.log("   🔧 You can manually select an available model in \"Model Configuration\"", "info")
                            # Auto-select first available model
                            first_model = self.ollama_models[0]
                            self.root.after(0, lambda nm=first_model: self.cfg_ollama_model.set(nm))
                    else:
                        self.log("⚠ No models installed", "warn")
                else:
                    self.log("⚠ Ollama is installed but the service is not running", "warn")
                    self.log("   Please start the Ollama desktop application first", "info")
            else:
                self.ollama_installed = False
                self.ollama_running = False
                self.log("❌ Ollama not detected", "error")
                self.log("   Click \"Install Ollama\" button to download", "error")

            # If in rules mode, remind user they can start directly
            if self.config_mode.get() == "rules":
                self.log("💡 Currently in Local Rules Mode — no model required to start", "info")
                self.log("   Click \"Launch System\" to begin", "info")

            self.root.after(0, self._refresh_ui)

        threading.Thread(target=task, daemon=True).start()

    # ── Action Buttons ──

    def _install_ollama(self):
        if messagebox.askyesno("Install Ollama",
                               "Open the Ollama official website download page?\n\n"
                               "Website: https://ollama.com/download\n\n"
                               "After installation, click \"Re-check\" to confirm."):
            webbrowser.open("https://ollama.com/download")
            self.log("Opened Ollama download page", "info")

    def _download_model(self):
        model = self.expected_model
        if not messagebox.askyesno("Download Model",
                                   f"About to pull model: {model}\n"
                                   f"Size approximately 4-8 GB, time depends on network speed\n\n"
                                   "Are you sure you want to continue?"):
            return

        self.log(f"Starting to pull model: {model} ...", "info")
        self.b_download_model.configure(state="disabled", text="⏳ Downloading...", bg=C["disabled"])

        def task():
            try:
                p = subprocess.Popen(["ollama", "pull", model],
                                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                     text=True, bufsize=1,
                                     creationflags=subprocess.CREATE_NO_WINDOW)
                for line in iter(p.stdout.readline, ""):
                    line = line.strip()
                    if line:
                        self.root.after(0, self.log, f"  {line}")

                p.wait()
                if p.returncode == 0:
                    self.root.after(0, self.log, f"✓ Model {model} downloaded successfully!", "ok")
                    self.ollama_models = self._check_models()
                    self.model_ok = model in self.ollama_models
                else:
                    self.root.after(0, self.log, f"❌ Model download failed", "error")
            except Exception as e:
                self.root.after(0, self.log, f"❌ Download error: {e}", "error")

            self.root.after(0, self.b_download_model.configure,
                            text="📦 Download Model", bg=C["primary"])
            self.root.after(0, self._refresh_ui)

        threading.Thread(target=task, daemon=True).start()

    # ── Service Control ──

    def _start_server(self):
        self.log("Starting Web service...")
        self.b_start.configure(state="disabled", text="⏳ Starting...", bg=C["disabled"])

        # Run server in background thread
        def run_server_thread():
            """Thread function to run the server — all exceptions are logged"""
            try:
                # Switch to working directory
                import os
                wd = get_work_dir()
                os.chdir(str(wd))

                # Suppress uvicorn log output
                import logging
                logging.getLogger("uvicorn").setLevel(logging.WARNING)
                logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

                # Import app (must be done after setting working directory)
                from app.main import app

                # Use uvicorn.Server so it can be stopped cleanly via should_exit
                import uvicorn
                uvicorn_config = uvicorn.Config(
                    app,
                    host="0.0.0.0",
                    port=8000,
                    reload=False,
                    log_level="warning",
                    access_log=False,
                    log_config=None,
                )
                server = uvicorn.Server(uvicorn_config)

                # Add shutdown endpoint (uses server.should_exit to actually stop uvicorn)
                @app.post("/api/shutdown")
                async def shutdown_endpoint():
                    server.should_exit = True
                    return {"status": "shutting_down"}

                @app.get("/api/shutdown")
                async def shutdown_get():
                    server.should_exit = True
                    return {"status": "shutting_down"}

                # Initialize database
                try:
                    from app.database.session import engine, Base
                    import asyncio
                    async def init_db():
                        async with engine.begin() as conn:
                            await conn.run_sync(Base.metadata.create_all)
                        # Initialize sample data (skip if already exists)
                        from app.database.init_data import init_sample_data
                        await init_sample_data()
                    asyncio.run(init_db())
                    self.root.after(0, self.log, "✓ Database initialization complete", "ok")
                except Exception as e:
                    self.root.after(0, self.log, f"⚠ Database init: {e}", "warn")

                self.root.after(0, self.log, "✓ Web service started!", "ok")
                self.root.after(0, self.log, "   Access URL: http://localhost:8000", "info")
                self.server_running = True
                self.root.after(0, self._on_server_ready)

                # Run server (synchronous blocking, server.run creates its own event loop)
                server.run()

                # uvicorn has stopped (server.should_exit was set to True)
                self.server_running = False
                self.root.after(0, self.log, "✓ Service stopped safely", "ok")
                self.root.after(0, self._refresh_ui)

            except Exception as e:
                import traceback
                err_msg = f"{e}\n{traceback.format_exc()}"
                self.root.after(0, self.log, f"❌ Server error: {err_msg[:200]}", "error")
                self.server_running = False
                self.root.after(0, self.b_start.configure,
                                text="🚀 Launch System", bg=C["success"])

        self.server_thread = threading.Thread(target=run_server_thread, daemon=True)
        self.server_thread.start()

    def _on_server_ready(self):
        self._refresh_ui()
        # Auto-open browser
        self.root.after(500, self._open_browser)

    def _stop_server(self):
        self.log("Stopping service...")
        try:
            # Send shutdown request
            import urllib.request
            try:
                req = urllib.request.Request("http://localhost:8000/api/shutdown",
                                             method="POST",
                                             data=b"{}",
                                             headers={"Content-Type": "application/json"})
                urllib.request.urlopen(req, timeout=3)
            except Exception:
                pass

            # Fallback shutdown method
            try:
                import requests
                requests.post("http://localhost:8000/api/shutdown", timeout=2)
            except Exception:
                pass

            self.server_running = False
            self.log("✓ Service stopped", "ok")
        except Exception as e:
            self.log(f"⚠ Stop exception: {e}", "warn")
            self.server_running = False

        self._refresh_ui()
        self.b_start.configure(text="🚀 Launch System")

    def _open_browser(self):
        webbrowser.open("http://localhost:8000")
        self.log("🌐 Browser opened", "info")


# ── Entry Point ──

def main():
    root = tk.Tk()
    AntiFraudLauncher(root)
    root.mainloop()


if __name__ == "__main__":
    main()

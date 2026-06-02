#!/usr/bin/env python3
"""
ElderGuard - EXE Build Script (GUI Launcher Edition)
Uses PyInstaller to package the project as a Windows executable
Outputs a window-mode exe (no black terminal window) with GUI launcher
"""
import os
import sys
import subprocess
import shutil
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent


def check_pyinstaller():
    """Check if PyInstaller is installed"""
    try:
        import PyInstaller
        print("[OK] PyInstaller is installed")
        return True
    except ImportError:
        print("[!] PyInstaller is not installed")
        choice = input("Auto-install PyInstaller? (y/n): ").strip().lower()
        if choice == 'y':
            print("Installing PyInstaller...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
            print("[OK] PyInstaller installed successfully")
            return True
        else:
            print("[ERROR] Please install PyInstaller manually: pip install pyinstaller")
            return False


def build_exe():
    """Build the EXE file"""
    print("=" * 60)
    print("  ElderGuard - EXE Build Tool")
    print("  GUI Launcher Edition · Window Mode (No Console)")
    print("=" * 60)

    # Check PyInstaller
    if not check_pyinstaller():
        return False

    # Check spec file
    spec_file = PROJECT_ROOT / "elderguard.spec"
    if not spec_file.exists():
        print(f"[ERROR] Spec file not found: {spec_file}")
        return False

    # Build command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        str(spec_file)
    ]

    print(f"\n[*] Starting EXE build...")
    print(f"[*] Entry: launcher.py (GUI Launcher)")
    print(f"[*] Mode: Window Mode (No Console)")
    print(f"[*] This may take a few minutes, please be patient...\n")

    start_time = time.time()

    try:
        # Run PyInstaller
        subprocess.check_call(cmd, cwd=PROJECT_ROOT)

        elapsed = time.time() - start_time
        print(f"\n[OK] EXE build successful! Time: {elapsed:.1f}s")

        # Find generated exe file
        dist_dir = PROJECT_ROOT / "dist"
        exe_files = list(dist_dir.glob("*.exe"))

        if exe_files:
            exe_path = exe_files[0]
            exe_size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"\n[OK] Executable: {exe_path}")
            print(f"[OK] File size: {exe_size_mb:.2f} MB")

            # Create release directory (for teacher submission)
            release_dir = dist_dir / "Release"
            release_dir.mkdir(exist_ok=True)

            # Copy exe to release directory
            shutil.copy2(exe_path, release_dir / exe_path.name)
            print(f"[OK] Copied executable to release directory")

            # Prepare runtime files
            print("[*] Preparing runtime files...")

            # Copy config file (prefer .env from project root, otherwise .env.example)
            env_src = PROJECT_ROOT.parent / ".env"
            if not env_src.exists():
                env_src = PROJECT_ROOT.parent / ".env.example"
            env_dst = release_dir / ".env"
            if env_src.exists():
                shutil.copy2(env_src, env_dst)
                print(f"[OK] Copied config file (.env)")

            # Copy database init file (if exists)
            db_file = PROJECT_ROOT / "antifraud.db"
            if db_file.exists():
                db_dst = release_dir / "antifraud.db"
                if not db_dst.exists():
                    shutil.copy2(db_file, db_dst)
                    print(f"[OK] Copied database file")

            # Create necessary directories
            for dir_name in ["logs", "data", "models"]:
                (release_dir / dir_name).mkdir(exist_ok=True)

            # Create startup script (double-click to launch, browser opens automatically)
            create_startup_bat(release_dir)

            # Create README
            create_readme(release_dir)

            # Create source package (for teacher submission)
            src_dir = dist_dir / "Source"
            create_source_package(src_dir)

            print()
            print(f"{'='*60}")
            print(f"  [OK] Build complete!")
            print(f"{'='*60}")
            print(f"  Release package:")
            print(f"    {release_dir}/")
            print(f"      |- ElderGuard.exe        (Main program, double-click to run)")
            print(f"      |- .env                  (Config file, optional edits)")
            print(f"      |- logs/                 (Log directory)")
            print(f"      +- data/                 (Data directory)")
            print(f"  Source package:")
            print(f"    {src_dir}/")
            print()
            print(f"  Usage: Double-click the exe to launch the GUI launcher")
            print(f"  {exe_path.name}")
            print()
        else:
            print("[!] No exe file found, please check the dist directory")
            return False

        return True

    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Build process failed: {e}")
        return False
    except Exception as e:
        print(f"\n[ERROR] Unknown error: {e}")
        return False


def create_startup_bat(target_dir: Path):
    """Create startup batch script"""
    content = '''@echo off
chcp 65001 >nul
title ElderGuard

echo ========================================
echo   ElderGuard
echo   AI-Powered Multi-Modal Fraud Detection
echo ========================================
echo.

:: Check main program
if not exist "ElderGuard.exe" (
    echo [ERROR] Main program not found
    echo.
    echo Please ensure "ElderGuard.exe" is in the current directory
    pause
    exit /b 1
)

:: Check config file
if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo [INFO] Created config file from example
    )
)

:: Create necessary directories
if not exist "logs" mkdir logs >nul 2>&1
if not exist "data" mkdir data >nul 2>&1
if not exist "models" mkdir models >nul 2>&1

echo [INFO] Starting...
echo [INFO] The launcher window will appear once the system is ready
echo.
echo The launcher will automatically check:
echo   - Whether Ollama is installed
echo   - Whether the required model is downloaded
echo   - Whether the system port is available
echo.
echo For first-time use, please install Ollama and download the model first
echo.

:: Launch system (window mode, no console)
start "" "ElderGuard.exe"

echo Launcher is now open. Do not close this window...
echo To exit, close the launcher window
echo.
pause
'''
    (target_dir / "Launch System.bat").write_text(content, encoding="gbk")
    print(f"[OK] Created startup script: {target_dir / 'Launch System.bat'}")


def create_readme(target_dir: Path):
    """Create README file"""
    content = """ElderGuard - User Guide
=================================

[File Description]
  ElderGuard.exe             - Main program (double-click to run)
  .env                       - Config file (optional edits)
  logs/                      - Log files (auto-generated)
  data/                      - Data files (auto-generated)

[Usage]
  Option 1: Double-click "ElderGuard.exe" to run
  Option 2: Double-click "Launch System.bat" to run

[Launcher Features]
  1. Automatically detects whether Ollama is installed
  2. Automatically detects whether the required model is downloaded
  3. Provides Install Ollama and Download Model buttons
  4. Model configuration supports Ollama local model and Remote API modes
  5. Easily switch models and configure API Key from the launcher interface
  6. Click "Launch System" to open the Web interface
  7. Click "Open Browser" to access the system

[System Requirements]
  - Windows 10/11 64-bit
  - 8GB+ RAM recommended
  - Ollama (required for LLM-based detection)

[Notes]
  - If Ollama is not installed, click the "Install Ollama" button in the launcher
  - If the model is not downloaded, click "Download Model" (~4-8 GB)
  - Switch between Ollama/API modes in the "Model Configuration" card
  - Restart the service after saving configuration changes
  - The browser will open automatically after the system starts
"""
    (target_dir / "README.txt").write_text(content, encoding="utf-8")
    print(f"[OK] Created README file")


def create_source_package(target_dir: Path):
    """Create source code package (for teacher submission)"""
    target_dir.mkdir(parents=True, exist_ok=True)

    # Directories and files to copy to source package
    items = [
        "app", "static", "scripts", "data", "models",
        "launcher.py", "run.py", "run_server.py", "build_exe.py",
        "elderguard.spec", "requirements.txt",
    ]

    # Extra items from other directories
    extra_items = [
        (PROJECT_ROOT.parent / "docs", "docs"),
        (PROJECT_ROOT.parent / "README.md", "README.md"),
        (PROJECT_ROOT.parent / ".env.example", ".env.example"),
    ]

    for item in items:
        src = PROJECT_ROOT / item
        dst = target_dir / item
        if src.is_dir() and src.exists():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", ".git"))
            print(f"[OK] Copied source directory: {item}")
        elif src.is_file() and src.exists():
            shutil.copy2(src, dst)
            print(f"[OK] Copied source file: {item}")

    # Copy extra files (from project root)
    for src_path, item_name in extra_items:
        dst = target_dir / item_name
        if src_path.is_dir() and src_path.exists():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src_path, dst, ignore=shutil.ignore_patterns("__pycache__", ".git"))
            print(f"[OK] Copied source directory: {item_name}")
        elif src_path.is_file() and src_path.exists():
            shutil.copy2(src_path, dst)
            print(f"[OK] Copied source file: {item_name}")

    print(f"[OK] Source package created: {target_dir}")


def clean():
    """Clean build files"""
    dirs = ["build", "dist", "__pycache__"]
    files = ["elderguard.spec"]  # Keep spec file, do not delete

    for d in dirs:
        p = PROJECT_ROOT / d
        if p.exists():
            shutil.rmtree(p)
            print(f"[OK] Deleted directory: {p}")

    for f in files:
        p = PROJECT_ROOT / f
        if p.exists() and f == "elderguard.spec":
            # No longer auto-delete spec file
            pass

    for pyc in PROJECT_ROOT.rglob("__pycache__"):
        shutil.rmtree(pyc)
        print(f"[OK] Deleted cache: {pyc}")

    print("[OK] Cleanup complete")


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description='ElderGuard EXE Build Tool')
    parser.add_argument('--build', action='store_true', help='Build the EXE file')
    parser.add_argument('--clean', action='store_true', help='Clean build files')
    args = parser.parse_args()

    if args.clean:
        clean()
        return

    # Default: execute build
    success = build_exe()

    if success:
        print("\n[HINT] To rebuild from scratch, run: python build_exe.py --clean")
    else:
        print("\n[ERROR] Build failed. Check the error messages above.")
        sys.exit(1)


if __name__ == "__main__":
    main()

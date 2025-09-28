#!/usr/bin/env python3
import sys
import os
import pathlib
import platform
import shutil
import subprocess

APP_NAME = "TaskTray"

# Source files (assume install.py is in the same folder as main.py, icon.png, default.yaml, .env, .venv)
SRC_DIR = pathlib.Path(__file__).parent
MAIN_PY_SRC = SRC_DIR / "main.py"
ICON_SRC = SRC_DIR / "icon.png"
ENV_SRC = SRC_DIR / ".env"
DEFAULT_YAML = SRC_DIR / "default.yaml"
VENV_SRC = SRC_DIR / ".venv"   # source virtual environment

# Target directories
CONFIG_DIR = pathlib.Path.home() / ".task-tray"
BIN_DIR = CONFIG_DIR / "bin"
MAIN_PY_TARGET = BIN_DIR / "main.py"
ICON_TARGET = BIN_DIR / "icon.png"
ENV_TARGET = BIN_DIR / ".env"
CONFIG_YAML = CONFIG_DIR / "config.yaml"
VENV_TARGET = BIN_DIR / ".venv"

# Default Python (will be replaced by .venv if copied)
PYTHON = sys.executable
system = platform.system()


# --- Copy files ---
def copy_files():
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(MAIN_PY_SRC, MAIN_PY_TARGET)
    print(f"Copied main.py to {MAIN_PY_TARGET}")

    if ICON_SRC.exists():
        shutil.copy2(ICON_SRC, ICON_TARGET)
        print(f"Copied icon.png to {ICON_TARGET}")

    if ENV_SRC.exists():
        with open(ENV_SRC, "r") as f:
            content = f.read()
        expanded = os.path.expandvars(content)
        with open(ENV_TARGET, "w") as f:
            f.write(expanded)
        print(f"Copied and expanded .env to {ENV_TARGET}")

    if DEFAULT_YAML.exists() and not CONFIG_YAML.exists():
        shutil.copy2(DEFAULT_YAML, CONFIG_YAML)
        print(f"Copied default.yaml to {CONFIG_YAML}")
    elif CONFIG_YAML.exists():
        print(f"Config already exists at {CONFIG_YAML}, skipping copy.")

    # Copy virtual environment
    if VENV_SRC.exists():
        if VENV_TARGET.exists():
            print(f"Removing old .venv at {VENV_TARGET}")
            shutil.rmtree(VENV_TARGET)
        print(f"Copying virtual environment from {VENV_SRC} to {VENV_TARGET}...")
        shutil.copytree(VENV_SRC, VENV_TARGET, symlinks=True)
        print("Virtual environment copied.")


# --- Resolve Python executable inside .venv ---
def get_venv_python():
    if system == "Windows":
        return VENV_TARGET / "Scripts" / "pythonw.exe"
    else:
        return VENV_TARGET / "bin" / "python3"


# --- Install startup ---
def install_windows():
    try:
        import winreg
    except ImportError:
        print("pywin32 required on Windows: pip install pywin32")
        return
    key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Run",
        0,
        winreg.KEY_SET_VALUE,
    )
    run_cmd = f'"{get_venv_python()}" "{MAIN_PY_TARGET}"'
    winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, run_cmd)
    winreg.CloseKey(key)
    print(f"[Windows] Installed {APP_NAME} to start at login.")


def install_macos():
    launch_dir = pathlib.Path.home() / "Library/LaunchAgents"
    launch_dir.mkdir(parents=True, exist_ok=True)
    plist_path = launch_dir / f"com.{APP_NAME}.plist"
    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>Label</key>
    <string>com.{APP_NAME}</string>
    <key>ProgramArguments</key>
    <array>
      <string>{get_venv_python()}</string>
      <string>{MAIN_PY_TARGET}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>LSBackgroundOnly</key>
    <true/>
  </dict>
</plist>
"""
    with open(plist_path, "w") as f:
        f.write(plist_content)
    subprocess.run(["launchctl", "load", "-w", str(plist_path)])
    print(f"[macOS] Installed {APP_NAME} to start at login.")


def install_linux():
    autostart_dir = pathlib.Path.home() / ".config/autostart"
    autostart_dir.mkdir(parents=True, exist_ok=True)
    desktop_file = autostart_dir / f"{APP_NAME}.desktop"
    desktop_content = f"""[Desktop Entry]
Type=Application
Exec={get_venv_python()} {MAIN_PY_TARGET}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name={APP_NAME}
Comment=Start TaskTray Tray App
"""
    with open(desktop_file, "w") as f:
        f.write(desktop_content)
    print(f"[Linux] Installed {APP_NAME} to start at login.")


# --- Uninstall startup ---
def uninstall_windows():
    try:
        import winreg
    except ImportError:
        print("pywin32 required on Windows: pip install pywin32")
        return
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE,
        )
        winreg.DeleteValue(key, APP_NAME)
        winreg.CloseKey(key)
        print(f"[Windows] Removed {APP_NAME} from startup.")
    except FileNotFoundError:
        print(f"[Windows] {APP_NAME} not found in startup.")


def uninstall_macos():
    plist_path = pathlib.Path.home() / "Library/LaunchAgents" / f"com.{APP_NAME}.plist"
    if plist_path.exists():
        subprocess.run(["launchctl", "unload", str(plist_path)])
        plist_path.unlink()
        print(f"[macOS] Removed {APP_NAME} from startup.")
    else:
        print(f"[macOS] {APP_NAME} plist not found.")


def uninstall_linux():
    desktop_file = pathlib.Path.home() / ".config/autostart" / f"{APP_NAME}.desktop"
    if desktop_file.exists():
        desktop_file.unlink()
        print(f"[Linux] Removed {APP_NAME} from startup.")
    else:
        print(f"[Linux] {APP_NAME} autostart file not found.")


# --- Main ---
def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ["--install", "--uninstall"]:
        print("Usage: python install.py --install | --uninstall")
        print("  --install   Install the application and set it to start at login")
        print("  --uninstall Remove the application from startup")  
        print("Note: This script does not remove application files.")
        print("Source files (assume install.py is in the same folder as main.py, icon.png, default.yaml, .env, .venv)")
        print("Make sure to run this 'uv sync' first.")
        sys.exit(1)

    action = sys.argv[1]

    if action == "--install":
        copy_files()
        if system == "Windows":
            install_windows()
        elif system == "Darwin":
            install_macos()
        elif system == "Linux":
            install_linux()
        else:
            print(f"Unsupported OS: {system}")

    elif action == "--uninstall":
        if system == "Windows":
            uninstall_windows()
        elif system == "Darwin":
            uninstall_macos()
        elif system == "Linux":
            uninstall_linux()
        else:
            print(f"Unsupported OS: {system}")


if __name__ == "__main__":
    main()

import os
import sys
import subprocess
import pathlib
import yaml
import webbrowser
from datetime import datetime

from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PySide6.QtGui import QAction, QIcon

# --- PATHS ---
ICON_FILE = pathlib.Path(__file__).parent / "icon.png"

if len(sys.argv) > 1:
    CONFIG_DIR = pathlib.Path(sys.argv[1]).expanduser().resolve()
else:
    CONFIG_DIR = pathlib.Path.home() / ".task-tray"

CONFIG_FILE = CONFIG_DIR / "config.yaml"
LOG_FILE = CONFIG_DIR / "out.log"


# --- LOGGING ---
def log(msg: str):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now()}] {msg}\n")


# --- RUN COMMAND ---
def run_command(cmd: str, type_: str = None, env: dict = None):
    log(f"Running: {cmd} (type={type_}) with env={env}")
    try:
        merged_env = os.environ.copy()
        if env:
            merged_env.update(env)

        if type_ == "browser":
            webbrowser.open(cmd)
        elif type_ == "terminal":
            if sys.platform.startswith("win"):
                subprocess.Popen(["wt", "-w", "0", "nt", "cmd", "/k", cmd], env=merged_env)
            elif sys.platform == "darwin":
                subprocess.Popen(
                    ["osascript", "-e", f'tell app "Terminal" to do script "{cmd}"'],
                    env=merged_env,
                )
            else:  # Linux
                for term in [
                    "gnome-terminal",
                    "x-terminal-emulator",
                    "konsole",
                    "xfce4-terminal",
                    "lxterminal",
                ]:
                    try:
                        subprocess.Popen([term, "-e", cmd], env=merged_env)
                        break
                    except FileNotFoundError:
                        continue
        elif type_ == "open":
            if sys.platform.startswith("win"):
                os.startfile(cmd)  # native Windows open
            elif sys.platform == "darwin":
                subprocess.Popen(["open", cmd], env=merged_env)
            else:  # Linux
                subprocess.Popen(["xdg-open", cmd], env=merged_env)
        elif type_ == "silent":
            subprocess.Popen(
                cmd,
                shell=True,
                stdout=open(LOG_FILE, "a"),
                stderr=open(LOG_FILE, "a"),
                env=merged_env,
            )
        else:
            log(f"Unknown type: {type_}")
    except Exception as e:
        log(f"Error running command: {e}")


# --- MENU BUILDING ---
def build_menu(links, parent_menu: QMenu, app: QApplication):
    for link in links:
        type_ = link.get("type", "silent")
        env = link.get("env", None)

        if type_ == "separator":
            parent_menu.addSeparator()
            continue

        name = link.get("name", "Unnamed")

        if "group" in link:
            submenu = QMenu(name, parent_menu)
            build_menu(link["group"], submenu, app)
            parent_menu.addMenu(submenu)
        else:
            cmd = link.get("cmd", "")

            action = QAction(name, parent_menu)
            action.triggered.connect(lambda checked=False, c=cmd, t=type_, e=env: run_command(c, t, e))
            parent_menu.addAction(action)

    # Add Quit only at root level
    if parent_menu.parentWidget() is None:
        parent_menu.addSeparator()
        quit_action = QAction("Quit", parent_menu)
        quit_action.triggered.connect(app.quit)
        parent_menu.addAction(quit_action)


# --- CONFIG LOADING ---
def load_config():
    if not CONFIG_FILE.exists():
        log(f"No config.yaml found in {CONFIG_DIR}.")
        return {"links": []}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# --- MAIN APP ---
def main():
    app = QApplication(sys.argv)

    config = load_config()
    links = config.get("links", [])

    # Tray Icon
    if ICON_FILE.exists():
        icon = QIcon(str(ICON_FILE))
    else:
        icon = app.style().standardIcon(QSystemTrayIcon.SP_ComputerIcon)

    tray = QSystemTrayIcon()
    tray.setIcon(icon)
    tray.setToolTip("Task Tray App")

    # Build menu
    menu = QMenu()
    build_menu(links, menu, app)
    tray.setContextMenu(menu)
    tray.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

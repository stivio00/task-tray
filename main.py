import sys
import subprocess
import yaml
import pathlib
from datetime import datetime
import webbrowser

import pystray
from pystray import MenuItem as Item, Menu
from PIL import Image, ImageDraw

ICON_FILE = pathlib.Path(__file__).parent / "icon.png"

# --- CONFIG DIRECTORY ---
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
def run_command(cmd: str, type_: str = None):
    log(f"Running: {cmd} (type={type_})")
    try:
        if type_ == "browser":
            webbrowser.open(cmd)
        elif type_ == "terminal":
            if sys.platform.startswith("win"):
                subprocess.Popen(["cmd", "/k", cmd])
            elif sys.platform == "darwin":
                subprocess.Popen(
                    ["osascript", "-e", f'tell app "Terminal" to do script "{cmd}"']
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
                        subprocess.Popen([term, "-e", cmd])
                        break
                    except FileNotFoundError:
                        continue
        elif type_ == "open":
            path = pathlib.Path(cmd).expanduser().resolve()
            print(path)
            if not path.exists():
                log(f"File does not exist: {path}")
                return
            if sys.platform.startswith("win"):
                subprocess.Popen(["start", "", path], shell=True)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:  # Linux
                subprocess.Popen(["xdg-open", path])
        elif type_ == "silent":
            subprocess.Popen(
                cmd, shell=True, stdout=open(LOG_FILE, "a"), stderr=subprocess.STDOUT
            )
        else:
            log(f"Unknown type: {type_}")
    except Exception as e:
        log(f"Error running command: {e}")


# --- BUILD MENU ---
def build_menu(links, is_root=True):
    items = []

    for link in links:
        type_ = link.get("type", "silent")

        if type_ == "separator":
            items.append(Menu.SEPARATOR)
            continue

        name = link.get("name", "Unnamed")

        if "group" in link:
            submenu_items = build_menu(link["group"], is_root=False)
            items.append(Item(name, Menu(*submenu_items)))
        else:
            cmd = link.get("cmd", "")

            def make_action(c, typ):
                def action(icon, item):
                    run_command(c, typ)

                return action

            items.append(Item(name, make_action(cmd, type_)))

    # Add separator + Quit only at root menu
    if is_root:
        if items and items[-1] is not Menu.SEPARATOR:
            items.append(Menu.SEPARATOR)
        items.append(Item("Quit", lambda icon, item: icon.stop()))

    return items


def create_icon():
    if ICON_FILE.exists():
        return Image.open(ICON_FILE)
    else:
        # Fallback: simple colored circle
        size = 64
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse([0, 0, size, size], fill=(255, 200, 0, 255))
        return img


# --- LOAD CONFIG ---
def load_config():
    if not CONFIG_FILE.exists():
        log(f"No config.yaml found in {CONFIG_DIR}.")
        return {"links": []}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# --- MAIN ---
def main():
    config = load_config()
    links = config.get("links", [])

    icon = pystray.Icon("TaskTray")
    icon.icon = create_icon()
    icon.title = "Task Tray App"
    icon.menu = Menu(*build_menu(links))

    icon.run()


if __name__ == "__main__":
    main()

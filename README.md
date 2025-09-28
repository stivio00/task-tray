# TaskTray App

A **cross-platform Python tray application** to quickly launch links, commands, and applications from a system tray menu. Supports Windows, macOS, and Linux.

---

## Features

- **Tray icon menu** with customizable links and commands.  
- Supports different command types:
  - `browser` → opens a URL in the default browser.
  - `terminal` → opens a command in a terminal window.
  - `open` → opens files or applications with the default OS handler.
  - `silent` → executes background commands without opening a window (default).
  - `separator` → adds a menu separator.  
- **Nested menus** and grouping support.  
- **Cross-platform startup**:
  - Windows: adds registry entry.  
  - macOS: LaunchAgent.  
  - Linux: `.desktop` autostart.  
- Automatically loads configuration and environment variables from `~/.quick-links`.  
- Optional **icon.png** for tray icon.  

---

## Installation

1. Clone the repository or copy the files to a folder.  
2. Make sure you have Python 3.10+ installed.  
3. Run the installer:

```bash
python install.py --install
```


## Manual Run

```bash
python main.py <test-folder>
```
When test folder is specified then it will load the config.yaml from there and write the logs in this folder.


## Config example
```yaml
links:
  - name: Open Google
    cmd: https://www.google.com
    type: browser

  - name: Open GitHub
    cmd: https://github.com
    type: browser

  - name: Open macOS Settings
    cmd: "/System/Applications/System Settings.app"
    type: open

  - type: separator

  - name: AWS SSO Login
    cmd: aws sso login
    type: terminal

  - name: Connect to Postgres via SSM
    cmd: aws ssm start-session --target i-0123456789abcdef0 --document-name AWS-StartPortForwardingSession --parameters '{"portNumber":["5432"],"localPortNumber":["5432"]}'
    type: terminal

  - type: separator

  - name: Kubernetes Port Forward Pod1
    cmd: kubectl port-forward svc/service1 9000:9000
    type: terminal

  - name: Kubernetes Port Forward Pod2
    cmd: kubectl port-forward svc/service2 8080:8080
    type: terminal

  - type: separator

  - name: Ping Google
    cmd: ping -c 4 google.com
    type: terminal

  - name: List Network Interfaces
    cmd: ifconfig
    type: terminal

  - type: separator

  - name: Run background command
    cmd: echo "Hello World" > ~/Desktop/hello.txt
    type: silent

  - name: Nested Group Example
    group:
      - name: Ping Google
        cmd: ping -c 4 google.com
        type: terminal
      - name: Open Docs
        cmd: ~/Desktop/hello.txt
        type: open

```

## Screenshots

<img src="docs/screenshot_mac.png" alt="drawing" width="300"/>

helm
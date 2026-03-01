import subprocess
import os

# Map of voice keywords → actual commands/app names
APP_MAP = {
    # System apps
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "paint": "mspaint.exe",
    "camera": "microsoft.windows.camera:",
    "calendar": "outlookcal:",
    "settings": "ms-settings:",
    "task manager": "taskmgr.exe",
    "file explorer": "explorer.exe",
    "explorer": "explorer.exe",

    # Browsers
    "chrome": "chrome.exe",
    "firefox": "firefox.exe",
    "edge": "msedge.exe",
    "browser": "msedge.exe",

    # Common apps
    "word": "winword.exe",
    "excel": "excel.exe",
    "powerpoint": "powerpnt.exe",
    "vs code": "code",
    "vscode": "code",
    "spotify": "spotify.exe",
    "discord": "discord.exe",
    "whatsapp": "whatsapp.exe",
    "vlc": "vlc.exe",
}

def handle_command(text):
    """
    Check if text is a system command like 'open notepad'.
    Returns True if handled, False if should go to AI.
    """
    text = text.lower().strip()

    # --- OPEN commands ---
    if text.startswith("open "):
        app_name = text[5:].strip()
        return open_app(app_name)

    # --- CLOSE commands ---
    if text.startswith("close ") or text.startswith("band karo "):
        app_name = text.split(" ", 1)[1].strip()
        return close_app(app_name)

    return False  # Not a system command, send to AI


def open_app(app_name):
    app_name = app_name.lower().strip()

    # Check our map first
    if app_name in APP_MAP:
        cmd = APP_MAP[app_name]
        try:
            if cmd.endswith(":"):  # URI scheme (e.g. ms-settings:)
                os.startfile(cmd)
            else:
                subprocess.Popen(cmd)
            print(f"[System] Opening {app_name}...")
            return f"Opening {app_name}."
        except Exception as e:
            print(f"[System] Error: {e}")
            return f"Sorry, I couldn't open {app_name}."

    # Try running it directly as a command
    try:
        subprocess.Popen(app_name)
        print(f"[System] Opening {app_name}...")
        return f"Opening {app_name}."
    except Exception:
        return f"Sorry, I don't know how to open {app_name}."


def close_app(app_name):
    app_name = app_name.lower().strip()

    # Map friendly names to process names
    process_map = {
        "notepad": "notepad.exe",
        "calculator": "calculator.exe",
        "chrome": "chrome.exe",
        "firefox": "firefox.exe",
        "edge": "msedge.exe",
        "spotify": "spotify.exe",
        "discord": "discord.exe",
        "vlc": "vlc.exe",
        "word": "winword.exe",
        "excel": "excel.exe",
    }

    process = process_map.get(app_name, app_name + ".exe")

    try:
        subprocess.call(["taskkill", "/F", "/IM", process], 
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"[System] Closed {app_name}")
        return f"Closed {app_name}."
    except Exception:
        return f"Couldn't close {app_name}."

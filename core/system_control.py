import os
import psutil
import pyautogui
import ctypes
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL
from screen_brightness_control import set_brightness, get_brightness

def get_system_stats():
    """Returns CPU, RAM, Battery, and Brightness percentage."""
    cpu = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory().percent
    
    # Battery
    battery = psutil.sensors_battery()
    bat_percent = battery.percent if battery else "N/A"
    
    # Brightness
    try:
        brightness = get_brightness()
        if isinstance(brightness, list):
            brightness = brightness[0]
    except Exception:
        brightness = "N/A"
        
    return {
        "cpu": cpu,
        "ram": ram,
        "battery": bat_percent,
        "brightness": brightness
    }

def set_volume(level):
    """Sets system volume (0-100)."""
    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = ctypes.cast(interface, ctypes.POINTER(IAudioEndpointVolume))
        # Range is 0.0 to 1.0
        volume.SetMasterVolumeLevelScalar(level / 100, None)
        return f"Volume set to {level} percent."
    except Exception as e:
        return f"Error setting volume: {e}"

def change_brightness(level):
    """Sets screen brightness (0-100)."""
    try:
        set_brightness(level)
        return f"Brightness set to {level} percent."
    except Exception as e:
        return f"Error setting brightness: {e}"

def capture_screenshot(save_path="static/screenshots/last_screenshot.png"):
    """Takes a screenshot and saves it."""
    try:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        pyautogui.screenshot(save_path)
        return f"Screenshot saved to {save_path}."
    except Exception as e:
        return f"Error taking screenshot: {e}"

def media_control(action):
    """Controls media playback (play/pause, next, prev)."""
    actions = {
        "play": "playpause",
        "pause": "playpause",
        "next": "nexttrack",
        "prev": "prevtrack",
        "previous": "prevtrack"
    }
    key = actions.get(action.lower())
    if key:
        pyautogui.press(key)
        return f"Media {action}ed."
    return "Unknown media action."

def power_control(action):
    """System power actions."""
    if action == "lock":
        ctypes.windll.user32.LockWorkStation()
        return "System locked."
    elif action == "hibernate":
        os.system("shutdown /h")
        return "Hibernating..."
    return "Unknown power action."

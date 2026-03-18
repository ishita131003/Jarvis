import os
import psutil

# --- Hardware Dependent Imports ---
HAS_PYAUTOGUI = False
try:
    import pyautogui
    HAS_PYAUTOGUI = True
except ImportError:
    print("[SystemControl] pyautogui not installed (skipping UI automation).")

HAS_PYCAW = False
try:
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    from comtypes import CLSCTX_ALL
    import ctypes
    HAS_PYCAW = True
except ImportError:
    print("[SystemControl] pycaw/comtypes not installed (skipping volume control).")

HAS_BRIGHTNESS = False
try:
    from screen_brightness_control import set_brightness, get_brightness
    HAS_BRIGHTNESS = True
except ImportError:
    print("[SystemControl] screen-brightness-control not installed.")

def get_system_stats():
    """Returns CPU, RAM, Battery, and Brightness percentage."""
    cpu = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory().percent
    
    # Battery
    try:
        battery = psutil.sensors_battery()
        bat_percent = battery.percent if battery else "N/A"
    except Exception:
        bat_percent = "N/A"
    
    # Brightness
    brightness = "N/A"
    if HAS_BRIGHTNESS:
        try:
            curr_brightness = get_brightness()
            if isinstance(curr_brightness, list):
                brightness = curr_brightness[0]
            else:
                brightness = curr_brightness
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
    if not HAS_PYCAW:
        return "Volume control is not supported on this platform/environment."
    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = ctypes.cast(interface, ctypes.POINTER(IAudioEndpointVolume))
        volume.SetMasterVolumeLevelScalar(level / 100, None)
        return f"Volume set to {level} percent."
    except Exception as e:
        return f"Error setting volume: {e}"

def change_brightness(level):
    """Sets screen brightness (0-100)."""
    if not HAS_BRIGHTNESS:
        return "Brightness control is not supported on this platform/environment."
    try:
        set_brightness(level)
        return f"Brightness set to {level} percent."
    except Exception as e:
        return f"Error setting brightness: {e}"

def capture_screenshot(save_path="static/screenshots/last_screenshot.png"):
    """Takes a screenshot and saves it."""
    if not HAS_PYAUTOGUI:
        return "Screenshot capture is not supported in this environment."
    try:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        pyautogui.screenshot(save_path)
        return f"Screenshot saved to {save_path}."
    except Exception as e:
        return f"Error taking screenshot: {e}"

def media_control(action):
    """Controls media playback (play/pause, next, prev)."""
    if not HAS_PYAUTOGUI:
        return "Media control is not supported in this environment."
    actions = {
        "play": "playpause",
        "pause": "playpause",
        "next": "nexttrack",
        "prev": "prevtrack",
        "previous": "prevtrack"
    }
    key = actions.get(action.lower())
    if key:
        try:
            pyautogui.press(key)
            return f"Media {action}ed."
        except Exception as e:
            return f"Media control error: {e}"
    return "Unknown media action."

def power_control(action):
    """System power actions."""
    if os.name != 'nt':
        return f"Power action '{action}' is only supported on Windows."
        
    try:
        if action == "lock":
            import ctypes
            ctypes.windll.user32.LockWorkStation()
            return "System locked."
        elif action == "hibernate":
            os.system("shutdown /h")
            return "Hibernating..."
    except Exception as e:
        return f"Power control error: {e}"
    return "Unknown power action."

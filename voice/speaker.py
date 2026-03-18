import os
import tempfile
import threading
import queue
import time

# --- Hardware Dependent Imports ---
HAS_PYGAME = False
try:
    import pygame
    pygame.mixer.init()
    HAS_PYGAME = True
except Exception as e:
    print(f"[Speaker] Pygame mixer init failed/unavailable: {e}")

HAS_GTTS = False
try:
    from gtts import gTTS
    HAS_GTTS = True
except ImportError:
    print("[Speaker] gTTS not installed.")

HAS_WIN32 = False
try:
    import win32com.client
    import pythoncom
    HAS_WIN32 = True
except ImportError:
    if os.name == 'nt':
        print("[Speaker] pywin32 not found on Windows.")
    else:
        print("[Speaker] pywin32 skipped (non-Windows platform).")

# Global Speech Queue
speech_queue = queue.Queue()

# Global SAPI5 speaker for English
_sapi_speaker = None
def get_sapi_speaker():
    global _sapi_speaker
    if not HAS_WIN32:
        return None
    if _sapi_speaker is None:
        try:
            pythoncom.CoInitialize()
            _sapi_speaker = win32com.client.Dispatch("SAPI.SpVoice")
        except Exception as e:
            print(f"[Speaker] Failed to init SAPI5: {e}")
    return _sapi_speaker

def is_hindi(text):
    for char in text:
        if '\u0900' <= char <= '\u097F':
            return True
    return False

def _internal_speak_hindi(text):
    if not HAS_GTTS or not HAS_PYGAME:
        print(f"[Speaker] Skipping Hindi speech (libraries missing): {text[:50]}...")
        return
    try:
        print(f"[Speaker] Speaking Hindi (gTTS): {text[:50]}...")
        if not pygame.mixer.get_init():
            pygame.mixer.init()
            
        tts = gTTS(text=text, lang='hi', slow=False)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as f:
            tmp_path = f.name
        tts.save(tmp_path)

        pygame.mixer.music.load(tmp_path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        
        pygame.mixer.music.unload()
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        print("[Speaker] Finished speaking via gTTS.")
    except Exception as e:
        print(f"[Speaker] Hindi Error: {e}")

def _internal_speak_english(text):
    if not HAS_WIN32:
        print(f"[Speaker] Skipping English speech (SAPI5 missing): {text[:50]}...")
        return
    try:
        print(f"[Speaker] Speaking English (SAPI): {text[:50]}...")
        speaker = get_sapi_speaker()
        if speaker:
            speaker.Speak(text, 1)
            while True:
                if speaker.WaitUntilDone(100): 
                    break
            print("[Speaker] Finished speaking via SAPI.")
        else:
            print("[Speaker] SAPI speaker not initialized!")
    except Exception as e:
        print(f"[Speaker] English (SAPI5) Error: {e}")

# Global speech state
is_speaking_now = False

def speech_worker():
    """Background worker that handles one speech task at a time."""
    global is_speaking_now
    if HAS_WIN32:
        pythoncom.CoInitialize()
    print("[Speaker] Worker thread started.")
    
    while True:
        try:
            text = speech_queue.get()
            if text is None: break 
            
            is_speaking_now = True
            clean_text = text.replace('*', '').replace('#', '')
            
            if is_hindi(clean_text):
                _internal_speak_hindi(clean_text)
            else:
                _internal_speak_english(clean_text)
                
            is_speaking_now = False
        except Exception as e:
            print(f"[Speaker Worker] Error: {e}")
            is_speaking_now = False
            time.sleep(1)
        finally:
            speech_queue.task_done()

# Start the dedicated speech thread
worker_thread = threading.Thread(target=speech_worker, daemon=True)
worker_thread.start()

def speak(text):
    if not text: return
    speech_queue.put(text)

def wait_until_finished():
    speech_queue.join()
    while is_speaking_now:
        time.sleep(0.1)

def stop_speaking():
    while not speech_queue.empty():
        try:
            speech_queue.get_nowait()
            speech_queue.task_done()
        except queue.Empty:
            break
    
    if HAS_PYGAME:
        try:
            pygame.mixer.music.stop()
        except:
            pass
        
    if HAS_WIN32 and _sapi_speaker:
        try:
            _sapi_speaker.Speak("", 2)
        except:
            pass
    
    print("[Speaker] Audio stopped.")

if __name__ == "__main__":
    speak("System check. Speaker module loaded.")
    time.sleep(2)
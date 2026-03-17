import os
import tempfile
import threading
import queue
import time
import win32com.client
import pythoncom
from gtts import gTTS
import pygame

# Initialize pygame mixer for Hindi/Audio playback
try:
    pygame.mixer.init()
except Exception as e:
    print(f"[Speaker] Pygame mixer init failed: {e}")

# ... existing code ...

# Global Speech Queue
speech_queue = queue.Queue()

# Global SAPI5 speaker for English
_sapi_speaker = None
def get_sapi_speaker():
    global _sapi_speaker
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
    try:
        print(f"[Speaker] Speaking English (SAPI): {text[:50]}...")
        speaker = get_sapi_speaker()
        if speaker:
            # 0 = Default (Synchronous)
            speaker.Speak(text)
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
    # Initialize COM for this thread
    pythoncom.CoInitialize()
    print("[Speaker] Worker thread started with COM init.")
    while True:
        try:
            text = speech_queue.get()
            if text is None: break # Shutdown signal
            
            is_speaking_now = True
            # Remove asterisks and markdown before speaking
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
    """Adds a message to the speech queue. Non-blocking."""
    if not text: return
    speech_queue.put(text)

def wait_until_finished():
    """Blocks until the speech queue is empty and the worker is idle."""
    speech_queue.join()
    while is_speaking_now:
        time.sleep(0.1)

def stop_speaking():
    """Immediately stops any current speech and clears the queue."""
    # 1. Clear the queue
    while not speech_queue.empty():
        try:
            speech_queue.get_nowait()
            speech_queue.task_done()
        except queue.Empty:
            break
    
    # 2. Stop Hindi (pygame)
    try:
        pygame.mixer.music.stop()
    except:
        pass
        
    # 3. Stop English (SAPI5 Purge)
    try:
        if _sapi_speaker:
            # 1 = SVSFPurgeBeforeSpeak
            _sapi_speaker.Speak("", 1)
    except:
        pass
    
    print("[Speaker] Audio stopped by user.")

if __name__ == "__main__":
    speak("Hello, I am Jarvis. SAPI5 is now active.")
    speak("नमस्ते, मैं जार्विस हूँ।")
    time.sleep(2)
    stop_speaking()
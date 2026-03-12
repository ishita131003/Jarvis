import os
import tempfile
import threading
import queue
import time
import win32com.client
from gtts import gTTS
import pygame

# Global Speech Queue
speech_queue = queue.Queue()

# Global SAPI5 speaker for English
_sapi_speaker = None
try:
    _sapi_speaker = win32com.client.Dispatch("SAPI.SpVoice")
except Exception as e:
    print(f"[Speaker] Failed to init SAPI5: {e}")

def is_hindi(text):
    for char in text:
        if '\u0900' <= char <= '\u097F':
            return True
    return False

def _internal_speak_hindi(text):
    try:
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
    except Exception as e:
        print(f"[Speaker] Hindi Error: {e}")

def _internal_speak_english(text):
    try:
        if _sapi_speaker:
            _sapi_speaker.Speak(text)
    except Exception as e:
        print(f"[Speaker] English (SAPI5) Error: {e}")

def speech_worker():
    """Background worker that handles one speech task at a time."""
    print("[Speaker] Worker thread started.")
    while True:
        try:
            text = speech_queue.get()
            if text is None: break # Shutdown signal
            
            # Remove asterisks and markdown before speaking
            clean_text = text.replace('*', '').replace('#', '')
            
            if is_hindi(clean_text):
                _internal_speak_hindi(clean_text)
            else:
                _internal_speak_english(clean_text)
                
            speech_queue.task_done()
        except Exception as e:
            print(f"[Speaker Worker] Error: {e}")
            time.sleep(1)

# Start the dedicated speech thread
worker_thread = threading.Thread(target=speech_worker, daemon=True)
worker_thread.start()

def speak(text):
    """Adds a message to the speech queue. Non-blocking."""
    if not text: return
    speech_queue.put(text)

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
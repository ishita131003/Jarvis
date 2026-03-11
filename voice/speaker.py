import os
import tempfile
import threading
import queue
import time
import win32com.client
from gtts import gTTS
import pygame

# Initialize pygame mixer once for Hindi/MP3 playback
pygame.mixer.init()

# Thread-safe queue for speech tasks
speech_queue = queue.Queue()

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
        # Use native Windows SAPI5 - much more stable than pyttsx3
        speaker = win32com.client.Dispatch("SAPI.SpVoice")
        speaker.Speak(text)
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
    # If text is too long (AI responses), split by sentences for better flow? 
    # For now, just queue the whole thing.
    speech_queue.put(text)

if __name__ == "__main__":
    speak("Hello, I am Jarvis. SAPI5 is now active.")
    speak("नमस्ते, मैं जार्विस हूँ।")
    time.sleep(5)
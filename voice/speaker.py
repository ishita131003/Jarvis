import pyttsx3
import os
import tempfile
from gtts import gTTS
import pygame

def is_hindi(text):
    # Check if text contains Devanagari script characters (Hindi)
    for char in text:
        if '\u0900' <= char <= '\u097F':
            return True
    return False

def speak_hindi(text):
    # Use gTTS for Hindi and play via pygame
    tts = gTTS(text=text, lang='hi', slow=False)
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as f:
        tmp_path = f.name
    tts.save(tmp_path)

    pygame.mixer.init()
    pygame.mixer.music.load(tmp_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
    pygame.mixer.quit()
    os.remove(tmp_path)

def speak_english(text):
    # Use pyttsx3 for English
    engine = pyttsx3.init()
    engine.setProperty('rate', 175)
    engine.setProperty('volume', 1.0)
    engine.say(text)
    engine.runAndWait()
    engine.stop()

def speak(text):
    if is_hindi(text):
        speak_hindi(text)
    else:
        speak_english(text)


# Temporary testing block
if __name__ == "__main__":
    speak("Hello, I am Jarvis.")
    speak("नमस्ते, मैं जार्विस हूँ।")
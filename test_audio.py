import sys
import os
import time

# Add current directory to path
sys.path.append(os.getcwd())

from voice.speaker import speak, wait_until_finished

def test_audio():
    print("--- JARVIS AUDIO ENGINE TEST ---")
    
    print("1. Testing English Speech (SAPI)...")
    speak("Hello Sir, this is a test of my English speech engine. Can you hear me?")
    wait_until_finished()
    print("   Done.")
    
    time.sleep(2)
    
    print("2. Testing Hindi Speech (gTTS/Pygame)...")
    # Using Devanagari to trigger Hindi engine
    speak("नमस्ते सर, यह मेरे हिंदी भाषण इंजन का परीक्षण है। क्या आप मुझे सुन सकते हैं?")
    wait_until_finished()
    print("   Done.")
    
    print("\n--- TEST COMPLETED ---")

if __name__ == "__main__":
    test_audio()

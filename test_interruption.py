import sys
import os
import time
import threading

# Add current directory to path
sys.path.append(os.getcwd())

from voice.speaker import speak, stop_speaking, is_speaking_now

def test_interruption():
    print("--- JARVIS AUDIO INTERRUPTION TEST ---")
    
    # Test English Interruption
    print("\n1. Testing English Interruption (SAPI5)...")
    long_text = "This is a very long sentence that should be interrupted by the stop_speaking function. " * 3
    speak(long_text)
    
    time.sleep(1) # Let it start speaking
    if is_speaking_now:
        print("   Speaking detected. Stopping now...")
        stop_speaking()
        time.sleep(0.5)
        if not is_speaking_now:
            print("   SUCCESS: English speech stopped immediately.")
        else:
            print("   FAILURE: English speech is still active.")
    else:
        print("   FAILURE: English speech never started.")

    # Test Hindi Interruption
    print("\n2. Testing Hindi Interruption (Pygame)...")
    long_hindi = "यह एक बहुत लंबा वाक्य है जिसे उपयोगकर्ता द्वारा म्यूट बटन दबाने पर तुरंत रुक जाना चाहिए। " * 3
    speak(long_hindi)
    
    time.sleep(2) # gTTS takes time to generate and load
    if is_speaking_now:
        print("   Hindi speaking detected. Stopping now...")
        stop_speaking()
        time.sleep(0.5)
        if not is_speaking_now:
            print("   SUCCESS: Hindi speech stopped immediately.")
        else:
            print("   FAILURE: Hindi speech is still active.")
    else:
        print("   FAILURE: Hindi speech never started. (Note: gTTS might be slow)")

    print("\n--- TEST COMPLETED ---")

if __name__ == "__main__":
    test_interruption()

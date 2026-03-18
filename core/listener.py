# --- Hardware Dependent Imports ---
HAS_SR = False
try:
    import speech_recognition as sr
    HAS_SR = True
except ImportError:
    print("[Listener] speech_recognition not installed (skipping voice input).")

if HAS_SR:
    recognizer = sr.Recognizer()
    recognizer.pause_threshold = 1.5
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = False
else:
    recognizer = None

def listen(timeout=None, phrase_time_limit=None):
    if not HAS_SR:
        return None
        
    try:
        with sr.Microphone() as source:
            print(f"[Listener] Ready! (timeout={timeout}, phrase_limit={phrase_time_limit})")
            try:
                audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
                print("[Listener] Got audio, processing...")
            except sr.WaitTimeoutError:
                return None

        text = recognizer.recognize_google(audio)
        print("You said:", text)
        return text.lower()
    except Exception as e:
        # Most likely PyAudio missing or microphone access error
        print(f"[Listener] Speech recognition error: {e}")
        return None

if __name__ == "__main__":
    if HAS_SR:
        listen()
    else:
        print("Listener module loaded in no-op mode (no SR library).")
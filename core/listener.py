import speech_recognition as sr

recognizer = sr.Recognizer()
recognizer.pause_threshold = 1.5      # stop after 1.5s of silence (instant but won't cut off mid-sentence)
recognizer.energy_threshold = 300      # fixed sensitivity (lower = more sensitive)
recognizer.dynamic_energy_threshold = False  # don't auto-adjust (was causing it to ignore voice)

def listen(timeout=None, phrase_time_limit=None):
    with sr.Microphone() as source:
        print(f"[Listener] Ready! (timeout={timeout}, phrase_limit={phrase_time_limit})")
        try:
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            print("[Listener] Got audio, processing...")
        except sr.WaitTimeoutError:
            return None

    try:
        text = recognizer.recognize_google(audio)
        print("You said:", text)
        return text.lower()
    except sr.UnknownValueError:
        print("Could not understand audio")
        return None
    except sr.RequestError:
        print("Speech service error")
        return None


# Temporary testing block
if __name__ == "__main__":
    while True:
        listen()
import speech_recognition as sr

recognizer = sr.Recognizer()
recognizer.pause_threshold = 1.5      # stop after 1.5s of silence (instant but won't cut off mid-sentence)
recognizer.energy_threshold = 300      # fixed sensitivity (lower = more sensitive)
recognizer.dynamic_energy_threshold = False  # don't auto-adjust (was causing it to ignore voice)

def listen():
    with sr.Microphone() as source:
        print("[Listener] Ready! Speak now... (stops after 1.5s of silence)")
        audio = recognizer.listen(source, timeout=None, phrase_time_limit=None)
        print("[Listener] Got audio, processing...")

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